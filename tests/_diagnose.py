"""Jalankan langsung run_scraping_session tanpa Flask untuk melihat error asli."""
import sys, traceback
sys.path.insert(0, '.')

print("=== Step 1: Test import orchestrator ===")
try:
    from services.orchestrator import run_scraping_session
    print("Import OK")
except Exception as e:
    print(f"IMPORT GAGAL: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n=== Step 2: Test DB koneksi ===")
try:
    from models.models import SessionLocal, ScrapingSession, Keyword
    db = SessionLocal()
    count = db.query(ScrapingSession).count()
    print(f"DB OK, total sesi: {count}")
    db.close()
except Exception as e:
    print(f"DB GAGAL: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n=== Step 3: Test arXiv fetch ===")
try:
    from services.arxiv_service import fetch_arxiv
    results = fetch_arxiv("IoT", start=0, max_results=5)
    print(f"arXiv OK, dapat {len(results)} paper")
    for p in results[:2]:
        print(f"  - year={p.get('year')} pdf={'Ada' if p.get('pdf_url') else 'NULL'} | {p.get('title','')[:50]}")
except Exception as e:
    print(f"arXiv GAGAL: {e}")
    traceback.print_exc()

print("\n=== Step 4: Buat sesi test dan jalankan scraping (5 paper, arxiv) ===")
try:
    from models.models import init_db
    init_db()

    db = SessionLocal()
    kw = db.query(Keyword).filter_by(keyword_normalized='iot test').first()
    if not kw:
        kw = Keyword(keyword_text='iot test', keyword_normalized='iot test')
        db.add(kw)
        db.commit()

    sesi = ScrapingSession(
        keyword_id=kw.id,
        requested_amount=3,
        source_option='arxiv'
    )
    db.add(sesi)
    db.commit()
    sesi_id = sesi.id
    db.close()

    print(f"Sesi test dibuat dengan ID={sesi_id}, mulai scraping...")
    run_scraping_session(sesi_id, 'IoT', 3, 'arxiv')

    db = SessionLocal()
    sesi = db.query(ScrapingSession).get(sesi_id)
    print(f"\nHasil: status={sesi.status} | new={sesi.new_papers_count} | invalid_skip={sesi.invalid_skipped_count} | total_found={sesi.total_found}")
    db.close()

except Exception as e:
    print(f"SCRAPING GAGAL: {e}")
    traceback.print_exc()
