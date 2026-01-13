import argparse
import os
from pathlib import Path
from typing import List, Tuple, Optional

from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# ---------- Helpers ----------
MM_TO_PT = 72.0 / 25.4

def mm(x: float) -> float:
    return x * MM_TO_PT

def list_images(folder: Path) -> List[Path]:
    exts = {".jpg", ".jpeg", ".png"}
    files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in exts]
    # Natural-ish sort: 1,2,10 instead of 1,10,2 when filenames are numeric
    def sort_key(p: Path):
        stem = p.stem
        return (stem.zfill(32), p.name.lower())
    return sorted(files, key=sort_key)

def match_pairs(fronts: List[Path], backs: List[Path], mode: str) -> List[Tuple[Path, Path]]:
    if mode == "by_name":
        back_map = {b.stem: b for b in backs}
        pairs = []
        missing = []
        for f in fronts:
            b = back_map.get(f.stem)
            if b is None:
                missing.append(f.name)
            else:
                pairs.append((f, b))
        if missing:
            raise RuntimeError(
                "Back images missing for these front files (by_name mode):\n  " +
                "\n  ".join(missing)
            )
        return pairs

    # mode == "by_order"
    if len(fronts) != len(backs):
        raise RuntimeError(f"Front/back counts differ: {len(fronts)} vs {len(backs)}")
    return list(zip(fronts, backs))

def draw_image_fit(c: canvas.Canvas, img_path: Path, x: float, y: float, w: float, h: float):
    """
    Draw image to fit within (w,h) while preserving aspect ratio (letterbox if needed).
    (x,y) is lower-left in PDF coordinate.
    """
    with Image.open(img_path) as im:
        im = im.convert("RGB")
        iw, ih = im.size
        # scale to fit
        scale = min(w / iw, h / ih)
        dw, dh = iw * scale, ih * scale
        dx = x + (w - dw) / 2.0
        dy = y + (h - dh) / 2.0

        # ReportLab can take a PIL image via temp file is slower; use filename directly
        # but ensure the image is in a supported format; JPG/PNG are fine.
        c.drawImage(str(img_path), dx, dy, dw, dh, preserveAspectRatio=True, mask='auto')


def positions_grid(
    page_w: float, page_h: float,
    card_w: float, card_h: float,
    cols: int, rows: int,
    margin_left: float, margin_right: float,
    margin_top: float, margin_bottom: float,
    gap_x: float, gap_y: float
) -> List[Tuple[float, float]]:
    """
    Returns list of (x,y) lower-left positions for each slot in row-major order.
    Coordinates in points.
    """
    usable_w = page_w - margin_left - margin_right
    usable_h = page_h - margin_top - margin_bottom

    need_w = cols * card_w + (cols - 1) * gap_x
    need_h = rows * card_h + (rows - 1) * gap_y

    if need_w > usable_w + 1e-6 or need_h > usable_h + 1e-6:
        raise RuntimeError(
            f"Layout does not fit A4 with current settings.\n"
            f"Needed: {need_w/MM_TO_PT:.1f}mm × {need_h/MM_TO_PT:.1f}mm, "
            f"Usable: {usable_w/MM_TO_PT:.1f}mm × {usable_h/MM_TO_PT:.1f}mm.\n"
            f"Reduce margins/gaps or card size, or change grid."
        )

    start_x = margin_left + (usable_w - need_w) / 2.0
    # PDF origin at bottom-left; margin_top is from top edge
    start_y_top = page_h - margin_top - (usable_h - need_h) / 2.0  # top baseline for grid block

    pos = []
    for r in range(rows):
        for col in range(cols):
            x = start_x + col * (card_w + gap_x)
            # y: from top down
            y_top_of_row = start_y_top - r * (card_h + gap_y)
            y = y_top_of_row - card_h
            pos.append((x, y))
    return pos

def draw_cut_marks(c: canvas.Canvas, slots: List[Tuple[float, float]], card_w: float, card_h: float,
                   mark_len: float = mm(3), stroke: float = 0.3):
    """
    Optional: small cut marks outside each card corner.
    """
    c.setLineWidth(stroke)
    for (x, y) in slots:
        # corners: (x,y), (x+card_w,y), (x,y+card_h), (x+card_w,y+card_h)
        corners = [
            (x, y), (x + card_w, y), (x, y + card_h), (x + card_w, y + card_h)
        ]
        for (cx, cy) in corners:
            # horizontal mark
            c.line(cx - mark_len, cy, cx + mark_len, cy)
            # vertical mark
            c.line(cx, cy - mark_len, cx, cy + mark_len)

# ---------- Main ----------
def main():
    ap = argparse.ArgumentParser(description="Place front/back card JPGs onto A4 PDF pages for duplex printing.")
    ap.add_argument("--fronts", required=True, help="Folder containing front images (JPG/PNG).")
    ap.add_argument("--backs", required=True, help="Folder containing back images (JPG/PNG).")
    ap.add_argument("--out", default="cards_a4_duplex.pdf", help="Output PDF filename.")
    ap.add_argument("--match", choices=["by_name", "by_order"], default="by_name",
                    help="Pairing strategy: by_name (same stem) or by_order (sorted order).")

    # Layout defaults: poker size 63x88mm, 3x3 grid on A4
    ap.add_argument("--card_w_mm", type=float, default=63.0, help="Card width in mm.")
    ap.add_argument("--card_h_mm", type=float, default=88.0, help="Card height in mm.")
    ap.add_argument("--cols", type=int, default=3, help="Columns per page.")
    ap.add_argument("--rows", type=int, default=3, help="Rows per page.")

    ap.add_argument("--margin_left_mm", type=float, default=10.0)
    ap.add_argument("--margin_right_mm", type=float, default=10.0)
    ap.add_argument("--margin_top_mm", type=float, default=10.0)
    ap.add_argument("--margin_bottom_mm", type=float, default=10.0)

    ap.add_argument("--gap_x_mm", type=float, default=3.0, help="Horizontal gap between cards in mm.")
    ap.add_argument("--gap_y_mm", type=float, default=3.0, help="Vertical gap between cards in mm.")

    ap.add_argument("--cut_marks", action="store_true", help="Draw small cut marks.")
    args = ap.parse_args()

    fronts_dir = Path(args.fronts)
    backs_dir = Path(args.backs)
    if not fronts_dir.is_dir():
        raise RuntimeError(f"Fronts folder not found: {fronts_dir}")
    if not backs_dir.is_dir():
        raise RuntimeError(f"Backs folder not found: {backs_dir}")

    fronts = list_images(fronts_dir)
    backs = list_images(backs_dir)
    if not fronts:
        raise RuntimeError("No front images found.")
    if not backs:
        raise RuntimeError("No back images found.")

    pairs = match_pairs(fronts, backs, args.match)

    page_w, page_h = A4
    card_w = mm(args.card_w_mm)
    card_h = mm(args.card_h_mm)
    cols, rows = args.cols, args.rows
    per_page = cols * rows

    slots = positions_grid(
        page_w, page_h,
        card_w, card_h,
        cols, rows,
        mm(args.margin_left_mm), mm(args.margin_right_mm),
        mm(args.margin_top_mm), mm(args.margin_bottom_mm),
        mm(args.gap_x_mm), mm(args.gap_y_mm)
    )

    c = canvas.Canvas(args.out, pagesize=A4)

    total = len(pairs)
    for start in range(0, total, per_page):
        batch = pairs[start:start + per_page]

        # Page: fronts
        for i, (f, _) in enumerate(batch):
            x, y = slots[i]
            draw_image_fit(c, f, x, y, card_w, card_h)
        if args.cut_marks:
            draw_cut_marks(c, slots[:len(batch)], card_w, card_h)
        c.showPage()

        # Page: backs (same positions, same order, no mirroring)
        for i, (_, b) in enumerate(batch):
            x, y = slots[i]
            draw_image_fit(c, b, x, y, card_w, card_h)
        if args.cut_marks:
            draw_cut_marks(c, slots[:len(batch)], card_w, card_h)
        c.showPage()

    c.save()
    print(f"Done. Wrote: {args.out}")
    print(f"Cards: {total}, Pages: {((total + per_page - 1) // per_page) * 2} (front/back alternating)")

if __name__ == "__main__":
    main()
