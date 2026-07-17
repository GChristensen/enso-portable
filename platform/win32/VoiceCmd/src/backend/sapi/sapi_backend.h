// voicecmd — in-process SAPI 5 recognizer backend.
//
// COM/SAPI/Win32 are fully confined to the .cpp (pimpl); this header stays
// clean so the core and bindings never pull in windows.h. Every method here is
// invoked ONLY on the engine's worker thread (the single-owner invariant);
// recognitions are delivered from a dedicated listener thread via BackendSink.
#ifndef VOICECMD_SAPI_BACKEND_H
#define VOICECMD_SAPI_BACKEND_H

#include <memory>

#include "voicecmd/backend.h"

namespace voicecmd {

class SapiBackend final : public IRecognizerBackend {
public:
    SapiBackend();
    ~SapiBackend() override;

    void create(const Config& cfg, BackendSink* sink) override;
    void updateGrammar(const std::vector<Verb>& verbs) override;
    void setActiveRuleset(Ruleset r) override;
    void start() override;
    void stop() override;
    void dispose() override;

private:
    struct Impl;
    std::unique_ptr<Impl> p_;
};

}  // namespace voicecmd

#endif  // VOICECMD_SAPI_BACKEND_H
