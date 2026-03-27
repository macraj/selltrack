import os

from nicegui import app, ui

from db import get_db, init_db
from models import Category
from services import UPLOAD_DIR, ensure_dirs

# Ensure directories exist
ensure_dirs()

# Serve uploaded images
app.add_static_files('/uploads', str(UPLOAD_DIR))

# Import pages (registers @ui.page routes and @app.get endpoints)
import pages.items   # noqa: F401, E402
import pages.categories  # noqa: F401, E402


def seed_categories():
    defaults = [
        ('elektronika', 'Elektronika'),
        ('meble', 'Meble'),
        ('odziez', 'Odziez'),
        ('ksiazki', 'Ksiazki'),
        ('inne', 'Inne'),
    ]
    with get_db() as db:
        for name, display_name in defaults:
            if not db.query(Category).filter_by(name=name).first():
                db.add(Category(name=name, display_name=display_name))
        db.commit()


init_db()
seed_categories()

if __name__ in {'__main__', '__mp_main__'}:
    host = os.environ.get('SELLTRACK_HOST', '0.0.0.0')
    port = int(os.environ.get('SELLTRACK_PORT', '5000'))
    debug = os.environ.get('SELLTRACK_DEBUG', '').lower() in ('1', 'true')
    ui.run(title='SellTrack', host=host, port=port, reload=debug)
