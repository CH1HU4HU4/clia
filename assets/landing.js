(function () {
  "use strict";

  var prompts = {
    build:
      "Clone https://github.com/CH1HU4HU4/clia into your skills folder as clia. Read SKILL.md, then build a CLI for this repo: map 90%+ of the product surface in CLI.md, scaffold from the matching template, implement reads before writes. No TTY prompts, stable --json, real exit codes. Run scripts/conformance and report every gap.",
    extend:
      "Clone https://github.com/CH1HU4HU4/clia into your skills folder as clia. Read SKILL.md, then audit this repo's existing CLI against CLI-GUIDELINES.md and extend it without breaking what works. Fill surface gaps, remove TTY-only flows, add --json and --dry-run, map every error to a real exit code. Run scripts/conformance and report what remains.",
    audit:
      "Clone https://github.com/CH1HU4HU4/clia into your skills folder as clia. Read SKILL.md, then audit this repo's CLI against CLI-GUIDELINES.md without changing code. Report surface coverage, non-TTY behavior, JSON stability, exit codes, help quality, write safety, and startup latency. Rank P0/P1/P2 with file references and the smallest fix for each."
  };

  var dialog = document.getElementById("prompt-dialog");
  var openers = [
    document.getElementById("open-prompt"),
    document.getElementById("open-prompt-top")
  ].filter(Boolean);
  var closeButton = document.getElementById("close-dialog");
  var tabs = Array.prototype.slice.call(document.querySelectorAll('[role="tab"]'));
  var panel = document.getElementById("prompt-panel");
  var promptText = document.getElementById("prompt-text");
  var copyButton = document.getElementById("copy");
  var status = document.getElementById("copy-status");
  var defaultStatus = status ? status.textContent : "";
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var resetTimer = 0;
  var lastTrigger = null;

  function selectTab(next) {
    var key = { "tab-build": "build", "tab-extend": "extend", "tab-audit": "audit" }[next.id] || "build";

    tabs.forEach(function (tab) {
      var active = tab === next;
      tab.setAttribute("aria-selected", active ? "true" : "false");
      tab.tabIndex = active ? 0 : -1;
    });

    panel.setAttribute("aria-labelledby", next.id);
    promptText.textContent = prompts[key];
    panel.scrollTop = 0;

    if (status) {
      status.textContent = defaultStatus;
    }

    if (!reduceMotion && panel.animate) {
      panel.animate(
        [{ opacity: 0.35 }, { opacity: 1 }],
        { duration: 180, easing: "ease-out" }
      );
    }
  }

  tabs.forEach(function (tab) {
    tab.addEventListener("click", function () {
      selectTab(tab);
    });

    tab.addEventListener("keydown", function (event) {
      var index = tabs.indexOf(tab);
      var next = null;

      if (event.key === "ArrowRight" || event.key === "ArrowDown") {
        next = tabs[(index + 1) % tabs.length];
      } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
        next = tabs[(index - 1 + tabs.length) % tabs.length];
      } else if (event.key === "Home") {
        next = tabs[0];
      } else if (event.key === "End") {
        next = tabs[tabs.length - 1];
      }

      if (next) {
        event.preventDefault();
        next.focus();
        selectTab(next);
      }
    });
  });

  function openDialog(trigger) {
    lastTrigger = trigger || null;

    if (typeof dialog.showModal === "function") {
      if (!dialog.open) {
        dialog.showModal();
      }
    } else {
      dialog.setAttribute("open", "");
    }

    window.setTimeout(function () {
      copyButton.focus();
    }, 30);
  }

  function closeDialog() {
    if (typeof dialog.close === "function" && dialog.open) {
      dialog.close();
    } else {
      dialog.removeAttribute("open");
    }
  }

  openers.forEach(function (opener) {
    opener.addEventListener("click", function () {
      openDialog(opener);
    });
  });

  closeButton.addEventListener("click", closeDialog);

  dialog.addEventListener("click", function (event) {
    if (event.target === dialog) {
      closeDialog();
    }
  });

  dialog.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      event.preventDefault();
      closeDialog();
    }
  });

  dialog.addEventListener("close", function () {
    if (lastTrigger && typeof lastTrigger.focus === "function") {
      lastTrigger.focus();
    }
    if (status) {
      status.textContent = defaultStatus;
    }
    copyButton.textContent = "Copy prompt";
  });

  function markCopied(ok) {
    if (!ok) {
      if (status) {
        status.textContent = "Copy blocked. The prompt is selected - press Cmd-C.";
      }
      copyButton.textContent = "Copy prompt";
      return;
    }

    if (status) {
      status.textContent = "Copied to clipboard.";
    }
    copyButton.textContent = "Copied";

    window.clearTimeout(resetTimer);
    resetTimer = window.setTimeout(function () {
      copyButton.textContent = "Copy prompt";
      if (status) {
        status.textContent = defaultStatus;
      }
    }, 2600);
  }

  function fallbackCopy() {
    var selection = window.getSelection();
    var range = document.createRange();
    range.selectNodeContents(promptText);
    selection.removeAllRanges();
    selection.addRange(range);

    var ok = false;
    try {
      ok = document.execCommand("copy");
    } catch (error) {
      ok = false;
    }

    if (ok) {
      selection.removeAllRanges();
    } else {
      panel.focus();
    }
    return ok;
  }

  copyButton.addEventListener("click", function () {
    var text = promptText.textContent;

    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(
        function () {
          markCopied(true);
        },
        function () {
          markCopied(fallbackCopy());
        }
      );
      return;
    }

    markCopied(fallbackCopy());
  });

  // A small pointer parallax keeps the harness tiles alive without moving the content.
  var stage = document.querySelector(".stage");
  if (stage && !reduceMotion && window.matchMedia("(pointer: fine)").matches) {
    var frame = 0;
    var pointerX = 0;
    var pointerY = 0;

    var apply = function () {
      frame = 0;
      stage.style.setProperty("--mx", pointerX.toFixed(3));
      stage.style.setProperty("--my", pointerY.toFixed(3));
    };

    window.addEventListener(
      "pointermove",
      function (event) {
        pointerX = (event.clientX / window.innerWidth) * 2 - 1;
        pointerY = (event.clientY / window.innerHeight) * 2 - 1;
        if (!frame) {
          frame = window.requestAnimationFrame(apply);
        }
      },
      { passive: true }
    );
  }
})();
