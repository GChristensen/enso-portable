// SAPI link + runtime smoke check: proves the SAPI GUIDs resolve at link time
// and that the recognizer/context/grammar/listener lifecycle stands up and tears
// down cleanly. Recognition itself needs a mic + installed SR engine; this only
// exercises construction, so it degrades gracefully on machines without either.
#include <chrono>
#include <cstdio>
#include <memory>
#include <thread>
#include <variant>

#include "sapi_backend.h"
#include "voicecmd/engine.h"

using namespace voicecmd;

int main() {
    Config cfg;
    cfg.keyword = "computer";
    cfg.keyword_required = true;
    Verb open;
    open.name = "open";
    Noun notepad;
    notepad.name = "notepad";
    open.nouns.push_back(notepad);
    Noun chrome;
    chrome.name = "google chrome";
    open.nouns.push_back(chrome);
    cfg.verbs = {open};

    Engine eng(cfg, std::make_unique<SapiBackend>(), nullptr);
    try {
        eng.start().get();
        std::printf("start OK; state=%s\n", to_string(eng.state()));
    } catch (const std::exception& e) {
        std::printf("start failed (ok if no SR engine/mic present): %s\n",
                    e.what());
    }

    std::this_thread::sleep_for(std::chrono::milliseconds(400));
    for (const auto& ev : eng.drain()) {
        if (auto* p = std::get_if<LogEvent>(&ev))
            std::printf("[log %s] %s\n", to_string(p->level), p->message.c_str());
        else if (auto* p = std::get_if<StateChangeEvent>(&ev))
            std::printf("[state] %s -> %s\n", to_string(p->old_state),
                        to_string(p->new_state));
    }

    eng.stop().get();
    eng.close();
    std::printf("closed cleanly; final state=%s\n", to_string(eng.state()));
    return 0;
}
