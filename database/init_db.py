from app import app, db
from models.models import (
    ScrapeJob, ApiKeyPool, PaperRaw, PaperFilter1, 
    PaperFilter2, PaperFilter3, PaperSummary
)
import os

with app.app_context():
    # Hapus database lama jika ada (opsional, untuk mulai dari nol)
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database', 'app.db')
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Database lama dihapus.")

    # Buat semua tabel berdasarkan model
    db.create_all()
    print("Database baru berhasil dibuat dengan semua tabel!")

    # Opsional: Isi awal untuk api_key_pool jika Anda memiliki key di .env
    # Ini biasanya dijalankan otomatis saat app start, tapi bisa dilakukan manual di sini
    # from services.api_key_manager import initialize_api_key_pool
    # initialize_api_key_pool()