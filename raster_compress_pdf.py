import argparse
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
import io

def raster_compress_pdf(input_pdf: Path, output_pdf: Path, dpi: int = 300, quality: int = 85):
    """
    Re-render each page at a target DPI, encode as JPEG, and rebuild a PDF.
    Page physical size stays the same; file size usually drops substantially.
    pdf页面图片化
    """
    src = fitz.open(str(input_pdf))
    dst = fitz.open()

    zoom = dpi / 72.0  # resize DPI / DPI可以自己根据需求改
    mat = fitz.Matrix(zoom, zoom)

    for i in range(len(src)):
        page = src.load_page(i)

        pix = page.get_pixmap(matrix=mat, alpha=False)  
        img = Image.open(io.BytesIO(pix.tobytes("ppm"))).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        jpg_bytes = buf.getvalue()
        rect = page.rect
        new_page = dst.new_page(width=rect.width, height=rect.height)
        new_page.insert_image(rect, stream=jpg_bytes)
    dst.save(str(output_pdf), deflate=True, garbage=4, clean=True)
    dst.close()
    src.close()

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Compress PDF by rasterizing pages to JPEG and rebuilding PDF.")
    ap.add_argument("input", help="Input PDF")
    ap.add_argument("output", help="Output PDF")
    ap.add_argument("--dpi", type=int, default=300, help="Render DPI (default: 300)")
    ap.add_argument("--quality", type=int, default=85, help="JPEG quality 1-95 (default: 85)")
    args = ap.parse_args()

    raster_compress_pdf(Path(args.input), Path(args.output), dpi=args.dpi, quality=args.quality)
    print(f"Saved: {args.output}")
