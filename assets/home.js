(function () {
  "use strict";

  const THREATENED = new Set(["CR", "EN"]);
  const FEATURED_SCI_NAME = "Panthera pardus"; // پلنگ ایرانی — همان گونه‌ی عکس تله‌دوربین در هیرو

  const els = {
    stats: {
      species: document.getElementById("statSpecies"),
      orders: document.getElementById("statOrders"),
      families: document.getElementById("statFamilies"),
      endemic: document.getElementById("statEndemic"),
      threatened: document.getElementById("statThreatened"),
    },
    orderBreakdown: document.getElementById("orderBreakdown"),
    lastUpdated: document.getElementById("lastUpdated"),
    heroSearch: document.getElementById("heroSearch"),
    heroSearchInput: document.getElementById("heroSearchInput"),
    featuredCard: document.getElementById("featuredCard"),
    featuredName: document.getElementById("featuredName"),
    featuredSci: document.getElementById("featuredSci"),
  };

  init();

  async function init() {
    bindSearch();

    let data;
    try {
      const res = await fetch("data/species.json");
      if (!res.ok) throw new Error("HTTP " + res.status);
      data = await res.json();
    } catch (err) {
      return; // صفحه‌ی اصلی بدون آمار هم قابل‌استفاده می‌ماند؛ خطای واقعی در list.html نشان داده می‌شود
    }

    renderStats(data.species);
    renderOrderBreakdown(data.species);
    linkFeaturedSpecies(data.species);
    if (els.lastUpdated) els.lastUpdated.textContent = faDigits(data.meta.updated);
  }

  function bindSearch() {
    if (!els.heroSearch) return;
    els.heroSearch.addEventListener("submit", (e) => {
      e.preventDefault();
      const q = els.heroSearchInput.value.trim();
      location.href = "list.html" + (q ? "?q=" + encodeURIComponent(q) : "");
    });
  }

  function renderStats(species) {
    els.stats.species.textContent = faDigits(species.length);
    els.stats.orders.textContent = faDigits(new Set(species.map((sp) => sp.order)).size);
    els.stats.families.textContent = faDigits(new Set(species.map((sp) => sp.family)).size);
    els.stats.endemic.textContent = faDigits(species.filter((sp) => sp.endemic).length);
    els.stats.threatened.textContent = faDigits(species.filter((sp) => THREATENED.has(sp.iucn)).length);
  }

  function renderOrderBreakdown(species) {
    const counts = {};
    species.forEach((sp) => {
      counts[sp.order] = (counts[sp.order] || 0) + 1;
    });
    const orders = Object.keys(counts).sort((a, b) => counts[b] - counts[a]);
    const max = counts[orders[0]] || 1;

    els.orderBreakdown.innerHTML = orders
      .map((name) => {
        const count = counts[name];
        const pct = Math.round((count / max) * 100);
        return `
          <li>
            <a class="order-bar-row" href="list.html?order=${encodeURIComponent(name)}">
              <span class="order-bar-label">${name}</span>
              <span class="order-bar-track"><span class="order-bar-fill" style="width:${pct}%"></span></span>
              <span class="order-bar-count">${faDigits(count)}</span>
            </a>
          </li>`;
      })
      .join("");
  }

  function linkFeaturedSpecies(species) {
    const sp = species.find((s) => s.scientificName === FEATURED_SCI_NAME);
    if (!sp || !els.featuredCard) return;
    els.featuredCard.href = `species.html?id=${encodeURIComponent(sp.id)}`;
    if (els.featuredName) els.featuredName.textContent = sp.faName || sp.enName;
    if (els.featuredSci) els.featuredSci.textContent = sp.scientificName;
  }
})();
