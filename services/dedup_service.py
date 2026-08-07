import re
from models.models import (
    SemanticScholarPaper, ArxivPaper,
    IeeePaper, PubmedPaper, CrossrefPaper
)

def normalize_title(title):
    if not title:
        return ""
    # Ubah ke lowercase
    title = title.lower()
    # Hapus semua tanda baca
    title = re.sub(r'[^\w\s]', '', title)
    # Hapus spasi berlebih
    title = re.sub(r'\s+', ' ', title).strip()
    return title

def is_duplicate(db_session, title_normalized, source=None):
    """Cek apakah judul sudah ada di database (lintas 5 sumber: Semantic Scholar, arXiv, IEEE, PubMed, Crossref)."""
    if not title_normalized:
        return False

    for model in [SemanticScholarPaper, ArxivPaper, IeeePaper, PubmedPaper, CrossrefPaper]:
        exists = db_session.query(model.id).filter_by(title_normalized=title_normalized).first()
        if exists is not None:
            return True

    return False