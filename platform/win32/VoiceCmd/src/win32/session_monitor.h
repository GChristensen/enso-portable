// voicecmd — workstation lock/unlock notifications (Win32).
//
// Deliberately outside the core (which is COM-free, Python-free and portable)
// and outside the SAPI backend (this is not a recognition concern): the host
// binding owns one of these and decides what locking means. For voicecmd that
// is a HARD stop -- see the note on the callback below.
#ifndef VOICECMD_SESSION_MONITOR_H
#define VOICECMD_SESSION_MONITOR_H

#include <atomic>
#include <functional>
#include <thread>

namespace voicecmd {

class SessionMonitor {
public:
    // Invoked with true on lock, false on unlock, from the monitor's own
    // thread. It must not block: post work to another queue and return.
    //
    // Callers should react by stopping the engine outright, not soft-pausing
    // it. A soft pause keeps the recognizer alive -- the microphone stays open
    // and the "resume listening" phrase stays in the grammar, both live to
    // whoever is standing at the lock screen.
    using Callback = std::function<void(bool locked)>;

    // Starts the monitor thread. Throws std::runtime_error if the message-only
    // window or the WTS registration cannot be created.
    explicit SessionMonitor(Callback cb);

    // Stops the monitor thread and joins it. Once this returns, the callback
    // is guaranteed not to fire again.
    ~SessionMonitor();

    SessionMonitor(const SessionMonitor&) = delete;
    SessionMonitor& operator=(const SessionMonitor&) = delete;

private:
    void run();

    Callback cb_;
    std::thread thread_;
    std::atomic<unsigned long> tid_{0};  // monitor thread id, for WM_QUIT
    std::atomic<bool> ready_{false};     // window created (or creation failed)
    std::atomic<bool> failed_{false};
};

}  // namespace voicecmd

#endif  // VOICECMD_SESSION_MONITOR_H
