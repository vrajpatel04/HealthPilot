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
    document.querySelectorAll(".theme-toggle-btn").forEach(function (btn) {
      btn.setAttribute("aria-label", theme === "dark" ? "Switch to light mode" : "Switch to dark mode");
      const iconSun = btn.querySelector(".icon-sun");
      const iconMoon = btn.querySelector(".icon-moon");
      if (iconSun && iconMoon) {
        iconSun.classList.toggle("hidden", theme !== "dark");
        iconMoon.classList.toggle("hidden", theme === "dark");
      }
    });
  }

  function toggleTheme() {
    const isDark = document.documentElement.classList.contains("dark");
    const nextTheme = isDark ? "light" : "dark";
    localStorage.setItem(THEME_KEY, nextTheme);
    applyTheme(nextTheme);
  }

  function setMobileMenuOpen(menuBtn, menuContainer, isOpen) {
    if (!menuBtn || !menuContainer) return;
    menuBtn.setAttribute("aria-expanded", String(isOpen));
    menuContainer.classList.toggle("hidden", !isOpen);
    menuContainer.classList.toggle("mobile-menu-open", isOpen);
    const iconMenu = menuBtn.querySelector(".icon-menu");
    const iconClose = menuBtn.querySelector(".icon-close");
    if (iconMenu && iconClose) {
      iconMenu.classList.toggle("hidden", isOpen);
      iconClose.classList.toggle("hidden", !isOpen);
    }
    document.body.classList.toggle("mobile-menu-active", isOpen);
  }

  function initMobileMenu() {
    const menuBtn = document.getElementById("mobile-menu-btn");
    const menuContainer = document.getElementById("mobile-menu");
    if (!menuBtn || !menuContainer) return;

    menuBtn.addEventListener("click", function () {
      const isOpen = menuBtn.getAttribute("aria-expanded") === "true";
      setMobileMenuOpen(menuBtn, menuContainer, !isOpen);
    });

    document.addEventListener("click", function (event) {
      if (menuBtn.getAttribute("aria-expanded") !== "true") return;
      const target = event.target;
      if (!menuContainer.contains(target) && !menuBtn.contains(target)) {
        setMobileMenuOpen(menuBtn, menuContainer, false);
      }
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && menuBtn.getAttribute("aria-expanded") === "true") {
        setMobileMenuOpen(menuBtn, menuContainer, false);
        menuBtn.focus();
      }
    });

    window.addEventListener("resize", function () {
      if (window.innerWidth >= 1024) {
        setMobileMenuOpen(menuBtn, menuContainer, false);
      }
    });
  }

  function initProfileMenu() {
    const profileBtn = document.getElementById("profile-menu-btn");
    const profileMenu = document.getElementById("profile-menu");
    if (!profileBtn || !profileMenu) return;

    function setProfileOpen(isOpen) {
      profileBtn.setAttribute("aria-expanded", String(isOpen));
      profileMenu.classList.toggle("hidden", !isOpen);
    }

    profileBtn.addEventListener("click", function (event) {
      event.stopPropagation();
      const isOpen = profileBtn.getAttribute("aria-expanded") === "true";
      setProfileOpen(!isOpen);
    });

    document.addEventListener("click", function (event) {
      if (profileBtn.getAttribute("aria-expanded") !== "true") return;
      if (!profileMenu.contains(event.target) && !profileBtn.contains(event.target)) {
        setProfileOpen(false);
      }
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && profileBtn.getAttribute("aria-expanded") === "true") {
        setProfileOpen(false);
        profileBtn.focus();
      }
    });
  }

  function initTheme() {
    applyTheme(getPreferredTheme());
  }

  function init() {
    document.querySelectorAll(".theme-toggle-btn").forEach(function (btn) {
      btn.addEventListener("click", toggleTheme);
    });
    applyTheme(getPreferredTheme());
    initMobileMenu();
    initProfileMenu();
  }

  initTheme();

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  window.HealthPilotTheme = {
    toggle: toggleTheme,
    getTheme: getPreferredTheme,
  };
})();
