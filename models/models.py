from datetime import datetime
from sqlalchemy import Text, create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import os

Base = declarative_base()

# 1. Tabel Keywords
class Keyword(Base):
    __tablename__ = 'keywords'
    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword_text = Column(String, nullable=False)
    keyword_normalized = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("ScrapingSession", back_populates="keyword")

# 2. Tabel Scraping Sessions (Riwayat)
class ScrapingSession(Base):
    __tablename__ = 'scraping_sessions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword_id = Column(Integer, ForeignKey('keywords.id'))
    requested_amount = Column(Integer)
    source_option = Column(String) # 'semantic_scholar', 'arxiv', atau 'both'
    total_found = Column(Integer, default=0)
    new_papers_count = Column(Integer, default=0)
    duplicate_skipped_count = Column(Integer, default=0)
    invalid_skipped_count = Column(Integer, default=0)
    status = Column(String, default='running') # 'running', 'completed', 'failed'
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    keyword = relationship("Keyword", back_populates="sessions")

# 3A. Tabel Hasil Paper - Semantic Scholar
class SemanticScholarPaper(Base):
    __tablename__ = 'semantic_scholar_papers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    title_normalized = Column(String, unique=True, nullable=False) # Mencegah duplikat internal S2
    abstract = Column(String)
    authors = Column(String)
    year = Column(Integer)
    external_id = Column(String) # Corpus ID
    paper_url = Column(String)
    pdf_url = Column(String, nullable=True)
    pdf_local_path = Column(String, nullable=True)
    pdf_downloaded = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# 3B. Tabel Hasil Paper - arXiv
class ArxivPaper(Base):
    __tablename__ = 'arxiv_papers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    title_normalized = Column(String, unique=True, nullable=False) # Mencegah duplikat internal arXiv
    abstract = Column(String)
    authors = Column(String)
    year = Column(Integer)
    external_id = Column(String) # arXiv ID
    paper_url = Column(String)
    pdf_url = Column(String, nullable=True)
    pdf_local_path = Column(String, nullable=True)
    pdf_downloaded = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# 3C. Tabel Hasil Paper - IEEE Xplore
class IeeePaper(Base):
    __tablename__ = 'ieee_papers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    title_normalized = Column(String, unique=True, nullable=False)
    abstract = Column(String)
    authors = Column(String)
    year = Column(Integer)
    external_id = Column(String)
    paper_url = Column(String)
    pdf_url = Column(String, nullable=True)
    pdf_local_path = Column(String, nullable=True)
    pdf_downloaded = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# 3D. Tabel Hasil Paper - PubMed / Europe PMC
class PubmedPaper(Base):
    __tablename__ = 'pubmed_papers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    title_normalized = Column(String, unique=True, nullable=False)
    abstract = Column(String)
    authors = Column(String)
    year = Column(Integer)
    external_id = Column(String)
    paper_url = Column(String)
    pdf_url = Column(String, nullable=True)
    pdf_local_path = Column(String, nullable=True)
    pdf_downloaded = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# 3E. Tabel Hasil Paper - Crossref
class CrossrefPaper(Base):
    __tablename__ = 'crossref_papers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    title_normalized = Column(String, unique=True, nullable=False)
    abstract = Column(String)
    authors = Column(String)
    year = Column(Integer)
    external_id = Column(String)
    paper_url = Column(String)
    pdf_url = Column(String, nullable=True)
    pdf_local_path = Column(String, nullable=True)
    pdf_downloaded = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# 4A. Tabel Relasi Sesi <-> Semantic Scholar
class SessionSemanticScholarPaper(Base):
    __tablename__ = 'session_semantic_scholar_papers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('scraping_sessions.id'))
    paper_id = Column(Integer, ForeignKey('semantic_scholar_papers.id'))
    is_duplicate = Column(Boolean, default=False)

# 4B. Tabel Relasi Sesi <-> arXiv
class SessionArxivPaper(Base):
    __tablename__ = 'session_arxiv_papers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('scraping_sessions.id'))
    paper_id = Column(Integer, ForeignKey('arxiv_papers.id'))
    is_duplicate = Column(Boolean, default=False)

# 4C. Tabel Relasi Sesi <-> IEEE Xplore
class SessionIeeePaper(Base):
    __tablename__ = 'session_ieee_papers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('scraping_sessions.id'))
    paper_id = Column(Integer, ForeignKey('ieee_papers.id'))
    is_duplicate = Column(Boolean, default=False)

# 4D. Tabel Relasi Sesi <-> PubMed
class SessionPubmedPaper(Base):
    __tablename__ = 'session_pubmed_papers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('scraping_sessions.id'))
    paper_id = Column(Integer, ForeignKey('pubmed_papers.id'))
    is_duplicate = Column(Boolean, default=False)

# 4E. Tabel Relasi Sesi <-> Crossref
class SessionCrossrefPaper(Base):
    __tablename__ = 'session_crossref_papers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('scraping_sessions.id'))
    paper_id = Column(Integer, ForeignKey('crossref_papers.id'))
    is_duplicate = Column(Boolean, default=False)


# ==========================================
# Konfigurasi Database & Fungsi Inisialisasi
# ==========================================
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database')
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, 'scraper.db')

engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Fungsi untuk membuat file database dan tabel jika belum ada."""
    Base.metadata.create_all(engine)
    with engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
        conn.exec_driver_sql("PRAGMA busy_timeout=10000;")
        # Auto-migration: Tambahkan kolom search_keyword jika belum ada pada database lama
        try:
            conn.exec_driver_sql("ALTER TABLE paper_extractions ADD COLUMN search_keyword VARCHAR;")
        except Exception:
            pass

    # Auto-backfill: Sinkronkan search_keyword ekstraksi lama dengan keyword riwayat scraping
    try:
        db = SessionLocal()
        models = [
            (SemanticScholarPaper, SessionSemanticScholarPaper),
            (ArxivPaper, SessionArxivPaper),
            (IeeePaper, SessionIeeePaper),
            (PubmedPaper, SessionPubmedPaper),
            (CrossrefPaper, SessionCrossrefPaper),
        ]
        unlinked = db.query(PaperExtraction).filter((PaperExtraction.search_keyword.is_(None)) | (PaperExtraction.search_keyword == '')).all()
        for ext in unlinked:
            title = ext.original_title or ext.title
            found_kw = None
            for m_paper, m_rel in models:
                papers = db.query(m_paper).filter(m_paper.title == title).all()
                for p in papers:
                    rels = db.query(m_rel).filter(m_rel.paper_id == p.id).all()
                    for r in rels:
                        sess = db.get(ScrapingSession, r.session_id)
                        if sess and sess.keyword:
                            found_kw = sess.keyword.keyword_text
                            break
                    if found_kw: break
                if found_kw: break
            if found_kw:
                ext.search_keyword = found_kw
        db.commit()
        db.close()
    except Exception:
        pass

    print(f"Database berhasil diinisialisasi di: {DB_PATH}")


# Tabel hasil ekstraksi AI per paper
class PaperExtraction(Base):
    __tablename__ = 'paper_extractions'
    id = Column(Integer, primary_key=True)
    original_title = Column(String)
    source_type = Column(String)
    search_keyword = Column(String, nullable=True)  # Keyword pencarian/scraping

    # 15 Kolom Hasil Ekstraksi AI
    doi = Column(String)
    title = Column(String)
    authors = Column(String)
    year = Column(String)
    abstract = Column(Text)
    relevance = Column(Text)
    systematic_review = Column(Text)
    publisher = Column(String)
    application = Column(String)
    system = Column(String)
    algorithm = Column(String)
    dataset = Column(String)
    keyword = Column(String)
    publication_type = Column(String)
    journal_name = Column(String)

    # Link PDF dan halaman jurnal
    pdf_url = Column(String)
    paper_url = Column(String)

    # Kolom contribution & limitations
    contribution = Column(Text)   # Kontribusi utama / novelty penelitian
    limitations = Column(Text)    # Keterbatasan penelitian

    # Status ekstraksi: 'success' atau 'failed'
    extraction_status = Column(String, default='success')
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


# Tabel PDF yang sudah diunduh ke lokal
class StoredPDF(Base):
    __tablename__ = 'stored_pdfs'
    id = Column(Integer, primary_key=True)
    paper_title = Column(String)
    pdf_url = Column(String, unique=True)
    file_path = Column(String)  # Jalur folder lokal tempat PDF disimpan
    created_at = Column(DateTime, default=datetime.utcnow)