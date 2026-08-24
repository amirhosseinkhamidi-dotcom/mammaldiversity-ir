#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mdd_iran_to_json.py — استخراج گونه‌های پستاندار ایران از دیتاست رسمی
Mammal Diversity Database (MDD) و تولید data/species.json.

منبع: فایل CSV رسمی MDD (۵۲ ستون)، همان که از
https://github.com/mammaldiversity/mammaldiversity.github.io/raw/refs/heads/master/assets/data/MDD.zip
منتشر می‌شود.

نسخه‌ی فعلی اسکریپت **تقریباً تمام ۵۲ ستون** MDD را برای هر گونه نگه
می‌دارد، نه یک زیرمجموعه‌ی خلاصه‌شده — چون ارزش این پایگاه در همان
جزئیات است (رده‌بندی کامل تا زیرجنس، محل و نوع نمونه‌ی تیپ، نام‌های
مترادف، یادداشت‌های رده‌بندی/پراکنش، شناسه‌ی متقابل با CMW/MSW3 و
پیوند مستقیم به رکورد اصلی در mammaldiversity.org).

آنچه از MDD اصلاً وجود ندارد (و این اسکریپت جعل نمی‌کند): پراکنش در
سطح استان‌های ایران — MDD فقط سطح کشور را پوشش می‌دهد. نام فارسی هم
فقط برای گونه‌هایی که در FA_NAMES (پایین همین فایل) با اطمینان ثبت
شده پر می‌شود؛ برای بقیه خالی می‌ماند.

ردیف‌هایی که کشور توزیع‌شان با «؟» علامت‌گذاری شده (یعنی حضور در ایران
هنوز قطعی نیست) کنار گذاشته می‌شوند.

استفاده:
    python3 mdd_iran_to_json.py مسیر/به/MDD_v2.x_NNNNspecies.csv [مسیر_خروجی.json]
"""

import csv
import json
import sys
from pathlib import Path

VALID_IUCN = {"CR", "EN", "VU", "NT", "LC", "DD", "NE", "EX", "EW"}
NULLISH = {"", "NA", "N/A", "na"}

# نام فارسی فقط برای گونه‌هایی که در منابع جانورشناسی فارسی (کتاب
# «پستانداران ایران»، فهرست‌های IUCN/DoE ترجمه‌شده و مشابه) نام
# جا‌افتاده و بدون ابهام دارند. عمداً ناقص است — نگاه کنید به یادداشت بالا.
FA_NAMES = {
    "Capra_aegagrus": "بز وحشی (پازن)",
    "Gazella_subgutturosa": "آهوی ایرانی",
    "Gazella_bennettii": "آهوی چینکارا",
    "Ovis_vignei": "قوچ و میش اوریال",
    "Ovis_gmelinii": "قوچ و میش موفلون",
    "Cervus_elaphus": "گوزن مرال",
    "Dama_mesopotamica": "گوزن زرد ایرانی",
    "Sus_scrofa": "گراز",
    "Physeter_macrocephalus": "نهنگ عنبر",
    "Balaenoptera_musculus": "نهنگ آبی",
    "Megaptera_novaeangliae": "نهنگ گوژپشت",
    "Delphinus_delphis": "دلفین معمولی",
    "Orcinus_orca": "نهنگ قاتل",
    "Grampus_griseus": "دلفین ریسو",
    "Canis_aureus": "شغال طلایی",
    "Canis_lupus": "گرگ خاکستری",
    "Vulpes_vulpes": "روباه معمولی",
    "Vulpes_cana": "روباه بلوچی",
    "Vulpes_corsac": "روباه کورساک",
    "Vulpes_rueppellii": "روباه شنی",
    "Acinonyx_jubatus": "یوزپلنگ آسیایی",
    "Panthera_pardus": "پلنگ ایرانی",
    "Caracal_caracal": "سیاه‌گوش",
    "Felis_chaus": "گربه جنگلی",
    "Felis_lybica": "گربه وحشی",
    "Felis_margarita": "گربه شنی",
    "Lynx_lynx": "وشق (لینکس اوراسیایی)",
    "Otocolobus_manul": "گربه پالاس",
    "Hyaena_hyaena": "کفتار راه‌راه",
    "Lutra_lutra": "سمور آبی",
    "Martes_foina": "سمور سنگی",
    "Martes_martes": "سمور جنگلی",
    "Meles_canescens": "گورکن",
    "Mellivora_capensis": "گورکن عسل‌خوار",
    "Mustela_nivalis": "راسو",
    "Vormela_peregusna": "راسوی مرقش",
    "Pusa_caspica": "فک خزری",
    "Ursus_arctos": "خرس قهوه‌ای",
    "Ursus_thibetanus": "خرس سیاه آسیایی",
    "Rhinolophus_ferrumequinum": "خفاش نعل‌اسبی بزرگ",
    "Rousettus_aegyptiacus": "خفاش میوه‌خوار مصری",
    "Erinaceus_concolor": "جوجه‌تیغی معمولی",
    "Hemiechinus_auritus": "جوجه‌تیغی گوش‌دراز",
    "Paraechinus_hypomelas": "جوجه‌تیغی بلوچستان",
    "Lepus_europaeus": "خرگوش اروپایی",
    "Ochotona_rufescens": "پیکای افغانی",
    "Equus_hemionus": "گور ایرانی (خرگور)",
    "Hystrix_indica": "تشی هندی",
    "Rhombomys_opimus": "جرد بزرگ",
    "Sciurus_anomalus": "سنجاب قفقازی",
    "Mus_musculus": "موش خانگی",
    "Rattus_rattus": "موش سیاه",
    "Rattus_norvegicus": "موش قهوه‌ای",
}


def die(msg: str) -> None:
    print(f"خطا: {msg}", file=sys.stderr)
    sys.exit(1)


def clean(val):
    """None برای خالی یا سنتینل «NA» که MDD برای رتبه‌های نامعتبر استفاده می‌کند."""
    if val is None:
        return None
    val = str(val).strip()
    return None if val in NULLISH else val


def split_pipe(val):
    val = clean(val)
    if not val:
        return []
    return [p.strip() for p in val.split("|") if p.strip()]


def build_authority(row: dict) -> str:
    author = clean(row.get("authoritySpeciesAuthor"))
    year = clean(row.get("authoritySpeciesYear"))
    if not author and not year:
        return ""
    core = f"{author}, {year}" if author and year else (author or year)
    return f"({core})" if clean(row.get("authorityParentheses")) == "1" else core


def build_iucn(raw) -> str:
    raw = clean(raw)
    if not raw:
        return "NE"
    code = raw.split(" ")[0].strip()
    return code if code in VALID_IUCN else "NE"


def load_rows(csv_path: Path) -> list:
    try:
        with csv_path.open(encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        die(f"فایل پیدا نشد: {csv_path}")
    except Exception as e:
        die(f"خواندن CSV شکست خورد: {e}")


def build_species_json(rows: list) -> dict:
    confirmed = []
    uncertain_count = 0

    for row in rows:
        countries = split_pipe(row.get("countryDistribution"))
        countries_raw = clean(row.get("countryDistribution")) or ""
        if "Iran" in countries:
            confirmed.append(row)
        elif "Iran?" in countries_raw.split("|"):
            uncertain_count += 1

    confirmed.sort(key=lambda r: (r["order"], r["family"], r["sciName"]))

    species_list = []
    for i, row in enumerate(confirmed, start=1):
        sci_key = clean(row["sciName"])  # e.g. "Acinonyx_jubatus"
        sci_name = sci_key.replace("_", " ") if sci_key else None
        countries = split_pipe(row.get("countryDistribution"))
        mdd_id = clean(row.get("id"))

        cmw_sci = clean(row.get("CMW_sciName"))
        msw3_sci = clean(row.get("MSW3_sciName"))

        species_list.append({
            "id": f"IR{i:04d}",
            "mddId": mdd_id,
            "mddUrl": f"https://www.mammaldiversity.org/taxon/{mdd_id}" if mdd_id else None,
            "phylosort": int(row["phylosort"]) if clean(row.get("phylosort")) else None,

            "order": clean(row.get("order")),
            "family": clean(row.get("family")),
            "scientificName": sci_name,
            "genus": clean(row.get("genus")),
            "subgenus": clean(row.get("subgenus")),
            "specificEpithet": clean(row.get("specificEpithet")),
            "authority": build_authority(row),

            "faName": FA_NAMES.get(sci_key, ""),
            "enName": clean(row.get("mainCommonName")) or "",
            "otherCommonNames": split_pipe(row.get("otherCommonNames")),

            "endemic": countries == ["Iran"],
            "status": "منقرض" if clean(row.get("extinct")) == "1" else "زنده",
            "iucn": build_iucn(row.get("iucnStatus")),
            "extinct": clean(row.get("extinct")) == "1",
            "domestic": clean(row.get("domestic")) == "1",
            "flagged": clean(row.get("flagged")) == "1",

            "taxonomy": {
                "subclass": clean(row.get("subclass")),
                "infraclass": clean(row.get("infraclass")),
                "magnorder": clean(row.get("magnorder")),
                "superorder": clean(row.get("superorder")),
                "order": clean(row.get("order")),
                "suborder": clean(row.get("suborder")),
                "infraorder": clean(row.get("infraorder")),
                "parvorder": clean(row.get("parvorder")),
                "superfamily": clean(row.get("superfamily")),
                "family": clean(row.get("family")),
                "subfamily": clean(row.get("subfamily")),
                "tribe": clean(row.get("tribe")),
                "subtribe": clean(row.get("subtribe")),
            },

            "nomenclature": {
                "originalNameCombination": clean(row.get("originalNameCombination")),
                "authorityCitation": clean(row.get("authoritySpeciesCitation")),
                "authorityLink": clean(row.get("authoritySpeciesLink")),
                "nominalNames": split_pipe(row.get("nominalNames")),
                "subspecies": clean(row.get("subspecies")),
                "taxonomyNotes": clean(row.get("taxonomyNotes")),
                "taxonomyNotesCitation": clean(row.get("taxonomyNotesCitation")),
            },

            "typeSpecimen": {
                "voucher": clean(row.get("typeVoucher")),
                "kind": clean(row.get("typeKind")),
                "uris": [u.strip() for u in (clean(row.get("typeVoucherURIs")) or "").split("|") if u.strip()],
                "locality": clean(row.get("typeLocality")),
                "latitude": clean(row.get("typeLocalityLatitude")),
                "longitude": clean(row.get("typeLocalityLongitude")),
            },

            "distribution": {
                "countries": countries,
                "continents": split_pipe(row.get("continentDistribution")),
                "biogeographicRealm": split_pipe(row.get("biogeographicRealm")),
                "subregion": clean(row.get("subregionDistribution")),
                "notes": clean(row.get("distributionNotes")),
                "notesCitation": clean(row.get("distributionNotesCitation")),
            },
            "worldDistribution": countries,  # سازگاری با نسخه‌ی قبلی UI

            "crossReference": {
                "cmwSciName": cmw_sci.replace("_", " ") if cmw_sci else None,
                "diffSinceCMW": clean(row.get("diffSinceCMW")) == "1",
                "msw3MatchType": clean(row.get("MSW3_matchtype")),
                "msw3SciName": msw3_sci.replace("_", " ") if msw3_sci else None,
                "diffSinceMSW3": clean(row.get("diffSinceMSW3")) == "1",
            },
        })

    named = sum(1 for sp in species_list if sp["faName"])

    return {
        "meta": {
            "version": "mdd-iran-2-full",
            "updated": __import__("datetime").date.today().isoformat(),
            "note": (
                f"{len(species_list)} گونه با حضور تأییدشده در ایران، استخراج‌شده از دیتاست رسمی "
                f"Mammal Diversity Database (MDD) توسط mdd_iran_to_json.py — دستی ویرایش نکنید. "
                "هر رکورد تقریباً تمام ۵۲ ستون CSV رسمی MDD را حمل می‌کند: رده‌بندی کامل، محل/نوع "
                "نمونه‌ی تیپ، نام‌های مترادف، یادداشت رده‌بندی و پراکنش، و شناسه‌ی متقابل با "
                "CMW/MSW3 — به‌علاوه‌ی پیوند مستقیم به رکورد اصلی در mammaldiversity.org. "
                f"{uncertain_count} گونه‌ی دیگر در MDD با علامت «؟» (حضور نامطمئن) مشخص شده‌اند و "
                "عمداً از این فهرست کنار گذاشته شدند. "
                f"نام فارسی فقط برای {named} گونه پر شده؛ برای بقیه، به‌جای حدس زدن، خالی گذاشته "
                "شده تا بعداً توسط متخصص تکمیل شود. پراکنش در سطح استان در MDD موجود نیست."
            ),
            "source": "Mammal Diversity Database (MDD), https://www.mammaldiversity.org",
        },
        "species": species_list,
    }


def main():
    if len(sys.argv) < 2:
        die("استفاده: python3 mdd_iran_to_json.py مسیر_CSV.csv [مسیر_خروجی.json]")

    csv_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else (
        Path(__file__).resolve().parent.parent / "data" / "species.json"
    )

    rows = load_rows(csv_path)
    data = build_species_json(rows)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    n = len(data["species"])
    named = sum(1 for sp in data["species"] if sp["faName"])
    endemic = sum(1 for sp in data["species"] if sp["endemic"])
    print(f"نوشته شد: {out_path}")
    print(f"  {n} گونه ({endemic} بومی ایران، {named} با نام فارسی تأییدشده)")


if __name__ == "__main__":
    main()
