(function () {
  "use strict";

  const IUCN_LABELS = {
    CR: "بحرانی (CR)",
    EN: "در معرض خطر (EN)",
    VU: "آسیب‌پذیر (VU)",
    NT: "نزدیک به خطر (NT)",
    LC: "کم‌دغدغه (LC)",
    DD: "داده ناکافی (DD)",
    NE: "ارزیابی‌نشده (NE)",
    EX: "منقرض (EX)",
    EW: "منقرض در طبیعت (EW)",
  };

  const TAXO_RANK_LABELS = {
    subclass: "زیررده (Subclass)",
    infraclass: "زیرردهٔ تحتانی (Infraclass)",
    magnorder: "ابرراستهٔ بزرگ (Magnorder)",
    superorder: "ابرراسته (Superorder)",
    order: "راسته (Order)",
    suborder: "زیرراسته (Suborder)",
    infraorder: "زیرراستهٔ تحتانی (Infraorder)",
    parvorder: "خردراسته (Parvorder)",
    superfamily: "ابرتیره (Superfamily)",
    family: "تیره (Family)",
    subfamily: "زیرتیره (Subfamily)",
    tribe: "قبیله (Tribe)",
    subtribe: "زیرقبیله (Subtribe)",
  };

  const COUNTRY_PREVIEW_COUNT = 14;
  const SYNONYM_PREVIEW_COUNT = 8;

  const content = document.getElementById("content");
  const breadcrumbCurrent = document.getElementById("breadcrumbCurrent");

  init();

  async function init() {
    const id = new URLSearchParams(location.search).get("id");
    if (!id) {
      renderNotFound("شناسه‌ی گونه در آدرس مشخص نشده.");
      return;
    }

    let data;
    try {
      const res = await fetch("data/species.json");
      if (!res.ok) throw new Error("HTTP " + res.status);
      data = await res.json();
    } catch (err) {
      renderNotFound(
        "دادهٔ سایت بارگذاری نشد. اگر فایل را مستقیم با دابل‌کلیک باز کرده‌اید، مرورگرها اجازهٔ خواندن data/species.json را از حالت file:// نمی‌دهند — یک سرور محلی ساده اجرا کنید، مثلاً «python -m http.server»."
      );
      return;
    }

    const sp = data.species.find((s) => s.id === id);
    if (!sp) {
      renderNotFound(`هیچ گونه‌ای با شناسه‌ی «${id}» پیدا نشد.`);
      return;
    }

    render(sp);
  }

  function renderNotFound(message) {
    breadcrumbCurrent.textContent = "پیدا نشد";
    content.innerHTML = `
      <section class="wrap not-found">
        <h1>گونه پیدا نشد</h1>
        <p>${escapeHTML(message)}</p>
        <p><a href="list.html">بازگشت به فهرست گونه‌ها</a></p>
      </section>`;
  }

  function render(sp) {
    const displayName = sp.faName || sp.enName || sp.scientificName;
    document.title = `${displayName} — ${sp.scientificName} — پستانداران ایران`;
    breadcrumbCurrent.textContent = displayName;

    const permalink = location.origin + location.pathname + "?id=" + encodeURIComponent(sp.id);
    const today = new Date().toLocaleDateString("fa-IR");

    content.innerHTML = `
      ${headHTML(sp)}
      <div class="wrap species-body">
        <div class="col-main">
          ${taxonomyPanelHTML(sp)}
          ${nomenclaturePanelHTML(sp)}
          ${typeSpecimenPanelHTML(sp)}
          ${synonymsPanelHTML(sp)}
          ${subspeciesPanelHTML(sp)}
          ${permalinkPanelHTML(sp, permalink, today, displayName)}
        </div>
        <div class="col-side">
          ${distributionPanelHTML(sp)}
          ${crossRefPanelHTML(sp)}
        </div>
      </div>
    `;

    bindCopyButton(permalink);
  }

  // ---------- sections ----------

  function headHTML(sp) {
    const faNameHTML = sp.faName
      ? escapeHTML(sp.faName)
      : `<span class="fa-pending">نام فارسی هنوز ثبت نشده</span>`;

    const otherNames = (sp.otherCommonNames || []).length
      ? `<p class="en-name">نام‌های دیگر: ${escapeHTML(sp.otherCommonNames.join("، "))}</p>`
      : "";

    const badges = [
      `<span class="badge">شناسه: ${sp.id}</span>`,
      `<span class="iucn" data-cat="${sp.iucn}">${IUCN_LABELS[sp.iucn] || sp.iucn || "نامشخص"}</span>`,
      sp.endemic ? `<span class="badge endemic">★ بومی ایران</span>` : "",
      sp.extinct ? `<span class="badge endemic">منقرض</span>` : `<span class="badge">${sp.status || "زنده"}</span>`,
      sp.domestic ? `<span class="badge">اهلی</span>` : "",
      sp.flagged ? `<span class="badge" title="این رکورد در MDD برای بازبینی علامت خورده">⚑ نیازمند بازبینی در MDD</span>` : "",
    ].join("");

    return `
      <header class="species-head">
        <div class="wrap">
          <p class="order-tag">${escapeHTML(sp.order || "")} · ${escapeHTML(sp.family || "")}</p>
          <h1>${escapeHTML(sp.scientificName || "")}<span class="authority">${escapeHTML(sp.authority || "")}</span></h1>
          <p class="fa-name">${faNameHTML}</p>
          <p class="en-name">${escapeHTML(sp.enName || "")}</p>
          ${otherNames}
          <div class="badge-row">${badges}</div>
        </div>
      </header>`;
  }

  function taxonomyPanelHTML(sp) {
    const rows = Object.keys(TAXO_RANK_LABELS)
      .map((key) => {
        const val = sp.taxonomy && sp.taxonomy[key];
        if (!val) return "";
        return `<tr><th>${TAXO_RANK_LABELS[key]}</th><td>${escapeHTML(val)}</td></tr>`;
      })
      .join("");

    return `
      <section class="panel">
        <h2>طبقه‌بندی کامل</h2>
        <table class="taxo-table">
          <tbody>
            ${rows}
            <tr><th>جنس (Genus)</th><td><em>${escapeHTML(sp.genus || "—")}</em></td></tr>
            ${sp.subgenus ? `<tr><th>زیرجنس (Subgenus)</th><td><em>${escapeHTML(sp.subgenus)}</em></td></tr>` : ""}
            <tr><th>نام گونه‌ای (Epithet)</th><td><em>${escapeHTML(sp.specificEpithet || "—")}</em></td></tr>
            <tr><th>مؤلف و سال</th><td>${escapeHTML(sp.authority || "—")}</td></tr>
            <tr><th>وضعیت IUCN</th><td>${IUCN_LABELS[sp.iucn] || sp.iucn || "—"}</td></tr>
            <tr><th>بومی ایران؟</th><td>${sp.endemic ? "بله" : "خیر"}</td></tr>
          </tbody>
        </table>
      </section>`;
  }

  function nomenclaturePanelHTML(sp) {
    const n = sp.nomenclature || {};
    const rows = [];
    if (n.originalNameCombination) {
      rows.push(`<tr><th>نام اصلی هنگام توصیف</th><td><em>${escapeHTML(n.originalNameCombination)}</em></td></tr>`);
    }
    if (n.authorityCitation) {
      rows.push(`<tr><th>منبع توصیف</th><td>${escapeHTML(n.authorityCitation)}</td></tr>`);
    }
    if (n.authorityLink) {
      rows.push(`<tr><th>پیوند منبع</th><td><a href="${escapeAttr(n.authorityLink)}" target="_blank" rel="noopener">${escapeHTML(n.authorityLink)}</a></td></tr>`);
    }
    if (!rows.length && !n.taxonomyNotes) return "";

    const notes = n.taxonomyNotes
      ? `<p class="citation" style="margin-top:14px">${escapeHTML(n.taxonomyNotes)}${n.taxonomyNotesCitation ? ` <span style="color:var(--ink-faint)">(${escapeHTML(n.taxonomyNotesCitation)})</span>` : ""}</p>`
      : "";

    return `
      <section class="panel">
        <h2>نام‌گذاری و منبع توصیف</h2>
        ${rows.length ? `<table class="taxo-table"><tbody>${rows.join("")}</tbody></table>` : ""}
        ${notes}
      </section>`;
  }

  function typeSpecimenPanelHTML(sp) {
    const t = sp.typeSpecimen || {};
    if (!t.voucher && !t.kind && !t.locality && !(t.uris && t.uris.length)) return "";

    const rows = [];
    if (t.voucher) rows.push(`<tr><th>نمونه‌ی تیپ</th><td>${escapeHTML(t.voucher)}</td></tr>`);
    if (t.kind) rows.push(`<tr><th>نوع تیپ</th><td>${escapeHTML(t.kind)}</td></tr>`);
    if (t.locality) rows.push(`<tr><th>محل تیپ</th><td>${escapeHTML(t.locality)}</td></tr>`);
    if (t.latitude && t.longitude) {
      rows.push(`<tr><th>مختصات</th><td class="mono-cell">${escapeHTML(t.latitude)}, ${escapeHTML(t.longitude)}</td></tr>`);
    }
    if (t.uris && t.uris.length) {
      const links = t.uris.map((u) => `<a href="${escapeAttr(u)}" target="_blank" rel="noopener">${escapeHTML(u)}</a>`).join("<br>");
      rows.push(`<tr><th>پیوند نمونه</th><td>${links}</td></tr>`);
    }

    return `
      <section class="panel">
        <h2>نمونه‌ی تیپ (Type Specimen)</h2>
        <table class="taxo-table"><tbody>${rows.join("")}</tbody></table>
      </section>`;
  }

  function synonymsPanelHTML(sp) {
    const names = (sp.nomenclature && sp.nomenclature.nominalNames) || [];
    if (!names.length) return "";

    const items = names.map((n) => `<li>${escapeHTML(n)}</li>`).join("");
    const isLong = names.length > SYNONYM_PREVIEW_COUNT;

    return `
      <section class="panel">
        <h2>نام‌ها و مترادف‌ها <span class="count-badge">(${names.length})</span></h2>
        <details ${isLong ? "" : "open"}>
          <summary>${isLong ? `نمایش همه‌ی ${names.length} نام` : "نام‌های ثبت‌شده"}</summary>
          <ul class="synonym-list">${items}</ul>
        </details>
      </section>`;
  }

  function subspeciesPanelHTML(sp) {
    const raw = sp.nomenclature && sp.nomenclature.subspecies;
    if (!raw) return "";

    const entries = raw.split(/;\s*/).filter(Boolean);
    const html = entries.map((e) => `<li>${italicize(escapeHTML(e))}</li>`).join("");
    const isLong = entries.length > 4;

    return `
      <section class="panel">
        <h2>زیرگونه‌ها <span class="count-badge">(${entries.length})</span></h2>
        <details ${isLong ? "" : "open"}>
          <summary>${isLong ? `نمایش همه‌ی ${entries.length} زیرگونه` : "فهرست زیرگونه‌ها"}</summary>
          <ul class="synonym-list">${html}</ul>
        </details>
      </section>`;
  }

  function distributionPanelHTML(sp) {
    const dist = sp.distribution || {};
    const countries = (dist.countries || sp.worldDistribution || []).slice().sort((a, b) => a.localeCompare(b));
    const preview = countries.slice(0, COUNTRY_PREVIEW_COUNT);
    const rest = countries.length - preview.length;
    const countryTags = preview
      .map((c) => {
        const isIran = c.replace("?", "") === "Iran";
        return `<span class="country-tag${isIran ? " is-iran" : ""}">${escapeHTML(c)}</span>`;
      })
      .join("");
    const moreTag = rest > 0 ? `<span class="country-more">+${rest} کشور دیگر</span>` : "";

    const meta = [];
    if (dist.continents && dist.continents.length) {
      meta.push(`<tr><th>قاره</th><td>${escapeHTML(dist.continents.join("، "))}</td></tr>`);
    }
    if (dist.biogeographicRealm && dist.biogeographicRealm.length) {
      meta.push(`<tr><th>قلمرو زیست‌جغرافیایی</th><td>${escapeHTML(dist.biogeographicRealm.join("، "))}</td></tr>`);
    }
    if (dist.subregion) {
      meta.push(`<tr><th>جزئیات زیرمنطقه‌ای</th><td class="mono-cell">${escapeHTML(dist.subregion)}</td></tr>`);
    }

    const notes = dist.notes
      ? `<p class="citation" style="margin-top:14px">${escapeHTML(dist.notes)}${dist.notesCitation ? ` <span style="color:var(--ink-faint)">(${escapeHTML(dist.notesCitation)})</span>` : ""}</p>`
      : "";

    return `
      <section class="panel">
        <h2>پراکنش جهانی <span class="count-badge">(${countries.length} کشور)</span></h2>
        ${countries.length ? `<div class="country-list">${countryTags}${moreTag}</div>` : `<p style="color:var(--ink-soft);font-size:0.88rem">داده‌ی پراکنشی ثبت نشده.</p>`}
        ${meta.length ? `<table class="taxo-table" style="margin-top:14px"><tbody>${meta.join("")}</tbody></table>` : ""}
        ${notes}
        <p style="margin:14px 0 0;font-size:0.78rem;color:var(--ink-faint)">
          پراکنش در سطح استان‌های ایران هنوز جمع‌آوری نشده — این فهرست فقط سطح کشور را نشان می‌دهد.
        </p>
      </section>`;
  }

  function crossRefPanelHTML(sp) {
    const c = sp.crossReference || {};
    const rows = [];
    rows.push(`<tr><th>شناسه‌ی MDD</th><td class="mono-cell">${escapeHTML(sp.mddId || "—")}</td></tr>`);
    if (sp.phylosort != null) rows.push(`<tr><th>ترتیب فیلوژنتیک</th><td class="mono-cell">${sp.phylosort}</td></tr>`);
    if (c.msw3MatchType) rows.push(`<tr><th>تطبیق با MSW3</th><td>${escapeHTML(c.msw3MatchType)}${c.diffSinceMSW3 && c.msw3SciName && c.msw3SciName !== sp.scientificName ? ` — قبلاً: <em>${escapeHTML(c.msw3SciName)}</em>` : ""}</td></tr>`);
    if (c.diffSinceCMW && c.cmwSciName && c.cmwSciName !== sp.scientificName) {
      rows.push(`<tr><th>تفاوت با CMW</th><td>قبلاً: <em>${escapeHTML(c.cmwSciName)}</em></td></tr>`);
    }

    return `
      <section class="panel">
        <h2>متادیتای MDD</h2>
        <table class="taxo-table"><tbody>${rows.join("")}</tbody></table>
        ${sp.mddUrl ? `<p style="margin:14px 0 0;font-size:0.82rem"><a href="${escapeAttr(sp.mddUrl)}" target="_blank" rel="noopener">مشاهده‌ی رکورد اصلی در Mammal Diversity Database ↗</a></p>` : ""}
      </section>`;
  }

  function permalinkPanelHTML(sp, permalink, today, displayName) {
    return `
      <section class="panel">
        <h2>پیوند دائمی و استناد</h2>
        <div class="permalink-box">
          <input type="text" id="permalinkInput" readonly value="${escapeAttr(permalink)}">
          <button class="copy-btn" id="copyBtn" type="button">کپی پیوند</button>
        </div>
        <p class="citation">
          «${escapeHTML(displayName)}» (${escapeHTML(sp.scientificName || "")}) — پستانداران ایران، شناسه ${escapeHTML(sp.id)}.
          بازیابی‌شده در ${today}. آدرس: ${escapeHTML(permalink)}
        </p>
      </section>`;
  }

  function bindCopyButton(permalink) {
    const copyBtn = document.getElementById("copyBtn");
    const permalinkInput = document.getElementById("permalinkInput");
    if (!copyBtn) return;
    copyBtn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(permalink);
      } catch (err) {
        permalinkInput.select();
        document.execCommand("copy");
      }
      copyBtn.textContent = "کپی شد ✓";
      copyBtn.classList.add("is-copied");
      setTimeout(() => {
        copyBtn.textContent = "کپی پیوند";
        copyBtn.classList.remove("is-copied");
      }, 1600);
    });
  }

  // ---------- helpers ----------

  function italicize(escapedStr) {
    return escapedStr.replace(/_(.+?)_/g, "<em>$1</em>");
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

  function escapeAttr(str) {
    return escapeHTML(str);
  }
})();
