(function () {
  const FLUSH_INTERVAL_MS = 5000;
  const MAX_QUEUE = 10;
  const SCROLL_BANDS = [25, 50, 75, 100];
  const VISIT_KEY_PREFIX = "hp_product_visit_";

  const queue = [];
  let pageStart = Date.now();
  let flushTimer = null;
  let config = {};

  function nowIso() {
    return new Date().toISOString();
  }

  function enqueue(eventType, metadata, productId) {
    queue.push({
      event_type: eventType,
      product_id: productId || null,
      metadata: metadata || {},
      timestamp: nowIso(),
    });
    if (queue.length >= MAX_QUEUE) {
      flush(false);
    }
  }

  function flush(useBeacon) {
    if (!queue.length) return;
    const payload = { events: queue.splice(0, queue.length) };
    const body = JSON.stringify(payload);
    const url = "/api/v1/events/batch";

    if (useBeacon && navigator.sendBeacon) {
      const blob = new Blob([body], { type: "application/json" });
      navigator.sendBeacon(url, blob);
      return;
    }

    fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body,
      keepalive: true,
    }).catch(function () {
      /* re-queue on failure is omitted to keep Phase 2 simple */
    });
  }

  function trackScroll() {
    const el = document.getElementById("product-description");
    if (!el) return;

    const fired = new Set();
    function onScroll() {
      const rect = el.getBoundingClientRect();
      const visible = Math.min(rect.bottom, window.innerHeight) - Math.max(rect.top, 0);
      const total = rect.height;
      if (total <= 0) return;
      const percent = Math.max(0, Math.min(100, Math.round((visible / total) * 100)));

      SCROLL_BANDS.forEach(function (band) {
        if (percent >= band && !fired.has(band)) {
          fired.add(band);
          enqueue("description_scroll", { scroll_percent: band }, config.productId);
        }
      });
    }

    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  function trackProductReturn() {
    if (!config.productId) return;
    const key = VISIT_KEY_PREFIX + config.productId;
    const count = parseInt(localStorage.getItem(key) || "0", 10) + 1;
    localStorage.setItem(key, String(count));
    if (count > 1) {
      enqueue("product_return", { visit_count: count }, config.productId);
    }
  }

  function trackPageEvents() {
    enqueue("page_view", { page: config.pageType });

    if (config.pageType === "product_detail" && config.productId) {
      enqueue("product_view", { category: config.productCategory || null }, config.productId);
      trackProductReturn();
      trackScroll();
    }

    if (config.pageType === "products" && config.searchQuery) {
      enqueue("search", {
        query: config.searchQuery,
        results_count: config.resultsCount,
      });
    }

    if (config.pageType === "products" && config.category) {
      enqueue("category_filter", { category: config.category });
    }
  }

  function trackTimeOnPage() {
    const duration = Math.round((Date.now() - pageStart) / 1000);
    enqueue("time_on_page", {
      duration_seconds: duration,
      page: window.location.pathname,
    });
  }

  window.EventTracker = {
    init: function (opts) {
      config = opts || {};
      pageStart = Date.now();
      trackPageEvents();

      flushTimer = setInterval(function () {
        flush(false);
      }, FLUSH_INTERVAL_MS);

      document.addEventListener("visibilitychange", function () {
        if (document.visibilityState === "hidden") {
          trackTimeOnPage();
          flush(true);
        }
      });

      window.addEventListener("pagehide", function () {
        trackTimeOnPage();
        flush(true);
      });
    },
  };
})();
