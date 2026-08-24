#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
species_fields.py — تعریف یک‌بارِ نگاشت بین فیلدهای data/species.json و
ستون‌های شیت «گونه‌ها»ی اکسل کل دیتابیس. هم build_database_template.py (خروجی
JSON → اکسل) و هم xlsx_to_json.py (ورودی اکسل → JSON) از همین فهرست استفاده
می‌کنند تا دو طرف هرگز از هم جدا نیفتند.

هر آیتم یک FieldSpec است: ستون اکسل چه اسمی دارد، از کجای دیکشنری گونه
خوانده/نوشته می‌شود، و آیا رنگ «قابل‌ویرایش» بگیرد یا «محاسبه‌شده/مرجع».
"""

from dataclasses import dataclass
from typing import Any, Callable, Optional

VALID_IUCN = {"CR", "EN", "VU", "NT", "LC", "DD", "NE", "EX", "EW"}
LIST_SEP = " | "


def get_path(sp: dict, path: str):
    node = sp
    for part in path.split("."):
        if not isinstance(node, dict):
            return None
        node = node.get(part)
    return node


def set_path(sp: dict, path: str, value):
    parts = path.split(".")
    node = sp
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    node[parts[-1]] = value


def fmt_bool(v) -> str:
    return "بله" if v else "خیر"


def parse_bool(v) -> bool:
    return str(v).strip() in ("بله", "1", "true", "True", "بلي")


def fmt_list(v) -> str:
    if not v:
        return ""
    return LIST_SEP.join(str(x) for x in v)


def parse_list(v) -> list:
    if not v or not str(v).strip():
        return []
    return [p.strip() for p in str(v).split("|") if p.strip()]


def fmt_plain(v) -> str:
    if v is None:
        return ""
    return str(v)


def parse_str(v) -> Optional[str]:
    if v is None:
        return None
    v = str(v).strip()
    return v or None


def parse_int(v):
    if v is None or str(v).strip() == "":
        return None
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return None


@dataclass
class FieldSpec:
    header: str
    path: str
    kind: str = "str"  # str | bool | list | int | iucn | computed
    editable: bool = True
    width: int = 18
    italic: bool = False


FIELDS: list[FieldSpec] = [
    FieldSpec("شناسه", "id", "str", editable=True, width=10),
    FieldSpec("شناسه MDD", "mddId", "str", editable=True, width=11),
    FieldSpec("پیوند MDD", "mddUrl", "computed", editable=False, width=34),
    FieldSpec("ترتیب فیلوژنتیک", "phylosort", "int", editable=True, width=12),

    FieldSpec("راسته (Order)", "order", "str", editable=True, width=16),
    FieldSpec("تیره (Family)", "family", "str", editable=True, width=18),
    FieldSpec("نام علمی", "scientificName", "str", editable=True, width=24, italic=True),
    FieldSpec("جنس (Genus)", "genus", "str", editable=True, width=16, italic=True),
    FieldSpec("زیرجنس (Subgenus)", "subgenus", "str", editable=True, width=16, italic=True),
    FieldSpec("نام گونه‌ای (Epithet)", "specificEpithet", "str", editable=True, width=16, italic=True),
    FieldSpec("مؤلف و سال", "authority", "str", editable=True, width=20),

    FieldSpec("نام فارسی", "faName", "str", editable=True, width=24),
    FieldSpec("نام انگلیسی", "enName", "str", editable=True, width=26),
    FieldSpec("نام‌های دیگر", "otherCommonNames", "list", editable=True, width=28),

    FieldSpec("بومی ایران؟", "endemic", "bool", editable=True, width=11),
    FieldSpec("وضعیت زیستی", "status", "str", editable=True, width=12),
    FieldSpec("وضعیت IUCN", "iucn", "iucn", editable=True, width=11),
    FieldSpec("منقرض‌شده؟", "extinct", "bool", editable=True, width=10),
    FieldSpec("اهلی؟", "domestic", "bool", editable=True, width=8),
    FieldSpec("نیازمند بازبینی؟", "flagged", "bool", editable=True, width=12),

    FieldSpec("زیررده (Subclass)", "taxonomy.subclass", "str", editable=True, width=14),
    FieldSpec("زیرردهٔ تحتانی (Infraclass)", "taxonomy.infraclass", "str", editable=True, width=16),
    FieldSpec("ابرراستهٔ بزرگ (Magnorder)", "taxonomy.magnorder", "str", editable=True, width=16),
    FieldSpec("ابرراسته (Superorder)", "taxonomy.superorder", "str", editable=True, width=16),
    FieldSpec("زیرراسته (Suborder)", "taxonomy.suborder", "str", editable=True, width=14),
    FieldSpec("زیرراستهٔ تحتانی (Infraorder)", "taxonomy.infraorder", "str", editable=True, width=16),
    FieldSpec("خردراسته (Parvorder)", "taxonomy.parvorder", "str", editable=True, width=14),
    FieldSpec("ابرتیره (Superfamily)", "taxonomy.superfamily", "str", editable=True, width=16),
    FieldSpec("زیرتیره (Subfamily)", "taxonomy.subfamily", "str", editable=True, width=16),
    FieldSpec("قبیله (Tribe)", "taxonomy.tribe", "str", editable=True, width=14),
    FieldSpec("زیرقبیله (Subtribe)", "taxonomy.subtribe", "str", editable=True, width=14),

    FieldSpec("نام اصلی هنگام توصیف", "nomenclature.originalNameCombination", "str", editable=True, width=22, italic=True),
    FieldSpec("منبع توصیف", "nomenclature.authorityCitation", "str", editable=True, width=40),
    FieldSpec("پیوند منبع توصیف", "nomenclature.authorityLink", "str", editable=True, width=30),
    FieldSpec("نام‌های مترادف", "nomenclature.nominalNames", "list", editable=True, width=40),
    FieldSpec("زیرگونه‌ها", "nomenclature.subspecies", "str", editable=True, width=40),
    FieldSpec("یادداشت رده‌بندی", "nomenclature.taxonomyNotes", "str", editable=True, width=40),
    FieldSpec("منبع یادداشت رده‌بندی", "nomenclature.taxonomyNotesCitation", "str", editable=True, width=30),

    FieldSpec("نمونه‌ی تیپ", "typeSpecimen.voucher", "str", editable=True, width=22),
    FieldSpec("نوع تیپ", "typeSpecimen.kind", "str", editable=True, width=14),
    FieldSpec("پیوند نمونه‌ی تیپ", "typeSpecimen.uris", "list", editable=True, width=30),
    FieldSpec("محل تیپ", "typeSpecimen.locality", "str", editable=True, width=26),
    FieldSpec("عرض جغرافیایی تیپ", "typeSpecimen.latitude", "str", editable=True, width=14),
    FieldSpec("طول جغرافیایی تیپ", "typeSpecimen.longitude", "str", editable=True, width=14),

    FieldSpec("پراکنش جهانی (کشورها)", "distribution.countries", "list", editable=True, width=40),
    FieldSpec("قاره‌ها", "distribution.continents", "list", editable=True, width=20),
    FieldSpec("قلمرو زیست‌جغرافیایی", "distribution.biogeographicRealm", "list", editable=True, width=20),
    FieldSpec("جزئیات زیرمنطقه‌ای", "distribution.subregion", "str", editable=True, width=20),
    FieldSpec("یادداشت پراکنش", "distribution.notes", "str", editable=True, width=34),
    FieldSpec("منبع یادداشت پراکنش", "distribution.notesCitation", "str", editable=True, width=26),

    FieldSpec("نام علمی در CMW", "crossReference.cmwSciName", "str", editable=True, width=20, italic=True),
    FieldSpec("تفاوت با CMW؟", "crossReference.diffSinceCMW", "bool", editable=True, width=10),
    FieldSpec("نوع تطبیق با MSW3", "crossReference.msw3MatchType", "str", editable=True, width=16),
    FieldSpec("نام علمی در MSW3", "crossReference.msw3SciName", "str", editable=True, width=20, italic=True),
    FieldSpec("تفاوت با MSW3؟", "crossReference.diffSinceMSW3", "bool", editable=True, width=10),
]


def field_to_cell(sp: dict, spec: FieldSpec):
    if spec.kind == "computed":
        if spec.path == "mddUrl":
            mdd_id = get_path(sp, "mddId")
            return f"https://www.mammaldiversity.org/taxon/{mdd_id}" if mdd_id else ""
        return fmt_plain(get_path(sp, spec.path))

    v = get_path(sp, spec.path)
    if spec.kind == "bool":
        return fmt_bool(v)
    if spec.kind == "list":
        return fmt_list(v)
    if spec.kind in ("str", "iucn", "int"):
        return fmt_plain(v)
    return fmt_plain(v)


def cell_to_field(sp: dict, spec: FieldSpec, raw_value):
    if spec.kind == "computed":
        return  # همیشه بعداً از mddId دوباره محاسبه می‌شود، از اکسل خوانده نمی‌شود
    if spec.kind == "bool":
        set_path(sp, spec.path, parse_bool(raw_value))
    elif spec.kind == "list":
        set_path(sp, spec.path, parse_list(raw_value))
    elif spec.kind == "int":
        set_path(sp, spec.path, parse_int(raw_value))
    elif spec.kind == "iucn":
        code = (parse_str(raw_value) or "NE").upper()
        set_path(sp, spec.path, code if code in VALID_IUCN else "NE")
    else:
        set_path(sp, spec.path, parse_str(raw_value))
