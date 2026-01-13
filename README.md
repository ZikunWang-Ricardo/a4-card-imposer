# a4-card-imposer

A lightweight Python tool to impose card images (e.g. poker-size cards) onto A4 pages,
designed specifically for **duplex printing** where front and back pages alternate
naturally (page 1 = fronts, page 2 = backs, etc.).

This project is intended for tabletop and board game prototyping, where designers
need a fast, reliable way to print card decks on standard A4 paper.

---

## Features

- Automatic A4 imposition of card images (default: 3 × 3 layout)
- Designed for duplex printing (front/back pages alternate, no mirroring)
- Supports poker-size cards (63 × 88 mm) by default
- Configurable:
  - Card size
  - Margins
  - Gaps between cards
  - Grid layout (rows × columns)
- Optional cut mark generation
- Pure Python implementation
- Cross-platform (Windows / macOS / Linux)

---

## Typical Use Case

- You have card **fronts and backs as JPG/PNG files**
- You want to print them on **A4 paper**
- You want:
  - Page 1: card fronts  
  - Page 2: corresponding card backs  
  - Page 3: next batch of fronts  
  - Page 4: next batch of backs
- You will use the printer’s **duplex printing** feature

This tool generates a **print-ready PDF** that follows exactly this order.

---

## Installation

### Requirements

- Python 3.9+
- Dependencies:
  - Pillow
  - reportlab

Install dependencies:

```bash
pip install pillow reportlab
```

---

## Project Structure

```
a4-card-imposer/
├─ make_cards_pdf.py
├─ fronts/
│   ├─ 001.jpg
│   ├─ 002.jpg
│   └─ ...
├─ backs/
│   ├─ 001.jpg
│   ├─ 002.jpg
│   └─ ...
├─ README.md
└─ .gitignore
```

---

## Image Pairing Rules

By default, **front and back images are paired by filename**.

Example:
```
fronts/001.jpg  <->  backs/001.jpg
fronts/002.jpg  <->  backs/002.jpg
```

If a matching back image is missing, the script will stop with an error to prevent
incorrect pairing.

---

## Usage

### Basic Command

```bash
python make_cards_pdf.py \
  --fronts fronts \
  --backs backs \
  --out cards_a4_duplex.pdf
```

---

## Duplex Printing Notes

- Disable any **automatic scaling** in the print dialog
- Choose **long-edge or short-edge flip** according to your printer
- Always print **one test sheet first** to confirm alignment

---

## License

GPL-3.0 License
