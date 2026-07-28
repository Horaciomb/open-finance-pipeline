"""Genera la imagen de preview (Open Graph) del dashboard.

La imagen es un asset ESTÁTICO ya commiteado en `frontend/public/og-image.png`.
Este script sólo hace falta para regenerarla si cambia el texto o la paleta —
no corre en el build ni en CI, por eso Pillow no está en `requirements.txt`.

Uso:
    pip install Pillow
    python scripts/generate_og_image.py

Dimensiones 1200x630 (proporción 1.91:1), el formato que esperan LinkedIn,
WhatsApp, Slack, X y Facebook para la tarjeta grande.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1200, 630

# Paleta: la misma del tema oscuro del dashboard (frontend/src/index.css).
BG = "#16171d"
TEXT_H = "#f3f4f6"
TEXT_MUTED = "#9ca3af"
ACCENT = "#aa3bff"
BORDER = "#2e303a"

# Colores literales de las tres capas Medallion.
LAYERS = [("Bronze", "#cd7f32"), ("Silver", "#c0c0c0"), ("Gold", "#ffd700")]

FONT_DIRS = [Path("C:/Windows/Fonts"), Path("/usr/share/fonts"), Path("/Library/Fonts")]
OUTPUT = Path(__file__).resolve().parents[1] / "frontend" / "public" / "og-image.png"


def _load_font(candidates: list[str], size: int) -> ImageFont.FreeTypeFont:
    """Busca la primera fuente disponible entre varios nombres de archivo.

    Args:
        candidates: Nombres de archivo de fuente, en orden de preferencia.
        size: Tamaño en puntos.

    Returns:
        La fuente cargada.

    Raises:
        FileNotFoundError: Si no se encuentra ninguna de las candidatas.
    """
    for name in candidates:
        for directory in FONT_DIRS:
            path = directory / name
            if path.is_file():
                return ImageFont.truetype(str(path), size)
    raise FileNotFoundError(f"No se encontró ninguna de estas fuentes: {candidates}")


def _draw_sparkline(draw: ImageDraw.ImageDraw) -> None:
    """Dibuja una línea de precios estilizada como marca de agua de fondo."""
    # Serie fija (no aleatoria) para que la imagen sea reproducible bit a bit.
    values = [0.35, 0.30, 0.42, 0.38, 0.52, 0.47, 0.61, 0.55, 0.70, 0.66, 0.82, 0.78, 0.95]
    left, right = 792, 1160
    base, span = 424, 232
    step = (right - left) / (len(values) - 1)
    points = [(left + i * step, base - v * span) for i, v in enumerate(values)]

    # Relleno tenue bajo la curva.
    draw.polygon([*points, (right, base), (left, base)], fill="#2a1b3d")
    draw.line(points, fill=ACCENT, width=5, joint="curve")
    for x, y in points:
        draw.ellipse([x - 6, y - 6, x + 6, y + 6], fill=BG, outline=ACCENT, width=4)


def build_image() -> Image.Image:
    """Construye la tarjeta de preview completa.

    Returns:
        La imagen RGB de 1200x630 lista para guardar.
    """
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    f_title = _load_font(["segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"], 74)
    f_sub = _load_font(["segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"], 33)
    f_layer = _load_font(["segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"], 25)
    f_foot = _load_font(["consola.ttf", "cour.ttf", "DejaVuSansMono.ttf"], 24)

    _draw_sparkline(draw)

    # Barra de acento vertical a la izquierda, como el borde de una tarjeta.
    draw.rectangle([0, 0, 14, HEIGHT], fill=ACCENT)

    x = 80
    draw.text((x, 92), "PROYECTO DE INGENIERÍA DE DATOS", font=f_foot, fill=ACCENT)
    draw.text((x, 148), "Open Finance Pipeline", font=f_title, fill=TEXT_H)
    draw.text((x, 248), "Arquitectura Medallion de punta a punta:", font=f_sub, fill=TEXT_MUTED)
    draw.text((x, 292), "mercados, macro de EE.UU. y brecha cambiaria", font=f_sub, fill=TEXT_MUTED)
    draw.text((x, 336), "de Bolivia.", font=f_sub, fill=TEXT_MUTED)

    # Píldoras Bronze -> Silver -> Gold.
    px, py = x, 420
    for i, (label, color) in enumerate(LAYERS):
        w = int(draw.textlength(label, font=f_layer)) + 44
        draw.rounded_rectangle([px, py, px + w, py + 52], radius=26, outline=color, width=3)
        draw.text((px + 22, py + 13), label, font=f_layer, fill=color)
        px += w + 16
        if i < len(LAYERS) - 1:
            draw.text((px - 2, py + 12), "\u2192", font=f_layer, fill=TEXT_MUTED)
            px += 30

    draw.line([x, 528, WIDTH - 80, 528], fill=BORDER, width=2)
    draw.text(
        (x, 556),
        "Python  ·  dbt  ·  PostgreSQL  ·  FastAPI  ·  React  ·  GitHub Actions",
        font=f_foot,
        fill=TEXT_MUTED,
    )
    return img


def main() -> None:
    """Genera la imagen y la escribe en frontend/public/."""
    img = build_image()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUTPUT, "PNG", optimize=True)
    print(f"Escrito {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
