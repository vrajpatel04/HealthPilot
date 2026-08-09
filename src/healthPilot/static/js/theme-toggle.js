(function () {
  const THEME_KEY = "hp_theme_preference";

  function getPreferredTheme() {
    const saved = localStorage.getItem(THEME_KEY);
    if (saved === "dark" || saved === "light") {
      return saved;
    }
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }

  function applyTheme(theme) {
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
    const toggleBtns = document.querySelectorAll(".theme-toggle-btn");
    toggleBtns.forEach(function (btn) {
      btn.setAttribute("aria-label", theme === "dark" ? "Switch to light mode" : "Switch to dark mode");
      const iconSun = btn.querySelector(".icon-sun");
      const iconMoon = btn.querySelector(".icon-moon");
      if (iconSun && iconMoon) {
        if (theme === "dark") {
          iconSun.classList.remove("hidden");
          iconMoon.classList.add("hidden");
        } else {
          iconSun.classList.add("hidden");
          iconMoon.classList.remove("hidden");
        }
      }
    });
  }

  function initTheme() {
    const current = getPreferredTheme();
    applyTheme(current);
  }

  function toggleTheme() {
    const isDark = document.documentElement.classList.contains("dark");
    const nextTheme = isDark ? "light" : "dark";
    localStorage.setItem(THEME_KEY, nextTheme);
    applyTheme(nextTheme);
  }

  function initMobileMenu() {
    const menuBtn = document.getElementById("mobile-menu-btn");
    const menuContainer = document.getElementById("mobile-menu");
    if (!menuBtn || !menuContainer) return;

    menuBtn.addEventListener("click", function () {
      const isExpanded = menuBtn.getAttribute("aria-expanded") === "true";
      menuBtn.setAttribute("aria-expanded", String(!isExpanded));
      if (isExpanded) {
        menuContainer.classList.add("hidden");
      } else {
        menuContainer.classList.remove("hidden");
        menuContainer.classList.add("animate-slide-down");
      }
    });
  }

  // Early theme initialization before DOM render completes
  initTheme();

  document.addEventListener("DOMContentLoaded", function () {
    const toggleBtns = document.querySelectorAll(".theme-toggle-btn");
    toggleBtns.forEach(function (btn) {
      btn.addEventListener("click", toggleTheme);
    });
    applyTheme(getPreferredTheme());
    initMobileMenu();
  });

  window.HealthPilotTheme = {
    toggle: toggleTheme,
    getTheme: getPreferredTheme,
  };
})();
