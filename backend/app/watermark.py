"""
Filigrane sur les photos de biens (protection contre la réutilisation des
photos sur d'autres plateformes — même principe qu'Avito.ma sur ses
annonces).

Le texte ("ImmoVision.ma" par défaut, configurable via `watermark_text`) est
incrusté en mosaïque diagonale, semi-transparent, directement dans le
fichier image avant son upload vers MinIO (voir routers/biens.py). Le
filigrane fait donc partie intégrante du fichier stocké — impossible à
retirer côté front-end.
"""
import logging
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from .config import settings

logger = logging.getLogger(__name__)


def apply_watermark(content: bytes, text: str | None = None) -> tuple[bytes, str]:
    """
    Incruste le filigrane sur une image et retourne (bytes, content_type).

    - PNG en entrée -> PNG en sortie (conserve la transparence éventuelle).
    - Tout autre format -> JPEG en sortie (format le plus adapté aux photos).

    best-effort : si `settings.watermark_enabled` est False, ou si l'image
    ne peut pas être décodée par Pillow (fichier corrompu, format exotique),
    l'appelant doit intercepter l'exception et stocker l'original tel quel
    plutôt que de faire échouer tout l'upload (voir routers/biens.py).
    """
    text = text or settings.watermark_text
    if not settings.watermark_enabled or not text:
        raise WatermarkDisabled

    img = Image.open(BytesIO(content))
    original_format = (img.format or "JPEG").upper()
    # Respecte l'orientation EXIF (photos prises au téléphone) avant de
    # figer l'image dans un tableau de pixels.
    img = _exif_transpose(img).convert("RGBA")

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Taille de police proportionnelle à la plus petite dimension de l'image,
    # pour un rendu cohérent quelle que soit la résolution envoyée.
    font_size = max(16, min(img.size) // 16)
    font = ImageFont.load_default(size=font_size)

    bbox = draw.textbbox((0, 0), text, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = font_size

    tile = Image.new("RGBA", (text_w + pad * 2, text_h + pad * 2), (0, 0, 0, 0))
    tile_draw = ImageDraw.Draw(tile)
    tile_draw.text(
        (pad - bbox[0], pad - bbox[1]),
        text,
        font=font,
        fill=(255, 255, 255, 130),  # blanc semi-transparent
        stroke_width=max(1, font_size // 18),
        stroke_fill=(0, 0, 0, 90),  # léger contour sombre : lisible sur fond clair ou foncé
    )
    tile = tile.rotate(-28, expand=True, resample=Image.BICUBIC)

    # Mosaïque décalée une ligne sur deux (motif "brique"), comme les
    # filigranes des banques d'images professionnelles.
    step_x = int(tile.width * 1.4)
    step_y = int(tile.height * 1.7)
    row = 0
    for y in range(-step_y, img.height + step_y, step_y):
        offset = (step_x // 2) if row % 2 else 0
        for x in range(-step_x - offset, img.width + step_x, step_x):
            overlay.alpha_composite(tile, (x, y))
        row += 1

    watermarked = Image.alpha_composite(img, overlay)

    buf = BytesIO()
    if original_format == "PNG":
        watermarked.save(buf, format="PNG", optimize=True)
        content_type = "image/png"
    else:
        watermarked.convert("RGB").save(buf, format="JPEG", quality=88, optimize=True)
        content_type = "image/jpeg"
    return buf.getvalue(), content_type


def _exif_transpose(img: Image.Image) -> Image.Image:
    try:
        from PIL import ImageOps

        return ImageOps.exif_transpose(img) or img
    except Exception:  # pragma: no cover - best-effort uniquement
        return img


class WatermarkDisabled(Exception):
    """Levée quand le filigrane est désactivé via la configuration."""
