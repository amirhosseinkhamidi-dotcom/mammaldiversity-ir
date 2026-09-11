(function () {
  "use strict";

  const paths = [...document.querySelectorAll(".province")];
  const side = document.getElementById("mapSide");

  init();

  async function init() {
    let counts = {};
    try {
      const res = await fetch("data/species.json");
      if (res.ok) {
        const data = await res.json();
        counts = countByProvince(data.species);
      }
    } catch (err) {
      // نقشه بدون آمار هم قابل‌استفاده می‌ماند
    }

    paths.forEach((p) => {
      const name = p.dataset.province;
      const count = counts[name] || 0;
      if (count > 0) p.classList.add("has-data");
      p.addEventListener("click", () => onProvinceClick(name, count));
      p.addEventListener("mouseenter", () => showHint(name, count));
    });
  }

  function countByProvince(species) {
    const counts = {};
    species.forEach((sp) => {
      (sp.provinces || []).forEach((pr) => {
        counts[pr.name] = (counts[pr.name] || 0) + 1;
      });
    });
    return counts;
  }

  function showHint(name, count) {
    side.innerHTML = `
      <p class="map-side-province">${escapeHTML(name)}</p>
      <p class="map-side-count">${count > 0 ? `${faDigits(count)} گونه ثبت‌شده` : "داده‌ی پراکنشی ثبت نشده"}</p>
    `;
  }

  function onProvinceClick(name, count) {
    if (count > 0) {
      location.href = "list.html?province=" + encodeURIComponent(name);
      return;
    }
    side.innerHTML = `
      <p class="map-side-province">${escapeHTML(name)}</p>
      <p class="map-side-empty">داده‌ی این استان هنوز جمع‌آوری نشده — پراکنش استانی در حال تکمیل است.</p>
      <p class="map-side-empty-sub">می‌خواهید کمک کنید؟ <a href="README.md">راهنمای تکمیل داده</a> را ببینید.</p>
    `;
  }

  function escapeHTML(str) {
    return String(str).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    })[c]);
  }
})();
