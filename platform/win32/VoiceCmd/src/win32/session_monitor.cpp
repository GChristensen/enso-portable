#include "session_monitor.h"

#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#include <wtsapi32.h>

#include <condition_variable>
#include <mutex>
#include <stdexcept>

namespace voicecmd {
namespace {

constexpr wchar_t kWindowClass[] = L"VoicecmdSessionMonitor";

std::mutex g_ready_mx;
std::condition_variable g_ready_cv;

LRESULT CALLBACK wndProc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp) {
    if (msg == WM_WTSSESSION_CHANGE) {
        // The window carries the callback itself (not the owning monitor), so
        // this proc needs no access to SessionMonitor's internals. The pointee
        // outlives the window: run() tears the window down before returning,
        // and the destructor joins that thread before cb_ dies.
        auto* cb = reinterpret_cast<SessionMonitor::Callback*>(
            GetWindowLongPtrW(hwnd, GWLP_USERDATA));
        if (cb != nullptr && (wp == WTS_SESSION_LOCK || wp == WTS_SESSION_UNLOCK)) {
            // Invoked directly on the monitor thread; by contract the callback
            // only posts work, so the message pump stays responsive.
            (*cb)(wp == WTS_SESSION_LOCK);
        }
        return 0;
    }
    return DefWindowProcW(hwnd, msg, wp, lp);
}

}  // namespace

SessionMonitor::SessionMonitor(Callback cb) : cb_(std::move(cb)) {
    if (!cb_) throw std::runtime_error("voicecmd: session monitor needs a callback");

    thread_ = std::thread([this] { run(); });

    std::unique_lock<std::mutex> lk(g_ready_mx);
    g_ready_cv.wait(lk, [this] { return ready_.load(); });
    if (failed_.load()) {
        lk.unlock();
        if (thread_.joinable()) thread_.join();
        throw std::runtime_error("voicecmd: could not start the session monitor");
    }
}

SessionMonitor::~SessionMonitor() {
    const unsigned long tid = tid_.load();
    if (tid != 0) {
        // Ends GetMessage() on the monitor thread; the window and the WTS
        // registration are torn down on that thread inside run().
        PostThreadMessageW(tid, WM_QUIT, 0, 0);
    }
    if (thread_.joinable()) thread_.join();
}

void SessionMonitor::run() {
    tid_.store(GetCurrentThreadId());

    HINSTANCE inst = GetModuleHandleW(nullptr);
    WNDCLASSEXW wc{};
    wc.cbSize = sizeof(wc);
    wc.lpfnWndProc = wndProc;
    wc.hInstance = inst;
    wc.lpszClassName = kWindowClass;
    // Re-registration across recognizer restarts is expected; only a genuine
    // failure (not "already registered") should abort.
    if (RegisterClassExW(&wc) == 0 && GetLastError() != ERROR_CLASS_ALREADY_EXISTS) {
        std::lock_guard<std::mutex> lk(g_ready_mx);
        failed_.store(true);
        ready_.store(true);
        g_ready_cv.notify_one();
        return;
    }

    // HWND_MESSAGE: an invisible, taskbar-less window that exists purely to
    // receive WM_WTSSESSION_CHANGE.
    HWND hwnd = CreateWindowExW(0, kWindowClass, L"", 0, 0, 0, 0, 0,
                                HWND_MESSAGE, nullptr, inst, nullptr);
    bool registered = false;
    if (hwnd != nullptr) {
        SetWindowLongPtrW(hwnd, GWLP_USERDATA, reinterpret_cast<LONG_PTR>(&cb_));
        registered = WTSRegisterSessionNotification(hwnd, NOTIFY_FOR_THIS_SESSION) != FALSE;
        if (!registered) {
            DestroyWindow(hwnd);
            hwnd = nullptr;
        }
    }

    {
        std::lock_guard<std::mutex> lk(g_ready_mx);
        failed_.store(hwnd == nullptr);
        ready_.store(true);
        g_ready_cv.notify_one();
    }
    if (hwnd == nullptr) return;

    MSG msg;
    while (GetMessageW(&msg, nullptr, 0, 0) > 0) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }

    WTSUnRegisterSessionNotification(hwnd);
    DestroyWindow(hwnd);
}

}  // namespace voicecmd
