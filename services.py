import uuid
import zipfile
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageOps

BASEDIR = Path(__file__).parent
UPLOAD_DIR = BASEDIR / 'uploads'
EXPORT_DIR = BASEDIR / 'exports'


def ensure_dirs():
    UPLOAD_DIR.mkdir(exist_ok=True)
    EXPORT_DIR.mkdir(exist_ok=True)


def process_and_save_image(content: bytes, original_filename: str) -> str:
    """Process uploaded image (EXIF rotate, resize, format normalize). Returns saved filename."""
    ext = Path(original_filename).suffix.lower()
    is_png = ext == '.png'
    filename = f"{uuid.uuid4().hex[:8]}.{'png' if is_png else 'jpg'}"
    filepath = UPLOAD_DIR / filename

    filepath.write_bytes(content)

    img = Image.open(filepath)
    img = ImageOps.exif_transpose(img)

    if is_png:
        if img.mode not in ('RGBA', 'LA', 'P'):
            img = img.convert('RGBA')
    else:
        if img.mode in ('RGBA', 'LA', 'P'):
            bg = Image.new('RGB', img.size, (255, 255, 255))
            alpha_img = img.convert('RGBA') if img.mode == 'P' else img
            bg.paste(alpha_img, mask=alpha_img.split()[-1])
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')

    img.thumbnail((1920, 1080), Image.Resampling.LANCZOS)

    if is_png:
        img.save(filepath, 'PNG', optimize=True)
    else:
        img.save(filepath, 'JPEG', quality=85, optimize=True)

    return filename


def delete_image_file(filename: str):
    filepath = UPLOAD_DIR / filename
    if filepath.exists():
        filepath.unlink()


def export_photos_zip(items) -> str:
    """Export all items' photos to a ZIP. Returns zip file path."""
    zip_path = EXPORT_DIR / f"selltrack_export_{datetime.now():%Y%m%d_%H%M%S}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for item in items:
            folder = f"{item.id}_{item.title.replace('/', '_')}"
            for image in item.images:
                img_path = UPLOAD_DIR / image.filename
                if img_path.exists():
                    zf.write(img_path, f"{folder}/{image.filename}")
    return str(zip_path)


def export_item_photos_zip(item) -> str:
    """Export single item's photos to a ZIP. Returns zip file path."""
    safe_title = item.title.replace(' ', '_').replace('/', '_')
    zip_path = EXPORT_DIR / f"photos_{item.id}_{safe_title}_{datetime.now():%Y%m%d_%H%M%S}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for image in item.images:
            img_path = UPLOAD_DIR / image.filename
            if img_path.exists():
                zf.write(img_path, image.filename)
    return str(zip_path)
