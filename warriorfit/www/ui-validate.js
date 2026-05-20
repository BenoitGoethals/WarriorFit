/**
 * WarriorFit — UI validation & status-bar helper
 *
 * 1. Status-bar semantic colouring
 *    Watches every .shiny-text-output inside a .wf-status-bar (or any element
 *    with data-wf-status).  When Shiny updates the text, a semantic modifier
 *    class is added so the CSS can colour it without server round-trips.
 *
 * 2. Time-format client-side hint
 *    Inputs whose placeholder contains "mm:ss" get a live format hint;
 *    a red outline appears if the value is non-empty and doesn't match.
 *
 * 3. Required-field highlight
 *    Action buttons whose id ends in _add_btn or _update_btn briefly flash
 *    any empty required sibling inputs in the same card when clicked.
 */

(function () {
  "use strict";

  /* ---- 1. Status-bar semantic colouring ---- */
  const STATUS_OK   = /^(saved|updated|deleted|success|ok|added|sent|done)/i;
  const STATUS_ERR  = /^(error|fail|invalid|required|already|not found|wrong|expired|denied|could not)/i;
  const STATUS_WARN = /^(warn|caution|pending|retry|partial)/i;

  function classifyStatus(text) {
    const t = (text || "").trim();
    if (!t) return null;
    if (STATUS_ERR.test(t))  return "wf-status-err";
    if (STATUS_OK.test(t))   return "wf-status-ok";
    if (STATUS_WARN.test(t)) return "wf-status-warn";
    return "wf-status-info";
  }

  function updateStatusBar(el) {
    const text = el.textContent || "";
    const cls  = classifyStatus(text);
    el.classList.remove("wf-status-ok", "wf-status-err", "wf-status-warn", "wf-status-info");
    if (cls) el.classList.add(cls);
  }

  // Observe all current and future status outputs
  const statusObserver = new MutationObserver(function (mutations) {
    mutations.forEach(function (m) {
      // Direct text updates on a known status element
      if (m.target.hasAttribute("data-wf-status") ||
          m.target.closest(".wf-status-bar")) {
        updateStatusBar(m.target);
        return;
      }
      // Shiny re-renders: scan added nodes for status outputs
      m.addedNodes.forEach(function (node) {
        if (node.nodeType !== 1) return;
        node.querySelectorAll
          ? node.querySelectorAll(".shiny-text-output").forEach(function (el) {
              if (el.closest(".wf-status-bar") || el.dataset.wfStatus !== undefined) {
                updateStatusBar(el);
              }
            })
          : null;
      });
    });
  });

  statusObserver.observe(document.body, {
    childList: true,
    subtree:   true,
    characterData: true,
  });

  // Initial scan after Shiny has mounted
  document.addEventListener("shiny:sessioninitialized", function () {
    document.querySelectorAll(".wf-status-bar .shiny-text-output").forEach(updateStatusBar);
    document.querySelectorAll("[data-wf-status] .shiny-text-output").forEach(updateStatusBar);
  });


  /* ---- 2. Time-format (mm:ss) live validation ---- */
  const TIME_RE = /^\d{1,2}:[0-5]\d$/;

  function hookTimeInputs() {
    document.querySelectorAll('input[type="text"]').forEach(function (inp) {
      if (inp.dataset.wfTimeHooked) return;
      const ph = inp.getAttribute("placeholder") || "";
      if (!ph.includes(":")) return;        // only time-like placeholders
      inp.dataset.wfTimeHooked = "1";

      function validate() {
        const v = inp.value.trim();
        if (!v) {
          inp.classList.remove("wf-input-invalid", "wf-input-valid");
          return;
        }
        const ok = TIME_RE.test(v);
        inp.classList.toggle("wf-input-invalid", !ok);
        inp.classList.toggle("wf-input-valid",    ok);
      }
      inp.addEventListener("input",  validate);
      inp.addEventListener("change", validate);
      inp.addEventListener("blur",   validate);
    });
  }

  // Hook existing + dynamically rendered inputs
  document.addEventListener("shiny:sessioninitialized", hookTimeInputs);
  document.addEventListener("shiny:value",              hookTimeInputs);


  /* ---- 3. Required-field flash on action buttons ---- */
  document.addEventListener("click", function (e) {
    const btn = e.target.closest(".btn");
    if (!btn) return;
    const id = btn.id || "";
    if (!id.endsWith("_add_btn") && !id.endsWith("_update_btn")) return;

    const card = btn.closest(".card, .bslib-card");
    if (!card) return;

    card.querySelectorAll('input[type="text"], input[type="number"], select').forEach(function (inp) {
      if (inp.hasAttribute("required") && !inp.value.trim()) {
        inp.classList.add("wf-input-required-flash");
        setTimeout(function () { inp.classList.remove("wf-input-required-flash"); }, 1800);
      }
    });
  }, true);

})();
