"""Cek berapa paper dari daftar 45 yang ada di DB paper_extractions."""
import re
from models.models import SessionLocal, PaperExtraction
from services.paper_list_45 import PAPER_TITLES_45

def normalize(t):
    if not t:
        return ""
    t = t.lower().strip()
    # hapus tanda baca non-alfanumerik untuk pencocokan lebih luwes
    t = re.sub(r'[^\w\s]', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

db = SessionLocal()
all_records = db.query(PaperExtraction).filter_by(extraction_status='success').all()
db.close()

# Buat index DB
db_index = {}
for r in all_records:
    key = normalize(r.title or r.original_title or '')
    db_index[key] = r

found = []
not_found = []
for title in PAPER_TITLES_45:
    key = normalize(title)
    if key in db_index:
        found.append((title, db_index[key]))
    else:
        # Coba partial match (70% kata pertama cocok)
        matched = None
        for db_key, rec in db_index.items():
            if key[:50] in db_key or db_key[:50] in key:
                matched = rec
                break
        if matched:
            found.append((title, matched))
        else:
            not_found.append(title)

print(f"\nCocok di DB  : {len(found)}")
print(f"Tidak cocok  : {len(not_found)}")
if not_found:
    print("\nTIDAK DITEMUKAN:")
    for t in not_found:
        print(f"  - {t[:80]}")
