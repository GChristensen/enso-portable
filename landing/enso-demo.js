// Enso overlay mockup: types a command, shows autocompletion and a suggestion, then loops.
(function () {
  "use strict";

  // ---- tuning ----
  var CONFIG = {
    tickMs: 280,             // duration of one animation tick (typing speed)
    command: "open notepad", // full command; the untyped remainder is shown as ghost autocompletion
    typeUntil: 9,            // characters typed before the animation holds ("open note")
    autocompleteAt: 6,       // character count where typing pauses a tick, then ghost completion appears
    suggestionAt: 7,         // character count where the suggestion row below appears
    revealTicks: 2,          // ticks the top bar fades in before typing starts
    holdEndTicks: 14,        // ticks to hold the finished state
    holdIdleTicks: 5         // ticks of blank screen before the loop restarts
  };
  // Fade durations of the top bar are in style.css (--demo-fade).

  var topBar = document.getElementById("demo-top");
  var commandBox = document.getElementById("demo-command");
  var typedEl = document.getElementById("typed-text");
  var ghostEl = document.getElementById("suggest-text");
  var suggestionBox = document.getElementById("demo-suggestion");
  if (!topBar || !commandBox || !typedEl || !ghostEl || !suggestionBox) return;

  // Phases: idle -> reveal -> type <-> autocomplete -> hold -> idle
  var phase = "idle";
  var typed = 0;          // number of characters typed so far
  var wait = 0;           // ticks to skip before advancing
  var showGhost = false;  // whether ghost autocompletion is visible

  function render() {
    typedEl.textContent = CONFIG.command.slice(0, typed);
    ghostEl.textContent = (typed >= CONFIG.autocompleteAt && showGhost) ? CONFIG.command.slice(typed) : "";
    commandBox.style.visibility = typed > 0 ? "visible" : "hidden";
    suggestionBox.style.visibility = typed >= CONFIG.suggestionAt ? "visible" : "hidden";
  }

  function tick() {
    if (wait > 0) { wait--; return; }

    switch (phase) {
      case "idle":
        phase = "reveal";
        wait = CONFIG.revealTicks;
        topBar.style.opacity = 1;
        break;

      case "reveal":
        phase = "type";
        break;

      case "type":
        if (typed < CONFIG.typeUntil) {
          typed++;
          if (typed === CONFIG.autocompleteAt) {
            phase = "autocomplete";
            showGhost = false;
          } else if (typed === CONFIG.typeUntil) {
            phase = "hold";
            wait = CONFIG.holdEndTicks;
          }
          render();
        }
        break;

      case "autocomplete":
        phase = "type";
        showGhost = true;
        render();
        break;

      default: // "hold" finished: reset
        phase = "idle";
        typed = 0;
        wait = CONFIG.holdIdleTicks;
        showGhost = false;
        topBar.style.opacity = 0;
        render();
    }
  }

  setInterval(tick, CONFIG.tickMs);
  render();
})();
