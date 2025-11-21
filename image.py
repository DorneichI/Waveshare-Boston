"""Generate an 800x480 PNG summarizing MBTA departures and simple weather.

This module builds a display image for an e-paper panel using Pillow.
It supports optional SVG icon rendering when `cairosvg` is installed.
"""

from PIL import Image, ImageDraw, ImageFont
import os
import io
import math
from datetime import datetime
import cairosvg

def _load_font(size, bold=False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _open_icon(path, size=(32, 32)):
    """Open an icon file. If it's an SVG, try converting with cairosvg; otherwise open with PIL.

    Returns a PIL Image or None on failure.
    """
    if not path:
        return None
    try:
        im = Image.open(path)
        im = im.convert("RGBA")
        resample = Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.ANTIALIAS
        im.thumbnail(size, resample)
        return im
    except Exception:
        if str(path).lower().endswith('.svg'):
            try:
                png_bytes = cairosvg.svg2png(url=path)
                im = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
                resample = Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.ANTIALIAS
                im.thumbnail(size, resample)
                return im
            except Exception:
                return None
        return None


def create_image(departures, weather):
    """Create an 800x480 PNG summarizing departures and weather.

    departures: list of dicts, each with 'name' and 'departures' (list of strings)
    weather: dict-like with keys like 'current_temp', 'condition', 'max_temp', 'min_temp', 'rain'

    Returns absolute path to the generated PNG file.
    """
    W, H = 800, 480
    img = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(img)

    # Fonts
    title_font = _load_font(36)
    heading_font = _load_font(24)
    text_font = _load_font(20)
    small_font = _load_font(16)

    padding = 16

    title = "MBTA Live Departures"
    try:
        bbox = draw.textbbox((0, 0), title, font=title_font)
        title_w = bbox[2] - bbox[0]
    except Exception:
        title_w, _ = draw.textsize(title, font=title_font)
    draw.text(((W - title_w) / 2, padding), title, font=title_font, fill="black")

    draw.line([(padding, 72), (W - padding, 72)], fill="black", width=2)

    cur_temp = weather.get("current_temp") if isinstance(weather, dict) else None
    cond = weather.get("condition") if isinstance(weather, dict) else None
    max_t = weather.get("max_temp") if isinstance(weather, dict) else None
    min_t = weather.get("min_temp") if isinstance(weather, dict) else None
    rain = weather.get("rain") if isinstance(weather, dict) else None

    banner_y = 80
    banner_h = 56
    parts = []
    if cur_temp is not None:
        parts.append(f"temp {cur_temp}\u00B0C")
    if max_t is not None and min_t is not None:
        parts.append(f"high {max_t}\u00B0C low {min_t}\u00B0C")
    if rain is not None:
        parts.append(f"rain {rain}%")
    banner_text = "  |  ".join(parts) if parts else "Weather data unavailable"

    try:
        tbbox = draw.textbbox((0, 0), banner_text, font=text_font)
        text_w = tbbox[2] - tbbox[0]
        text_h = tbbox[3] - tbbox[1]
    except Exception:
        text_w, text_h = draw.textsize(banner_text, font=text_font)
    banner_x = (W - text_w) / 2
    banner_y_offset = banner_y + (banner_h - text_h) / 2
    draw.text((banner_x, banner_y_offset), banner_text, font=text_font, fill="black")

    divider_y = banner_y + banner_h + 12
    draw.line([(padding, divider_y), (W - padding, divider_y)], fill="black", width=2)

    dep_area_w = W - 2 * padding
    dep_x = padding
    dep_y = banner_y + banner_h + 24
    station_gap = 6
    base_station_name_h = 20
    base_dep_line_h = 18
    box_h = H - dep_y - 36
    
    max_stations = 9
    cols = 3
    stations = departures[:max_stations] if departures else []
    per_col = math.ceil(len(stations) / float(cols)) if stations else 0
    col_gap = 8
    col_w = (dep_area_w - (cols - 1) * col_gap) // cols
    icon_size = (36, 36)

    if not stations:
        draw.text((dep_x, dep_y), "No departure data", font=text_font, fill="black")
    else:
        rows = per_col if per_col else len(stations)
        available_height = box_h - 24
        per_station_h = max(20, available_height // max(1, rows))

        max_lines_per_station = 3
        usable_for_deps = per_station_h - base_station_name_h - station_gap
        if usable_for_deps <= 0:
            dep_lines = 1
        else:
            dep_lines = min(max_lines_per_station, max(1, usable_for_deps // 12))

        if dep_lines > 0:
            dep_line_h = max(10, usable_for_deps // dep_lines)
        else:
            dep_line_h = 12

        total_block_w = cols * col_w + (cols - 1) * col_gap
        left_offset = dep_x + max(0, (dep_area_w - total_block_w) // 2)

        for idx, station in enumerate(stations):
            col = idx // per_col if per_col else 0
            row = idx % per_col if per_col else idx
            sx = left_offset + col * (col_w + col_gap)
            sy = dep_y + row * per_station_h

            name = station.get("name") if isinstance(station, dict) else str(station)
            deps = station.get("departures", []) if isinstance(station, dict) else []
            icon_path = station.get("icon") if isinstance(station, dict) else None

            icon_im = _open_icon(icon_path, size=icon_size) if icon_path else None
            if icon_im:
                img.paste(icon_im, (sx, sy), icon_im)
                text_x = sx + icon_size[0] + 6
            else:
                text_x = sx

            max_name_w = col_w - (icon_size[0] + 12)
            try:
                name_bbox = draw.textbbox((0, 0), name, font=text_font)
                name_w = name_bbox[2] - name_bbox[0]
            except Exception:
                name_w, _ = draw.textsize(name, font=text_font)
            if name_w > max_name_w:
                while name and name_w > max_name_w:
                    name = name[:-1]
                    try:
                        name_bbox = draw.textbbox((0, 0), name + '…', font=text_font)
                        name_w = name_bbox[2] - name_bbox[0]
                    except Exception:
                        name_w, _ = draw.textsize(name + '…', font=text_font)
                name = name + '…'

            draw.text((text_x, sy), name, font=text_font, fill="black")
            for j in range(dep_lines):
                if j < len(deps):
                    d = deps[j]
                    ypos = sy + base_station_name_h + j * dep_line_h
                    d_str = str(d)
                    draw.text((text_x, ypos), d_str, font=small_font, fill="black")

    footer = "Updated: " + datetime.now().strftime("%Y-%m-%d %H:%M")
    draw.text((padding, H - 22), footer, font=small_font, fill="black")

    out_dir = os.path.join(os.path.dirname(__file__), "images")
    try:
        os.makedirs(out_dir, exist_ok=True)
    except Exception:
        out_dir = os.path.dirname(__file__)

    out_path = os.path.join(out_dir, "epaper.png")
    img.save(out_path, format="PNG")

    return os.path.abspath(out_path)

