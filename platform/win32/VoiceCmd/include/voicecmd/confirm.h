// voicecmd — confirmation UI seam. The Win32 implementation (M4) lives on the
// library's UI thread; unit tests supply a deterministic double. The engine
// owns the timeout itself (deterministic), so implementations need not time out.
#ifndef VOICECMD_CONFIRM_H
#define VOICECMD_CONFIRM_H

#include <functional>
#include <string>

namespace voicecmd {

class IConfirmationUI {
public:
    virtual ~IConfirmationUI() = default;

    // Show a topmost dialog asking to confirm `phrase`. Non-blocking. When the
    // user clicks a button, call `resolve(true)` for yes / `resolve(false)` for
    // no. Voice yes/no is handled by the engine, not here. `resolve` is safe to
    // call from any thread (it posts to the engine's queue).
    virtual void beginConfirm(const std::string& phrase,
                              std::function<void(bool)> resolve) = 0;

    // Hide any active dialog (answered, timed out, or cancelled).
    virtual void endConfirm() = 0;
};

}  // namespace voicecmd

#endif  // VOICECMD_CONFIRM_H
