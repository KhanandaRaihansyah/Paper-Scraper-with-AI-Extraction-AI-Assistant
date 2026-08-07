import time
import threading
from datetime import datetime
from models.models import (
    SessionLocal, ScrapingSession, Keyword,
    SemanticScholarPaper, ArxivPaper, IeeePaper, PubmedPaper, CrossrefPaper,
    SessionSemanticScholarPaper, SessionArxivPaper, SessionIeeePaper, SessionPubmedPaper, SessionCrossrefPaper
)
from services.semantic_scholar_service import fetch_semantic_scholar
from services.arxiv_service import fetch_arxiv
from services.ieee_service import fetch_ieee
from services.pubmed_service import fetch_pubmed
from services.crossref_service import fetch_crossref
from services.validation_service import is_valid_paper
from services.dedup_service import normalize_title, is_duplicate
from services.pdf_service import queue_pdf_download

def run_scraping_session(session_id, keyword_text, requested_amount, source_option):
    db = SessionLocal()
    session = db.query(ScrapingSession).get(session_id)
    
    if not session:
        db.close()
        return

    # Parameter Pagination
    ss_offset = 0
    arxiv_start = 0
    ieee_offset = 0
    pubmed_offset = 0
    crossref_offset = 0
    batch_size = 30

    # Penghitung retry untuk SS saat rate-limited
    ss_retry_count = 0
    SS_MAX_RETRY = 2

    # Penanda jika sumber data sudah kehabisan hasil
    ss_exhausted = False if source_option in ['semantic_scholar', 'both', 'all'] else True
    arxiv_exhausted = False if source_option in ['arxiv', 'both', 'all'] else True
    ieee_exhausted = False if source_option in ['ieee', 'all'] else True
    pubmed_exhausted = False if source_option in ['pubmed', 'all'] else True
    crossref_exhausted = False if source_option in ['crossref', 'all'] else True

    try:
        while session.new_papers_count < requested_amount:
            
            if ss_exhausted and arxiv_exhausted and ieee_exhausted and pubmed_exhausted and crossref_exhausted:
                break 
            
            candidates = []
            
            # 1. Tarik dari Semantic Scholar
            if not ss_exhausted:
                ss_data = fetch_semantic_scholar(keyword_text, limit=batch_size, offset=ss_offset)
                if not ss_data:
                    ss_retry_count += 1
                    if ss_retry_count >= SS_MAX_RETRY:
                        print(f"[SS] Tidak ada data setelah {SS_MAX_RETRY}x percobaan, dianggap habis.")
                        ss_exhausted = True
                    else:
                        print(f"[SS] Percobaan {ss_retry_count}/{SS_MAX_RETRY} gagal, jeda 10 detik...")
                        time.sleep(10)
                else:
                    ss_retry_count = 0
                    candidates.extend(ss_data)
                    ss_offset += batch_size
                    
            # 2. Tarik dari arXiv
            if not arxiv_exhausted:
                arxiv_data = fetch_arxiv(keyword_text, start=arxiv_start, max_results=batch_size)
                if not arxiv_data:
                    arxiv_exhausted = True
                else:
                    candidates.extend(arxiv_data)
                    arxiv_start += batch_size

            # 3. Tarik dari IEEE Xplore
            if not ieee_exhausted:
                ieee_data = fetch_ieee(keyword_text, offset=ieee_offset, limit=batch_size)
                if not ieee_data:
                    ieee_exhausted = True
                else:
                    candidates.extend(ieee_data)
                    ieee_offset += batch_size

            # 4. Tarik dari PubMed / Europe PMC
            if not pubmed_exhausted:
                pubmed_data = fetch_pubmed(keyword_text, offset=pubmed_offset, limit=batch_size)
                if not pubmed_data:
                    pubmed_exhausted = True
                else:
                    candidates.extend(pubmed_data)
                    pubmed_offset += batch_size

            # 5. Tarik dari Crossref
            if not crossref_exhausted:
                crossref_data = fetch_crossref(keyword_text, offset=crossref_offset, limit=batch_size)
                if not crossref_data:
                    crossref_exhausted = True
                else:
                    candidates.extend(crossref_data)
                    crossref_offset += batch_size

            if not candidates:
                break

            session.total_found += len(candidates)
            db.commit()

            # 3. Proses setiap paper kandidat
            for paper_data in candidates:
                if session.new_papers_count >= requested_amount:
                    break 

                if not is_valid_paper(paper_data):
                    session.invalid_skipped_count += 1
                    db.commit()
                    continue
                
                title_norm = normalize_title(paper_data['title'])
                source = paper_data['source']

                if is_duplicate(db, title_norm, source):
                    session.duplicate_skipped_count += 1
                    rel = None
                    if source == 'semantic_scholar':
                        ex = db.query(SemanticScholarPaper).filter_by(title_normalized=title_norm).first()
                        if ex: rel = SessionSemanticScholarPaper(session_id=session.id, paper_id=ex.id, is_duplicate=True)
                    elif source == 'arxiv':
                        ex = db.query(ArxivPaper).filter_by(title_normalized=title_norm).first()
                        if ex: rel = SessionArxivPaper(session_id=session.id, paper_id=ex.id, is_duplicate=True)
                    elif source in ('ieee', 'crossref_ieee'):
                        ex = db.query(IeeePaper).filter_by(title_normalized=title_norm).first()
                        if ex: rel = SessionIeeePaper(session_id=session.id, paper_id=ex.id, is_duplicate=True)
                    elif source == 'pubmed':
                        ex = db.query(PubmedPaper).filter_by(title_normalized=title_norm).first()
                        if ex: rel = SessionPubmedPaper(session_id=session.id, paper_id=ex.id, is_duplicate=True)
                    elif source == 'crossref':
                        ex = db.query(CrossrefPaper).filter_by(title_normalized=title_norm).first()
                        if ex: rel = SessionCrossrefPaper(session_id=session.id, paper_id=ex.id, is_duplicate=True)

                    if rel:
                        db.add(rel)
                    db.commit()
                    continue

                # Simpan metadata paper baru sesuai sumbernya
                new_paper = None
                rel = None
                if source == 'semantic_scholar':
                    new_paper = SemanticScholarPaper(
                        title=paper_data['title'], title_normalized=title_norm,
                        abstract=paper_data['abstract'], authors=paper_data['authors'],
                        year=paper_data['year'], external_id=paper_data.get('external_id'),
                        paper_url=paper_data['paper_url'], pdf_url=paper_data.get('pdf_url')
                    )
                    db.add(new_paper)
                    db.flush()
                    rel = SessionSemanticScholarPaper(session_id=session.id, paper_id=new_paper.id, is_duplicate=False)
                elif source == 'arxiv':
                    new_paper = ArxivPaper(
                        title=paper_data['title'], title_normalized=title_norm,
                        abstract=paper_data['abstract'], authors=paper_data['authors'],
                        year=paper_data['year'], external_id=paper_data.get('external_id'),
                        paper_url=paper_data['paper_url'], pdf_url=paper_data.get('pdf_url')
                    )
                    db.add(new_paper)
                    db.flush()
                    rel = SessionArxivPaper(session_id=session.id, paper_id=new_paper.id, is_duplicate=False)
                elif source in ('ieee', 'crossref_ieee'):
                    new_paper = IeeePaper(
                        title=paper_data['title'], title_normalized=title_norm,
                        abstract=paper_data['abstract'], authors=paper_data['authors'],
                        year=paper_data['year'], external_id=paper_data.get('external_id'),
                        paper_url=paper_data['paper_url'], pdf_url=paper_data.get('pdf_url')
                    )
                    db.add(new_paper)
                    db.flush()
                    rel = SessionIeeePaper(session_id=session.id, paper_id=new_paper.id, is_duplicate=False)
                elif source == 'pubmed':
                    new_paper = PubmedPaper(
                        title=paper_data['title'], title_normalized=title_norm,
                        abstract=paper_data['abstract'], authors=paper_data['authors'],
                        year=paper_data['year'], external_id=paper_data.get('external_id'),
                        paper_url=paper_data['paper_url'], pdf_url=paper_data.get('pdf_url')
                    )
                    db.add(new_paper)
                    db.flush()
                    rel = SessionPubmedPaper(session_id=session.id, paper_id=new_paper.id, is_duplicate=False)
                elif source == 'crossref':
                    new_paper = CrossrefPaper(
                        title=paper_data['title'], title_normalized=title_norm,
                        abstract=paper_data['abstract'], authors=paper_data['authors'],
                        year=paper_data['year'], external_id=paper_data.get('external_id'),
                        paper_url=paper_data['paper_url'], pdf_url=paper_data.get('pdf_url')
                    )
                    db.add(new_paper)
                    db.flush()
                    rel = SessionCrossrefPaper(session_id=session.id, paper_id=new_paper.id, is_duplicate=False)

                if rel:
                    db.add(rel)

                session.new_papers_count += 1
                db.commit()
                print(f"[OK ({source.upper().replace('CROSSREF_IEEE','IEEE/Crossref')})] Tersimpan ({session.new_papers_count}/{requested_amount}): {paper_data['title'][:60]}")

                # Luncurkan download PDF di background — tidak menghalangi loop scraping
                if paper_data.get('pdf_url'):
                    queue_pdf_download(paper_data['title'], paper_data['pdf_url'])

        session.status = 'completed'
        session.finished_at = datetime.utcnow()
        db.commit()
        print(f"[SELESAI] Sesi {session_id}: {session.new_papers_count} paper tersimpan. PDF didownload di background.")

    except Exception as e:
        print(f"Error pada sesi {session_id}: {e}")
        session.status = 'failed'
        session.finished_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()

def start_scraping_background(session_id, keyword_text, requested_amount, source_option):
    thread = threading.Thread(
        target=run_scraping_session, 
        args=(session_id, keyword_text, requested_amount, source_option)
    )
    thread.daemon = True
    thread.start()