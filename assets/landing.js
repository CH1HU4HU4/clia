(function () {
  "use strict";

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var live = document.getElementById("copy-live");

  function announce(message) {
    if (!live) {
      return;
    }
    live.textContent = "";
    window.setTimeout(function () {
      live.textContent = message;
    }, 30);
  }

  function fallbackCopy(text) {
    var area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.top = "-1000px";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();

    var ok = false;
    try {
      ok = document.execCommand("copy");
    } catch (error) {
      ok = false;
    }

    document.body.removeChild(area);
    return ok;
  }

  function copyText(text, done) {
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(
        function () {
          done(true);
        },
        function () {
          done(fallbackCopy(text));
        }
      );
      return;
    }

    done(fallbackCopy(text));
  }

  Array.prototype.forEach.call(document.querySelectorAll(".ask"), function (row) {
    var hint = row.querySelector(".ask-copy");
    var text = row.getAttribute("data-copy") || "";
    var timer = 0;

    row.addEventListener("click", function () {
      copyText(text, function (ok) {
        if (!ok) {
          announce("Copy blocked. Select the command and press Command-C.");
          return;
        }

        announce("Copied " + text);
        row.classList.add("is-copied");
        if (hint) {
          hint.textContent = "Copied";
        }

        window.clearTimeout(timer);
        timer = window.setTimeout(function () {
          row.classList.remove("is-copied");
          if (hint) {
            hint.textContent = "Copy";
          }
        }, 1800);
      });
    });
  });

  var installButton = document.getElementById("copy-install");
  var installPrompt = document.getElementById("install-prompt");
  var installStatus = document.getElementById("copy-status");
  var installDefault = installStatus ? installStatus.textContent : "";
  var resetTimer = 0;

  if (installButton && installPrompt) {
    installButton.addEventListener("click", function () {
      copyText(installPrompt.textContent.trim(), function (ok) {
        if (!ok) {
          if (installStatus) {
            installStatus.textContent = "Copy blocked. Select the prompt and press Command-C.";
          }
          return;
        }

        installButton.textContent = "Copied";
        if (installStatus) {
          installStatus.textContent = "Copied to clipboard.";
        }
        announce("Install prompt copied.");

        window.clearTimeout(resetTimer);
        resetTimer = window.setTimeout(function () {
          installButton.textContent = "Copy install prompt";
          if (installStatus) {
            installStatus.textContent = installDefault;
          }
        }, 2400);
      });
    });
  }

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

  // Section entrances, staggered within each block. Content stays visible without script.
  var groups = document.querySelectorAll(
    ".why-lead, .why-points, .asks-head, .asks, .footer-inner"
  );
  var revealTargets = [];

  Array.prototype.forEach.call(groups, function (group) {
    Array.prototype.forEach.call(group.children, function (child, index) {
      child.classList.add("reveal");
      child.style.setProperty("--d", Math.min(index * 70, 280) + "ms");
      revealTargets.push(child);
    });
  });

  if (revealTargets.length && !reduceMotion && "IntersectionObserver" in window) {
    document.documentElement.classList.add("motion");

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("in");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px" }
    );

    revealTargets.forEach(function (target) {
      observer.observe(target);
    });
  }
})();
