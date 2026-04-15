import os
import csv
import math
import argparse
from collections import Counter
from typing import List, Tuple, Dict

from PIL import Image


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".gif", ".tiff"}


def srgb_to_linear(value: int) -> float:
    v = value / 255.0
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def rgb_to_lab(r: int, g: int, b: int) -> Tuple[float, float, float]:
    rl = srgb_to_linear(r)
    gl = srgb_to_linear(g)
    bl = srgb_to_linear(b)

    x = (rl * 0.4124564 + gl * 0.3575761 + bl * 0.1804375) / 0.95047
    y = (rl * 0.2126729 + gl * 0.7151522 + bl * 0.0721750) / 1.00000
    z = (rl * 0.0193339 + gl * 0.1191920 + bl * 0.9503041) / 1.08883

    def f(t: float) -> float:
        return t ** (1 / 3) if t > 0.008856 else (7.787 * t) + (16 / 116)

    fx = f(x)
    fy = f(y)
    fz = f(z)

    l = (116 * fy) - 16
    a = 500 * (fx - fy)
    b_value = 200 * (fy - fz)
    return l, a, b_value


def quantize_color(r: int, g: int, b: int, step: int = 32) -> Tuple[int, int, int]:
    qr = min(255, round(r / step) * step)
    qg = min(255, round(g / step) * step)
    qb = min(255, round(b / step) * step)
    return qr, qg, qb


def is_background_pixel(r: int, g: int, b: int, a: int, white_threshold: int = 245) -> bool:
    if a == 0:
        return True
    return r >= white_threshold and g >= white_threshold and b >= white_threshold


def normalize_histogram(values: List[int]) -> List[float]:
    total = sum(values)
    if total == 0:
        return [0.0 for _ in values]
    return [v / total for v in values]


def get_bin_index(value: float, minimum: float, maximum: float, bins: int) -> int:
    if value <= minimum:
        return 0
    if value >= maximum:
        return bins - 1
    ratio = (value - minimum) / (maximum - minimum)
    return min(bins - 1, max(0, int(math.floor(ratio * bins))))


def analyze_image(
    image_path: str,
    bins: int = 8,
    resize_max: int = 300,
    top_colors_count: int = 6,
    white_threshold: int = 245,
) -> Dict[str, str]:
    with Image.open(image_path) as img:
        img = img.convert("RGBA")

        width, height = img.size
        longest_side = max(width, height)
        if longest_side > resize_max:
            scale = resize_max / float(longest_side)
            new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        pixels = list(img.getdata())

    total_l = 0.0
    total_a = 0.0
    total_b = 0.0
    used_pixel_count = 0

    hist_l = [0] * bins
    hist_a = [0] * bins
    hist_b = [0] * bins
    color_counter: Counter = Counter()

    for r, g, b, a in pixels:
        if is_background_pixel(r, g, b, a, white_threshold=white_threshold):
            continue

        l_value, a_value, b_value = rgb_to_lab(r, g, b)
        total_l += l_value
        total_a += a_value
        total_b += b_value
        used_pixel_count += 1

        hist_l[get_bin_index(l_value, 0.0, 100.0, bins)] += 1
        hist_a[get_bin_index(a_value, -128.0, 127.0, bins)] += 1
        hist_b[get_bin_index(b_value, -128.0, 127.0, bins)] += 1

        qr, qg, qb = quantize_color(r, g, b, step=32)
        color_counter[(qr, qg, qb)] += 1

    if used_pixel_count == 0:
        avg_l = avg_a = avg_b = 0.0
    else:
        avg_l = total_l / used_pixel_count
        avg_a = total_a / used_pixel_count
        avg_b = total_b / used_pixel_count

    norm_l = normalize_histogram(hist_l)
    norm_a = normalize_histogram(hist_a)
    norm_b = normalize_histogram(hist_b)

    top_colors = color_counter.most_common(top_colors_count)
    top_color_parts = []
    for (r, g, b), count in top_colors:
        percentage = (count / used_pixel_count * 100.0) if used_pixel_count else 0.0
        top_color_parts.append(f"{r}:{g}:{b}:{percentage:.2f}")

    return {
        "file_name": os.path.basename(image_path),
        "file_path": os.path.abspath(image_path),
        "avg_lab_l": f"{avg_l:.6f}",
        "avg_lab_a": f"{avg_a:.6f}",
        "avg_lab_b": f"{avg_b:.6f}",
        "used_pixels": str(used_pixel_count),
        "hist_l": "|".join(f"{v:.8f}" for v in norm_l),
        "hist_a": "|".join(f"{v:.8f}" for v in norm_a),
        "hist_b": "|".join(f"{v:.8f}" for v in norm_b),
        "top_colors": "|".join(top_color_parts),
    }


def find_images(folder: str) -> List[str]:
    image_paths = []
    for root, _, files in os.walk(folder):
        for name in files:
            ext = os.path.splitext(name)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                image_paths.append(os.path.join(root, name))
    image_paths.sort()
    return image_paths


def write_csv(rows: List[Dict[str, str]], output_csv: str) -> None:
    fieldnames = [
        "file_name",
        "file_path",
        "avg_lab_l",
        "avg_lab_a",
        "avg_lab_b",
        "used_pixels",
        "hist_l",
        "hist_a",
        "hist_b",
        "top_colors",
    ]

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))

    parser = argparse.ArgumentParser(
        description="Scan a folder of images and build a CSV index with Lab color features."
    )
    parser.add_argument(
        "input_folder",
        nargs="?",
        default=script_dir,
        help="Folder containing images. Defaults to the folder where this script is saved.",
    )
    parser.add_argument(
        "output_csv",
        nargs="?",
        default=os.path.join(script_dir, "image_index.csv"),
        help="Output CSV path. Defaults to image_index.csv next to this script.",
    )
    parser.add_argument("--bins", type=int, default=8, help="Number of histogram bins per Lab channel")
    parser.add_argument(
        "--resize-max",
        type=int,
        default=300,
        help="Resize longest image side to this value before analysis for speed",
    )
    parser.add_argument(
        "--top-colors",
        type=int,
        default=6,
        help="How many dominant quantized colors to store",
    )
    parser.add_argument(
        "--white-threshold",
        type=int,
        default=245,
        help="Pixels at or above this RGB threshold are treated as white background",
    )
    args = parser.parse_args()

    image_paths = find_images(args.input_folder)
    if not image_paths:
        print("No supported images found.")
        return

    rows = []
    total = len(image_paths)

    for index, image_path in enumerate(image_paths, start=1):
        try:
            row = analyze_image(
                image_path=image_path,
                bins=args.bins,
                resize_max=args.resize_max,
                top_colors_count=args.top_colors,
                white_threshold=args.white_threshold,
            )
            rows.append(row)
            print(f"[{index}/{total}] Indexed: {image_path}")
        except Exception as exc:
            print(f"[{index}/{total}] Skipped: {image_path} ({exc})")

    write_csv(rows, args.output_csv)
    print(f"Done. Wrote {len(rows)} image records to: {args.output_csv}")


if __name__ == "__main__":
    main()
