from models.models import SessionLocal, PaperExtraction
from services.rangkuman_service import build_rangkuman_review, filter_records_by_titles
from services.paper_list_45 import PAPER_TITLES_45
import os

db = SessionLocal()
all_records = db.query(PaperExtraction).filter_by(extraction_status='success').all()
db.close()

records = filter_records_by_titles(all_records, PAPER_TITLES_45)
print(f"Total DB     : {len(all_records)}")
print(f"Setelah filter: {len(records)}")

output = build_rangkuman_review(records)

os.makedirs("exports", exist_ok=True)
out_path = "exports/rangkuman_review_45.docx"
with open(out_path, "wb") as f:
    f.write(output.read())

size_kb = os.path.getsize(out_path) / 1024
print(f"OK: {out_path} ({size_kb:.1f} KB)")
