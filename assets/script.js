(function () {
  "use strict";

  const state = { data: null, activeOrder: "", activeProvince: "", query: "" };

  const els = {
    stats: {
      species: document.getElementById("statSpecies"),
      endemic: document.getElementById("statEndemic"),
      threatened: document.getElementById("statThreatened"),
    },
    orderChips: document.getElementById("orderChips"),
    allChip: document.querySelector(".chip--all"),
    searchBox: document.getElementById("searchBox"),
    resultCount: document.getElementById("resultCount"),
    grid: document.getElementById("cardGrid"),
    empty: document.getElementById("emptyState"),
    lastUpdated: document.getElementById("lastUpdated"),
    toolbar: document.querySelector(".toolbar"),
  };

  const THREATENED = new Set(["CR", "EN"]);

  init();

  async function init() {
    try {
      const res = await fetch("data/species.json");
      if (!res.ok) throw new Error("HTTP " + res.status);
      state.data = await res.json();
    } catch (err) {
      renderLoadError(err);
      return;
    }
    buildOrderStrip();
    bindEvents();
    applyUrlParams();
    render();
    els.lastUpdated.textContent = state.data.meta.updated;
  }

  function applyUrlParams() {
    const params = new URLSearchParams(location.search);
    const q = params.get("q");
    const order = params.get("order");
    const province = params.get("province");

    if (q) {
      els.searchBox.value = q;
      state.query = q.trim().toLowerCase();
    }
    if (order) {
      const chip = document.querySelector(`.chip[data-order="${CSS.escape(order)}"]`);
      if (chip) {
        document.querySelectorAll(".chip").forEach((c) => c.classList.remove("is-active"));
        chip.classList.add("is-active");
        state.activeOrder = order;
      }
    }
    if (province) {
      state.activeProvince = province;
      renderProvinceBadge();
    }
  }

  function renderProvinceBadge() {
    if (!els.toolbar) return;
    const old = document.getElementById("provinceBadge");
    if (old) old.remove();
    if (!state.activeProvince) return;

    const badge = document.createElement("span");
    badge.id = "provinceBadge";
    badge.className = "province-badge";
    badge.innerHTML = `استان: ${state.activeProvince} <button type="button" aria-label="حذف فیلتر استان">×</button>`;
    badge.querySelector("button").addEventListener("click", () => {
      state.activeProvince = "";
      badge.remove();
      const url = new URL(location.href);
      url.searchParams.delete("province");
      history.replaceState(null, "", url);
      render();
    });
    els.toolbar.appendChild(badge);
  }

  function renderLoadError() {
    els.grid.innerHTML = "";
    els.empty.hidden = false;
    els.empty.textContent =
      "دادهٔ سایت بارگذاری نشد. اگر فایل را مستقیم با دابل‌کلیک باز کرده‌اید، مرورگرها اجازهٔ خواندن data/species.json را از حالت file:// نمی‌دهند — یک سرور محلی ساده اجرا کنید، مثلاً «python -m http.server» در همین پوشه، بعد آدرس localhost را باز کنید.";
  }

  function buildOrderStrip() {
    const counts = {};
    state.data.species.forEach((sp) => {
      counts[sp.order] = (counts[sp.order] || 0) + 1;
    });
    const orders = Object.keys(counts).sort((a, b) => counts[b] - counts[a]);

    els.orderChips.innerHTML = "";
    orders.forEach((name) => {
      const btn = document.createElement("button");
      btn.className = "chip";
      btn.dataset.order = name;
      btn.innerHTML = `${name}<span class="tab-count">${counts[name]}</span>`;
      els.orderChips.appendChild(btn);
    });
  }

  function bindEvents() {
    document.addEventListener("click", (e) => {
      const chip = e.target.closest(".chip");
      if (!chip) return;
      document.querySelectorAll(".chip").forEach((c) => c.classList.remove("is-active"));
      chip.classList.add("is-active");
      state.activeOrder = chip.dataset.order || "";
      render();
    });

    els.searchBox.addEventListener("input", (e) => {
      state.query = e.target.value.trim().toLowerCase();
      render();
    });
  }

  function matches(sp) {
    if (state.activeOrder && sp.order !== state.activeOrder) return false;
    if (state.activeProvince && !(sp.provinces || []).some((pr) => pr.name === state.activeProvince)) {
      return false;
    }

    if (!state.query) return true;
    const haystack = [sp.faName, sp.enName, sp.scientificName, sp.family, sp.order]
      .join(" ")
      .toLowerCase();
    return haystack.includes(state.query);
  }

  function render() {
    const list = state.data.species.filter(matches);

    els.stats.species.textContent = state.data.species.length;
    els.stats.endemic.textContent = state.data.species.filter((sp) => sp.endemic).length;
    els.stats.threatened.textContent = state.data.species.filter((sp) =>
      THREATENED.has(sp.iucn)
    ).length;

    els.resultCount.textContent = `${list.length} از ${state.data.species.length} گونه`;
    els.empty.hidden = list.length !== 0;

    els.grid.innerHTML = list.map(cardHTML).join("");
  }

  function cardHTML(sp) {
    const hasFa = Boolean(sp.faName);
    const headline = hasFa ? sp.faName : sp.enName;
    const subline = hasFa
      ? sp.enName
      : '<span class="fa-pending">نام فارسی هنوز ثبت نشده</span>';
    return `
      <a class="card-link" href="species.html?id=${encodeURIComponent(sp.id)}">
        <article class="card" data-id="${sp.id}">
          <p class="card-order">${sp.order} · ${sp.family}</p>
          <p class="card-sci">${sp.scientificName}<span class="authority">${sp.authority}</span></p>
          <p class="card-fa">${headline}${sp.endemic ? " ★" : ""}</p>
          <p class="card-en">${subline}</p>
          <span class="iucn" data-cat="${sp.iucn}">${sp.iucn}</span>
        </article>
      </a>`;
  }
})();
