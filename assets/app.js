(() => {
  const feedback = new Map();
  document.querySelectorAll("[data-copy]").forEach((button) => {
    button.addEventListener("click", async () => {
      const text = button.getAttribute("data-copy") || "";
      try {
        await navigator.clipboard.writeText(text);
        button.textContent = "已复制";
        clearTimeout(feedback.get(button));
        feedback.set(button, setTimeout(() => {
          button.textContent = button.getAttribute("data-label") || "复制命令";
        }, 1600));
      } catch (_error) {
        const target = button.nextElementSibling;
        if (target && target.classList.contains("copy-feedback")) {
          target.textContent = text;
        }
      }
    });
  });

  const modeButtons = [...document.querySelectorAll("[data-mode-button]")];
  const modeSections = [...document.querySelectorAll("[data-mode]")];
  if (modeButtons.length || modeSections.length) {
    const setMode = (mode) => {
      modeButtons.forEach((button) => {
        button.setAttribute("aria-pressed", String(button.getAttribute("data-mode-button") === mode));
      });
      modeSections.forEach((section) => {
        const modes = (section.getAttribute("data-mode") || "").split(/\s+/);
        section.hidden = mode !== "all" && !modes.includes(mode);
      });
      localStorage.setItem("rw-dashboard-mode", mode);
    };
    modeButtons.forEach((button) => button.addEventListener("click", () => setMode(button.getAttribute("data-mode-button") || "all")));
    setMode(localStorage.getItem("rw-dashboard-mode") || "all");
  }
})();
