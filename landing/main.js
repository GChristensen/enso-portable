// General page logic.
(function () {
  "use strict";

  // ---- iframe-aware link handling ----
  // When embedded in an iframe, links open in a new tab; standalone, they
  // navigate normally in the same tab.
  function isEmbedded() {
    try {
      return window.self !== window.top;
    } catch (e) {
      // cross-origin parent access throws, which itself implies embedding
      return true;
    }
  }

  if (isEmbedded()) {
    var links = document.querySelectorAll("a[href]");
    for (var i = 0; i < links.length; i++) {
      links[i].target = "_blank";
      links[i].rel = "noopener noreferrer";
    }
  }
})();
