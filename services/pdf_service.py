import os
import threading
import requests
import zipfile
import time
from models.models import SessionLocal, StoredPDF

# Pastikan folder lokal tersedia
PDF_DIR = os.path.join("downloads", "pdf")
if not os.path.exists(PDF_DIR):
    os.makedirs(PDF_DIR)

# Batas maksimal ukuran PDF yang didownload (10 MB)
MAX_PDF_SIZE_BYTES = 10 * 1024 * 1024

# ---------------------------------------------------------
# FUNGSI INTI: Download dan simpan satu PDF ke folder lokal
# ---------------------------------------------------------
def _do_download_pdf(title, pdf_url):
    """
    Download PDF dari URL dan simpan ke folder lokal.
    Dipanggil baik secara langsung maupun dari background thread.
    """
    db = SessionLocal()
    try:
        # Cek apakah sudah ada di database dan filenya benar-benar ada
        existing = db.query(StoredPDF).filter_by(pdf_url=pdf_url).first()
        if existing and existing.file_path and os.path.exists(existing.file_path):
            return True

        headers = {'User-Agent': 'Mozilla/5.0'}
        # timeout=(5, 15): 5 detik connect, 15 detik per-chunk read
        response = requests.get(pdf_url, headers=headers, stream=True, timeout=(5, 15))

        if response.status_code != 200:
            return False

        # Download bertahap dengan batas ukuran
        chunks = []
        total_size = 0
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                chunks.append(chunk)
                total_size += len(chunk)
                if total_size > MAX_PDF_SIZE_BYTES:
                    print(f"⚠️ [SKIP] PDF terlalu besar: {title[:40]}")
                    return False

        content = b''.join(chunks)

        if not content.startswith(b'%PDF'):
            print(f"❌ [REJECTED] Bukan PDF asli: {title[:40]}")
            return False

        safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).rstrip()[:50]
        file_path = os.path.join(PDF_DIR, f"{safe_title}_{int(time.time())}.pdf")

        with open(file_path, "wb") as f:
            f.write(content)

        new_pdf = StoredPDF(paper_title=title, pdf_url=pdf_url, file_path=file_path)
        db.add(new_pdf)
        db.commit()
        print(f"[PDF OK] {title[:50]}")
        return True

    except requests.exceptions.Timeout:
        print(f"⏱️ [TIMEOUT] PDF lambat, dilewati: {title[:40]}")
        return False
    except Exception as e:
        print(f"Gagal download PDF '{title[:40]}': {e}")
        return False
    finally:
        db.close()


# ---------------------------------------------------------
# FUNGSI BACKGROUND: Dipanggil dari orchestrator
# Download berjalan di thread daemon — tidak menghalangi scraping
# ---------------------------------------------------------
def queue_pdf_download(title, pdf_url):
    """Luncurkan download PDF di background thread terpisah."""
    if not pdf_url:
        return
    t = threading.Thread(target=_do_download_pdf, args=(title, pdf_url), daemon=True)
    t.start()


# ---------------------------------------------------------
# FUNGSI LAMA (dipertahankan): Untuk fitur Download ZIP dari UI
# ---------------------------------------------------------
def download_and_store_pdf_during_scrape(title, pdf_url, db_session):
    """Wrapper lama — tetap dipertahankan untuk kompatibilitas."""
    return _do_download_pdf(title, pdf_url)


def download_pdf(url, save_path):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, stream=True, timeout=15)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            return True
        return False
    except Exception as e:
        return False

def create_zip_from_paths(file_paths, zip_filename):
    try:
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in file_paths:
                if os.path.exists(file):
                    arcname = os.path.basename(file)
                    zipf.write(file, arcname)
        return zip_filename
    except Exception as e:
        return None