// Minimal dependency-free test harness (no Catch2/gtest fetch required).
#ifndef VOICECMD_TEST_UTIL_H
#define VOICECMD_TEST_UTIL_H

#include <atomic>
#include <cstdio>
#include <functional>
#include <optional>
#include <string>
#include <variant>
#include <vector>

#include "voicecmd/confirm.h"
#include "voicecmd/engine.h"

namespace vctest {

inline int& failures() {
    static int f = 0;
    return f;
}
inline int& checks() {
    static int c = 0;
    return c;
}

#define CHECK(cond)                                                          \
    do {                                                                     \
        ++::vctest::checks();                                                \
        if (!(cond)) {                                                       \
            ++::vctest::failures();                                          \
            std::printf("  FAIL %s:%d  CHECK(%s)\n", __FILE__, __LINE__,     \
                        #cond);                                              \
        }                                                                    \
    } while (0)

#define RUN(fn)                                                              \
    do {                                                                     \
        std::printf("[test] %s\n", #fn);                                     \
        fn();                                                                \
    } while (0)

// Deterministic confirmation-UI double.
class FakeUI final : public voicecmd::IConfirmationUI {
public:
    void beginConfirm(const std::string& phrase,
                      std::function<void(bool)> resolve) override {
        last_phrase = phrase;
        resolver_ = resolve;
        active.store(true);
        begin_count.fetch_add(1);
        if (auto_answer.has_value()) resolve(*auto_answer);
    }
    void endConfirm() override {
        active.store(false);
        end_count.fetch_add(1);
    }

    // Simulate a button click (from the test / UI thread).
    void click(bool yes) {
        if (resolver_) resolver_(yes);
    }

    std::optional<bool> auto_answer;  // set to auto-resolve on beginConfirm
    std::string last_phrase;
    std::atomic<bool> active{false};
    std::atomic<int> begin_count{0};
    std::atomic<int> end_count{0};

private:
    std::function<void(bool)> resolver_;
};

// Drain repeatedly so chained worker messages (e.g. Recognition -> Confirm
// -> RecognitionEvent) settle before assertions.
inline void flush(voicecmd::Engine& e) {
    for (int i = 0; i < 4; ++i) e.sync().get();
}

template <class T>
int count(const std::vector<voicecmd::Event>& v) {
    int c = 0;
    for (const auto& e : v)
        if (std::holds_alternative<T>(e)) ++c;
    return c;
}

template <class T>
const T* first(const std::vector<voicecmd::Event>& v) {
    for (const auto& e : v)
        if (const T* p = std::get_if<T>(&e)) return p;
    return nullptr;
}

}  // namespace vctest

#endif  // VOICECMD_TEST_UTIL_H
