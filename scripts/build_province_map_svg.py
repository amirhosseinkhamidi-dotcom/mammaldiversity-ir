#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_province_map_svg.py — یک‌بار اجرا می‌شود تا از روی مرزهای اداری واقعی
استان‌های ایران (geoBoundaries, ODbL — © OpenStreetMap contributors) یک
نقشه‌ی SVG سبک و تعاملی بسازد: assets/img/iran-provinces.svg

این یک اسکریپت دیتا-پایپ‌لاین نیست (مثل mdd_iran_to_json.py) — یک ابزار
ساخت اَسِت است، شبیه فشرده‌سازی عکس هیرو. خروجی‌اش دستی قابل ویرایش/بازتولید
است، فقط وقتی لازم شد (مثلاً مرز جدید، سطح جزئیات متفاوت) دوباره اجرا کنید.

استفاده:
    python3 build_province_map_svg.py مسیر/به/geoBoundaries-IRN-ADM1_simplified.geojson
"""

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "assets" / "img" / "iran-provinces.svg"

# نام انگلیسی shapeName در دیتاست geoBoundaries → نام فارسی رسمی استان
EN_TO_FA = {
    "East Azerbaijan": "آذربایجان شرقی",
    "West Azerbaijan": "آذربایجان غربی",
    "Ardabil": "اردبیل",
    "Isfahan": "اصفهان",
    "Alborz": "البرز",
    "Ilam": "ایلام",
    "Bushehr": "بوشهر",
    "Tehran": "تهران",
    "Chaharmahal and Bakhtiari": "چهارمحال و بختیاری",
    "South Khorasan": "خراسان جنوبی",
    "Razavi Khorasan": "خراسان رضوی",
    "North Khorasan": "خراسان شمالی",
    "Khuzestan": "خوزستان",
    "Zanjan": "زنجان",
    "Semnan": "سمنان",
    "Sistan and Baluchestan": "سیستان و بلوچستان",
    "Fars": "فارس",
    "Qazvin": "قزوین",
    "Qom": "قم",
    "Kurdistan": "کردستان",
    "Kerman": "کرمان",
    "Kermanshah": "کرمانشاه",
    "Kohgiluyeh and Boyer-Ahmad": "کهگیلویه و بویراحمد",
    "Golestan": "گلستان",
    "Gilan": "گیلان",
    "Lorestan": "لرستان",
    "Mazandaran": "مازندران",
    "Markazi": "مرکزی",
    "Hormozgan": "هرمزگان",
    "Hamadan": "همدان",
    "Yazd": "یزد",
}

SIMPLIFY_TOLERANCE_DEG = 0.035  # تقریباً چند کیلومتر — کافی برای نقشه‌ی شماتیک وب
SVG_WIDTH = 760


def rdp(points, epsilon):
    """Ramer–Douglas–Peucker — ساده‌سازی یک خط‌شکسته با حفظ شکل کلی."""
    if len(points) < 3:
        return points

    def perp_dist(pt, a, b):
        if a == b:
            return math.hypot(pt[0] - a[0], pt[1] - a[1])
        x1, y1 = a; x2, y2 = b; x0, y0 = pt
        num = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1)
        den = math.hypot(y2 - y1, x2 - x1)
        return num / den

    dmax, index = 0.0, 0
    for i in range(1, len(points) - 1):
        d = perp_dist(points[i], points[0], points[-1])
        if d > dmax:
            dmax, index = d, i

    if dmax > epsilon:
        left = rdp(points[: index + 1], epsilon)
        right = rdp(points[index:], epsilon)
        return left[:-1] + right
    return [points[0], points[-1]]


def load_polygons(geojson_path: Path):
    """برمی‌گرداند: {نام_فارسی: [ [ (lon,lat), ... ], ... ]}  — هر آیتم یک حلقه‌ی بیرونی."""
    data = json.loads(geojson_path.read_text(encoding="utf-8"))
    by_province: dict[str, list] = {}

    for feat in data["features"]:
        en_name = feat["properties"]["shapeName"]
        fa_name = EN_TO_FA.get(en_name)
        if not fa_name:
            print(f"هشدار: نام ناشناخته در geojson نادیده گرفته شد: {en_name}", file=sys.stderr)
            continue

        geom = feat["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        rings = []
        for poly in polys:
            outer = poly[0]  # فقط حلقه‌ی بیرونی؛ حفره‌های داخلی (بسیار کوچک/نادر) صرف‌نظر می‌شود
            pts = [(pt[0], pt[1]) for pt in outer]
            simplified = rdp(pts, SIMPLIFY_TOLERANCE_DEG)
            rings.append(simplified)
        by_province.setdefault(fa_name, []).extend(rings)

    missing = set(EN_TO_FA.values()) - set(by_province)
    if missing:
        print(f"هشدار: این استان‌ها در geojson پیدا نشدند: {missing}", file=sys.stderr)

    return by_province


def build_svg(by_province: dict) -> str:
    all_lons = [lon for rings in by_province.values() for ring in rings for lon, lat in ring]
    all_lats = [lat for rings in by_province.values() for ring in rings for lon, lat in ring]
    lon_min, lon_max = min(all_lons), max(all_lons)
    lat_min, lat_max = min(all_lats), max(all_lats)
    lat_mid = (lat_min + lat_max) / 2
    x_scale = math.cos(math.radians(lat_mid))  # تصحیح نسبت طول جغرافیایی در این عرض جغرافیایی

    lon_span = (lon_max - lon_min) * x_scale
    lat_span = lat_max - lat_min
    scale = SVG_WIDTH / lon_span
    svg_height = lat_span * scale

    def project(lon, lat):
        x = (lon - lon_min) * x_scale * scale
        y = (lat_max - lat) * scale  # y رو به پایین در SVG؛ عرض جغرافیایی رو به بالا
        return round(x, 1), round(y, 1)

    path_els = []
    for fa_name, rings in sorted(by_province.items()):
        d_parts = []
        for ring in rings:
            projected = [project(lon, lat) for lon, lat in ring]
            d = "M " + " L ".join(f"{x},{y}" for x, y in projected) + " Z"
            d_parts.append(d)
        d_attr = " ".join(d_parts)
        safe_name = fa_name.replace('"', "")
        path_els.append(
            f'  <path class="province" data-province="{safe_name}" d="{d_attr}">'
            f"<title>{safe_name}</title></path>"
        )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SVG_WIDTH:.1f} {svg_height:.1f}" '
        f'role="group" aria-label="نقشه‌ی استان‌های ایران">\n'
        + "\n".join(path_els)
        + "\n</svg>\n"
    )


def main():
    if len(sys.argv) < 2:
        print("استفاده: python3 build_province_map_svg.py مسیر_geojson.geojson", file=sys.stderr)
        sys.exit(1)

    by_province = load_polygons(Path(sys.argv[1]))
    svg = build_svg(by_province)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(svg, encoding="utf-8")
    print(f"نوشته شد: {OUT_PATH} ({len(svg)} بایت، {len(by_province)} استان)")


if __name__ == "__main__":
    main()
