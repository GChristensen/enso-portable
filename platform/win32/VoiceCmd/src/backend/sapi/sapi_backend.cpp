// voicecmd — SAPI 5 backend implementation.
//
// Grammar strategy (see plan §4): ONE dynamic grammar holding one top-level rule
// per verb, plus control ("stop/resume listening"), yes/no, and a REQUIRED
// garbage/wildcard rule. "Ruleset swap" = toggling which top-level rules are
// active on the single engine (no second engine, no device contention). Semantic
// identity is read from the matched rule id and a noun property — never from
// word positions — so multi-word verbs/nouns and the keyword shift are handled.
#include "sapi_backend.h"

#ifdef _WIN32

#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
// initguid.h BEFORE sapi.h materializes the SAPI CLSID/IID definitions in this
// translation unit, so we need not link sapi.lib.
#include <initguid.h>
#include <sapi.h>
#include <sperror.h>
#include <wrl/client.h>

#include <atomic>
#include <cstdio>
#include <cstring>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

using Microsoft::WRL::ComPtr;

namespace voicecmd {
namespace {

// Rule id scheme. Verb rules occupy [kVerbBase, kVerbBase + nVerbs).
constexpr ULONG kIdCtlStop = 1;
constexpr ULONG kIdCtlResume = 2;
constexpr ULONG kIdYes = 3;
constexpr ULONG kIdNo = 4;
constexpr ULONG kIdGarbage = 5;
constexpr ULONG kVerbBase = 1000;
constexpr ULONGLONG kGrammarId = 1;

// Garbage rule is a low-weight fallback so real commands win when spoken.
constexpr float kGarbageWeight = 0.30f;

// Dictation likewise sits below the fixed rules: a free-text tail must never
// out-compete an enumerated noun on the same verb.
constexpr float kDictationWeight = 0.50f;

std::wstring toWide(const std::string& s) {
    if (s.empty()) return {};
    int n = ::MultiByteToWideChar(CP_UTF8, 0, s.data(), (int)s.size(), nullptr, 0);
    std::wstring w(n, L'\0');
    ::MultiByteToWideChar(CP_UTF8, 0, s.data(), (int)s.size(), w.data(), n);
    return w;
}

std::string toUtf8(const wchar_t* w) {
    if (!w || !*w) return {};
    int n = ::WideCharToMultiByte(CP_UTF8, 0, w, -1, nullptr, 0, nullptr, nullptr);
    if (n <= 0) return {};
    std::string s(n - 1, '\0');  // drop trailing NUL
    ::WideCharToMultiByte(CP_UTF8, 0, w, -1, s.data(), n, nullptr, nullptr);
    return s;
}

void check(HRESULT hr, const char* what) {
    if (FAILED(hr)) {
        // Carry the HRESULT: without it a failure here is undiagnosable from a
        // log ("SAPI: GetRule(verb)" says nothing about *why*).
        char buf[192];
        std::snprintf(buf, sizeof(buf), "SAPI: %s failed (hr=0x%08lX)", what,
                      (unsigned long)hr);
        throw std::runtime_error(buf);
    }
}

// Native (tri-level + engine float) -> normalized 0..1. SREngineConfidence
// carries the real per-utterance signal (it separates correct commands from
// force-matched garbage); the coarse tri-level only nudges it. When the engine
// is uncertain (LOW) -- the common case with an untrained profile -- we rely on
// the raw engine confidence so its discrimination is preserved rather than
// crushed into a narrow band. Backend-owned mapping (plan §5).
double mapConfidence(signed char rel, float eng) {
    double e = eng;
    if (e < 0.0) e = 0.0;
    if (e > 1.0) e = 1.0;
    if (rel >= SP_HIGH_CONFIDENCE) return 0.75 + 0.25 * e;  // confident
    if (rel == SP_NORMAL_CONFIDENCE) return e > 0.55 ? e : 0.55;
    return e;  // LOW: raw engine confidence is the only real signal
}

// The default object token for a SAPI category (e.g. the user's current
// recognition profile or SR engine), fetched WITHOUT sphelper.h. Returns null
// if the category has no default (e.g. Windows Speech never set up).
ComPtr<ISpObjectToken> defaultToken(const wchar_t* category) {
    ComPtr<ISpObjectTokenCategory> cat;
    if (FAILED(::CoCreateInstance(CLSID_SpObjectTokenCategory, nullptr, CLSCTX_ALL,
                                  IID_PPV_ARGS(&cat))))
        return nullptr;
    if (FAILED(cat->SetId(category, FALSE))) return nullptr;
    LPWSTR tokenId = nullptr;
    if (FAILED(cat->GetDefaultTokenId(&tokenId)) || !tokenId) return nullptr;
    ComPtr<ISpObjectToken> token;
    HRESULT hr = ::CoCreateInstance(CLSID_SpObjectToken, nullptr, CLSCTX_ALL,
                                    IID_PPV_ARGS(&token));
    if (SUCCEEDED(hr)) hr = token->SetId(nullptr, tokenId, FALSE);
    ::CoTaskMemFree(tokenId);
    return SUCCEEDED(hr) ? token : nullptr;
}

// Depth-first search for a phrase property node by name; null if absent.
const SPPHRASEPROPERTY* findPropNode(const SPPHRASEPROPERTY* p,
                                     const wchar_t* name) {
    for (; p; p = p->pNextSibling) {
        if (p->pszName && wcscmp(p->pszName, name) == 0) return p;
        if (const SPPHRASEPROPERTY* c = findPropNode(p->pFirstChild, name))
            return c;
    }
    return nullptr;
}

// Depth-first search for a phrase property by name; returns its ulId or -1.
int findProp(const SPPHRASEPROPERTY* p, const wchar_t* name) {
    const SPPHRASEPROPERTY* n = findPropNode(p, name);
    return n ? (int)n->ulId : -1;
}

}  // namespace

struct SapiBackend::Impl {
    Config cfg;
    BackendSink* sink = nullptr;

    ComPtr<ISpRecognizer> recognizer;
    ComPtr<ISpRecoContext> context;
    ComPtr<ISpRecoGrammar> grammar;

    std::thread listener;
    HANDLE stop_event = nullptr;   // signals the listener to exit
    std::atomic<bool> com_init{false};
    int verb_count = 0;
    bool has_garbage = false;
    bool dictation_loaded = false;

    void log(LogLevel lvl, std::string msg) {
        if (sink) sink->onLog(lvl, std::move(msg));
    }

    // ---- grammar construction (worker thread) ----

    // Adds an optional (or required) keyword prefix, returning the state to
    // continue building the verb/control words from.
    SPSTATEHANDLE addKeywordPrefix(SPSTATEHANDLE hInit) {
        SPSTATEHANDLE hMid = nullptr;
        check(grammar->CreateNewState(hInit, &hMid), "CreateNewState");
        std::wstring kw = toWide(cfg.keyword);
        if (!kw.empty()) {
            check(grammar->AddWordTransition(hInit, hMid, kw.c_str(), L" ",
                                             SPWT_LEXICAL, 1.0f, nullptr),
                  "keyword transition");
            if (!cfg.keyword_required) {
                // epsilon path so the keyword may be omitted
                check(grammar->AddWordTransition(hInit, hMid, nullptr, nullptr,
                                                 SPWT_LEXICAL, 1.0f, nullptr),
                      "keyword epsilon");
            }
        } else {
            check(grammar->AddWordTransition(hInit, hMid, nullptr, nullptr,
                                             SPWT_LEXICAL, 1.0f, nullptr),
                  "no-keyword epsilon");
        }
        return hMid;
    }

    // The dictation topic is loaded lazily and only once: it is needed solely
    // by SPRULETRANS_DICTATION, and loading it costs memory + startup time.
    void ensureDictation() {
        if (dictation_loaded) return;
        check(grammar->LoadDictation(nullptr, SPLO_STATIC), "LoadDictation");
        dictation_loaded = true;
    }

    void buildVerbRule(int index, const Verb& v) {
        SPSTATEHANDLE hInit = nullptr;
        // The rule NAME is derived from the index, never from the verb. SAPI
        // binds name<->id for the life of the grammar and ClearRule empties a
        // rule body WITHOUT unbinding it, so naming the rule "google" at id
        // 1001 makes every later grammar update that puts a different verb at
        // index 1 fail with SPERR_RULE_NAME_ID_CONFLICT. Since nothing reads
        // the name back (handleResult dispatches on Rule.ulId), an id-derived
        // name costs nothing and makes updates order-independent.
        const std::wstring rule_name =
            L"__verb" + std::to_wstring(index) + L"__";
        check(grammar->GetRule(rule_name.c_str(), kVerbBase + index,
                               SPRAF_TopLevel, TRUE, &hInit),
              "GetRule(verb)");
        SPSTATEHANDLE hMid = addKeywordPrefix(hInit);

        SPPROPERTYINFO vprop{};
        vprop.pszName = L"V";
        vprop.ulId = (ULONG)index;

        std::wstring verb = toWide(v.name);
        if (v.nouns.empty() && !v.free_text) {
            check(grammar->AddWordTransition(hMid, nullptr, verb.c_str(), L" ",
                                             SPWT_LEXICAL, 1.0f, &vprop),
                  "verb-only transition");
            return;
        }
        SPSTATEHANDLE hAfterVerb = nullptr;
        check(grammar->CreateNewState(hInit, &hAfterVerb), "CreateNewState(verb)");
        check(grammar->AddWordTransition(hMid, hAfterVerb, verb.c_str(), L" ",
                                         SPWT_LEXICAL, 1.0f, &vprop),
              "verb transition");
        for (size_t i = 0; i < v.nouns.size(); ++i) {
            SPPROPERTYINFO nprop{};
            nprop.pszName = L"N";
            nprop.ulId = (ULONG)i;
            std::wstring noun = toWide(v.nouns[i].name);
            check(grammar->AddWordTransition(hAfterVerb, nullptr, noun.c_str(),
                                             L" ", SPWT_LEXICAL, 1.0f, &nprop),
                  "noun transition");
        }
        if (v.free_text) {
            ensureDictation();
            // Tagged so handleResult can recover the element range and ask for
            // just the dictated words back, rather than the whole utterance.
            SPPROPERTYINFO dprop{};
            dprop.pszName = L"D";
            dprop.ulId = 0;
            check(grammar->AddRuleTransition(hAfterVerb, nullptr,
                                             SPRULETRANS_DICTATION,
                                             kDictationWeight, &dprop),
                  "dictation transition");
            // Epsilon to final: the dictated tail is OPTIONAL, so the bare verb
            // still matches (e.g. "computer calculate" acting on a selection).
            check(grammar->AddWordTransition(hAfterVerb, nullptr, nullptr,
                                             nullptr, SPWT_LEXICAL, 1.0f,
                                             nullptr),
                  "free-text epsilon");
        }
    }

    void buildControlRule(ULONG id, const wchar_t* name, const std::string& phrase,
                          int propId) {
        SPSTATEHANDLE hInit = nullptr;
        check(grammar->GetRule(name, id, SPRAF_TopLevel, TRUE, &hInit),
              "GetRule(control)");
        SPSTATEHANDLE hMid = addKeywordPrefix(hInit);
        SPPROPERTYINFO prop{};
        prop.pszName = L"C";
        prop.ulId = (ULONG)propId;
        check(grammar->AddWordTransition(hMid, nullptr, toWide(phrase).c_str(),
                                         L" ", SPWT_LEXICAL, 1.0f, &prop),
              "control transition");
    }

    void buildYesNoRule(ULONG id, const wchar_t* name, const wchar_t* word,
                        int propId) {
        SPSTATEHANDLE hInit = nullptr;
        check(grammar->GetRule(name, id, SPRAF_TopLevel, TRUE, &hInit),
              "GetRule(yesno)");
        SPPROPERTYINFO prop{};
        prop.pszName = L"Y";
        prop.ulId = (ULONG)propId;
        // Yes/no need no keyword prefix — spoken bare inside the dialog.
        check(grammar->AddWordTransition(hInit, nullptr, word, L" ",
                                         SPWT_LEXICAL, 1.0f, &prop),
              "yesno transition");
    }

    void buildGarbageRule() {
        SPSTATEHANDLE hInit = nullptr;
        check(grammar->GetRule(L"__garbage__", kIdGarbage, SPRAF_TopLevel, TRUE,
                               &hInit),
              "GetRule(garbage)");
        // Wildcard absorbs out-of-grammar speech so the engine stops
        // force-matching it onto a real command.
        check(grammar->AddRuleTransition(hInit, nullptr, SPRULETRANS_WILDCARD,
                                         kGarbageWeight, nullptr),
              "garbage wildcard");
    }

    void buildAllRules() {
        verb_count = (int)cfg.verbs.size();
        for (int i = 0; i < verb_count; ++i) {
            if (cfg.verbs[i].disabled) continue;
            buildVerbRule(i, cfg.verbs[i]);
        }
        buildControlRule(kIdCtlStop, L"__ctl_stop__", "stop listening", 1);
        buildControlRule(kIdCtlResume, L"__ctl_resume__", "resume listening", 2);
        buildYesNoRule(kIdYes, L"__yes__", L"yes", 1);
        buildYesNoRule(kIdNo, L"__no__", L"no", 2);
        if (cfg.use_garbage_rule) {
            buildGarbageRule();
            has_garbage = true;
        }
        check(grammar->Commit(0), "Commit");
    }

    void setRule(ULONG id, bool active) {
        grammar->SetRuleIdState(id, active ? SPRS_ACTIVE : SPRS_INACTIVE);
    }

    void applyRuleset(Ruleset r) {
        const bool commands = (r == Ruleset::Commands);
        const bool resume_only = (r == Ruleset::ResumeOnly);
        const bool yesno = (r == Ruleset::YesNo);
        for (int i = 0; i < verb_count; ++i) {
            if (cfg.verbs[i].disabled) continue;
            setRule(kVerbBase + i, commands);
        }
        setRule(kIdCtlStop, commands);        // can pause only while listening
        setRule(kIdCtlResume, resume_only);   // unpause only while paused
        setRule(kIdYes, yesno);
        setRule(kIdNo, yesno);
        if (has_garbage) setRule(kIdGarbage, true);  // absorb OOV speech (opt-in)
    }

    // ---- recognition listener thread ----

    void listenLoop() {
        // This thread touches SAPI objects -> its own COM init (MTA to match).
        HRESULT hrCom = ::CoInitializeEx(nullptr, COINIT_MULTITHREADED);
        bool listener_com = SUCCEEDED(hrCom);
        HANDLE notify = context->GetNotifyEventHandle();
        HANDLE waits[2] = {stop_event, notify};
        for (;;) {
            DWORD w = ::WaitForMultipleObjects(2, waits, FALSE, INFINITE);
            if (w == WAIT_OBJECT_0) break;  // stop_event
            drainEvents();
        }
        if (listener_com) ::CoUninitialize();
    }

    void drainEvents() {
        SPEVENT ev;
        ULONG fetched = 0;
        std::memset(&ev, 0, sizeof(ev));
        while (context && SUCCEEDED(context->GetEvents(1, &ev, &fetched)) &&
               fetched == 1) {
            switch (ev.eEventId) {
                case SPEI_RECOGNITION:
                    handleResult(reinterpret_cast<ISpRecoResult*>(ev.lParam),
                                 /*false_reco=*/false);
                    break;
                case SPEI_FALSE_RECOGNITION:
                    handleResult(reinterpret_cast<ISpRecoResult*>(ev.lParam),
                                 /*false_reco=*/true);
                    break;
                case SPEI_END_SR_STREAM:
                    if (sink) sink->onBackendEnded();
                    break;
                default:
                    break;
            }
            // Release/free the event payload.
            if (ev.elParamType == SPET_LPARAM_IS_OBJECT ||
                ev.elParamType == SPET_LPARAM_IS_TOKEN) {
                if (ev.lParam) reinterpret_cast<IUnknown*>(ev.lParam)->Release();
            } else if (ev.elParamType == SPET_LPARAM_IS_POINTER ||
                       ev.elParamType == SPET_LPARAM_IS_STRING) {
                if (ev.lParam) ::CoTaskMemFree(reinterpret_cast<void*>(ev.lParam));
            }
            std::memset(&ev, 0, sizeof(ev));
            fetched = 0;
        }
    }

    void handleResult(ISpRecoResult* result, bool false_reco) {
        if (!result || !sink) return;
        SPPHRASE* phrase = nullptr;
        HRESULT hr = result->GetPhrase(&phrase);

        RawRecognition r;
        if (FAILED(hr) || !phrase) {
            r.kind = RawKind::Garbage;
            r.confidence = 0.1;
            sink->onRecognition(std::move(r));
            return;
        }

        const ULONG ruleId = phrase->Rule.ulId;
        // Report the real mapped confidence for BOTH recognition and false-
        // recognition events (no artificial penalty) so the confidence bands and
        // the rejection telemetry see the engine's true, discriminating signal.
        r.confidence = mapConfidence(phrase->Rule.Confidence,
                                     phrase->Rule.SREngineConfidence);

        if (ruleId >= kVerbBase && (int)(ruleId - kVerbBase) < verb_count) {
            const int vi = (int)(ruleId - kVerbBase);
            r.kind = RawKind::Command;
            r.verb_index = vi;
            r.noun_index = findProp(phrase->pProperties, L"N");
            // A dictated tail is transcribed speech, so it is the ONE part of
            // the utterance that cannot come from the configured strings. Ask
            // for exactly the elements the dictation transition consumed.
            const SPPHRASEPROPERTY* dict =
                findPropNode(phrase->pProperties, L"D");
            if (dict != nullptr && dict->ulCountOfElements > 0) {
                wchar_t* dtext = nullptr;
                if (SUCCEEDED(result->GetText(dict->ulFirstElement,
                                              dict->ulCountOfElements, TRUE,
                                              &dtext, nullptr))) {
                    r.free_text = toUtf8(dtext);
                    if (dtext) ::CoTaskMemFree(dtext);
                }
            }
            // Resolved utterance from CONFIGURED strings (original casing, no
            // keyword) so the host resolves it directly -- except the dictated
            // tail, which is passed through verbatim and unnormalized.
            r.text = cfg.verbs[vi].name;
            if (r.noun_index >= 0 &&
                r.noun_index < (int)cfg.verbs[vi].nouns.size()) {
                r.text += " ";
                r.text += cfg.verbs[vi].nouns[r.noun_index].name;
            } else if (!r.free_text.empty()) {
                r.text += " ";
                r.text += r.free_text;
            }
        } else if (ruleId == kIdCtlStop) {
            r.kind = RawKind::Control;
            r.control = ControlPhrase::StopListening;
            r.text = "stop listening";
        } else if (ruleId == kIdCtlResume) {
            r.kind = RawKind::Control;
            r.control = ControlPhrase::ResumeListening;
            r.text = "resume listening";
        } else if (ruleId == kIdYes) {
            r.kind = RawKind::YesNo;
            r.answer = YesNoAnswer::Yes;
            r.text = "yes";
        } else if (ruleId == kIdNo) {
            r.kind = RawKind::YesNo;
            r.answer = YesNoAnswer::No;
            r.text = "no";
        } else {
            r.kind = RawKind::Garbage;
            wchar_t* text = nullptr;
            if (SUCCEEDED(result->GetText(SP_GETWHOLEPHRASE, SP_GETWHOLEPHRASE,
                                          TRUE, &text, nullptr))) {
                r.text = toUtf8(text);
                if (text) ::CoTaskMemFree(text);
            }
        }
        // Diagnostics: expose the RAW SAPI confidence signals so correct vs
        // out-of-grammar utterances can be compared and a threshold chosen.
        {
            char buf[320];
            std::snprintf(buf, sizeof(buf),
                          "reco %-5s rule=%lu tri=%+d eng=%.3f norm=%.3f text='%s'",
                          false_reco ? "FALSE" : "OK", (unsigned long)ruleId,
                          (int)phrase->Rule.Confidence,
                          (double)phrase->Rule.SREngineConfidence, r.confidence,
                          r.text.c_str());
            sink->onLog(LogLevel::Info, buf);
        }

        ::CoTaskMemFree(phrase);
        sink->onRecognition(std::move(r));
    }
};

// ---- IRecognizerBackend (worker thread) -----------------------------------

SapiBackend::SapiBackend() : p_(std::make_unique<Impl>()) {}
SapiBackend::~SapiBackend() { dispose(); }

void SapiBackend::create(const Config& cfg, BackendSink* sink) {
    p_->cfg = cfg;
    p_->sink = sink;

    HRESULT hrCom = ::CoInitializeEx(nullptr, COINIT_MULTITHREADED);
    p_->com_init.store(SUCCEEDED(hrCom));

    const CLSID clsid = cfg.shared_recognizer ? CLSID_SpSharedRecognizer
                                              : CLSID_SpInprocRecognizer;
    check(::CoCreateInstance(clsid, nullptr, CLSCTX_ALL,
                             IID_PPV_ARGS(&p_->recognizer)),
          "create recognizer");

    if (!cfg.shared_recognizer) {
        // In-proc: load the default SR engine + the user's TRAINED recognition
        // profile so this private recognizer is as well-calibrated as the shared
        // one -- good confidence discrimination WITHOUT launching the Windows
        // Speech Recognition app.
        if (auto engine = defaultToken(SPCAT_RECOGNIZERS)) {
            p_->recognizer->SetRecognizer(engine.Get());
        }
        if (auto profile = defaultToken(SPCAT_RECOPROFILES)) {
            HRESULT hrp = p_->recognizer->SetRecoProfile(profile.Get());
            p_->log(SUCCEEDED(hrp) ? LogLevel::Info : LogLevel::Warning,
                    SUCCEEDED(hrp) ? "in-proc: loaded trained reco profile"
                                   : "in-proc: SetRecoProfile failed");
        } else {
            p_->log(LogLevel::Warning,
                    "in-proc: no trained reco profile found -- confidence may be "
                    "poor; set up Windows Speech Recognition (train your profile)");
        }
        // Bind the default audio input. (Shared uses the mic from Speech settings.)
        ComPtr<IUnknown> audio;
        if (SUCCEEDED(::CoCreateInstance(CLSID_SpMMAudioIn, nullptr, CLSCTX_ALL,
                                         IID_PPV_ARGS(&audio)))) {
            p_->recognizer->SetInput(audio.Get(), TRUE);
        } else {
            p_->recognizer->SetInput(nullptr, TRUE);
        }
    }

    check(p_->recognizer->CreateRecoContext(&p_->context), "create context");
    check(p_->context->SetNotifyWin32Event(), "SetNotifyWin32Event");
    const ULONGLONG interest = SPFEI(SPEI_RECOGNITION) |
                               SPFEI(SPEI_FALSE_RECOGNITION) |
                               SPFEI(SPEI_END_SR_STREAM);
    check(p_->context->SetInterest(interest, interest), "SetInterest");

    check(p_->context->CreateGrammar(kGrammarId, &p_->grammar), "CreateGrammar");
    p_->buildAllRules();

    // Idle until start(); rules stay inactive until a ruleset is selected.
    p_->recognizer->SetRecoState(SPRST_INACTIVE);

    p_->stop_event = ::CreateEventW(nullptr, TRUE, FALSE, nullptr);
    p_->listener = std::thread([impl = p_.get()] { impl->listenLoop(); });
    p_->log(LogLevel::Info, cfg.shared_recognizer
                                ? "SAPI backend created (SHARED recognizer)"
                                : "SAPI backend created (in-proc recognizer)");
}

void SapiBackend::updateGrammar(const std::vector<Verb>& verbs) {
    if (!p_->grammar) return;
    // Clear existing verb rules, rebuild from the new list, recommit.
    for (int i = 0; i < p_->verb_count; ++i) {
        p_->grammar->SetRuleIdState(kVerbBase + i, SPRS_INACTIVE);
        // Empty the rule body so stale words don't linger.
        SPSTATEHANDLE h = nullptr;
        if (SUCCEEDED(p_->grammar->GetRule(nullptr, kVerbBase + i, 0, FALSE, &h))) {
            p_->grammar->ClearRule(h);
        }
    }
    p_->cfg.verbs = verbs;
    p_->verb_count = (int)verbs.size();
    for (int i = 0; i < p_->verb_count; ++i) {
        if (verbs[i].disabled) continue;
        p_->buildVerbRule(i, verbs[i]);
    }
    p_->grammar->Commit(0);
    p_->applyRuleset(Ruleset::Commands);
}

void SapiBackend::setActiveRuleset(Ruleset r) {
    if (p_->grammar) p_->applyRuleset(r);
}

void SapiBackend::start() {
    if (p_->recognizer) p_->recognizer->SetRecoState(SPRST_ACTIVE);
}

void SapiBackend::stop() {
    if (p_->recognizer) p_->recognizer->SetRecoState(SPRST_INACTIVE_WITH_PURGE);
}

void SapiBackend::dispose() {
    if (!p_) return;
    if (p_->stop_event) ::SetEvent(p_->stop_event);
    if (p_->listener.joinable()) p_->listener.join();
    if (p_->stop_event) {
        ::CloseHandle(p_->stop_event);
        p_->stop_event = nullptr;
    }
    p_->grammar.Reset();
    p_->context.Reset();
    p_->recognizer.Reset();
    if (p_->com_init.exchange(false)) ::CoUninitialize();
    p_->verb_count = 0;
    // The grammar is gone, so the dictation topic must be reloaded on re-create.
    p_->dictation_loaded = false;
}

}  // namespace voicecmd

#else  // !_WIN32 — the SAPI backend is Windows-only.
#endif
