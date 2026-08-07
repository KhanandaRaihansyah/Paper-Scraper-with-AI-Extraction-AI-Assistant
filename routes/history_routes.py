from flask import Blueprint, jsonify
from models.models import (
    SessionLocal, Keyword, ScrapingSession,
    SemanticScholarPaper, ArxivPaper, IeeePaper, PubmedPaper, CrossrefPaper,
    SessionSemanticScholarPaper, SessionArxivPaper, SessionIeeePaper, SessionPubmedPaper, SessionCrossrefPaper
)

history_bp = Blueprint('history_bp', __name__)

@history_bp.route('/api/history/keywords', methods=['GET'])
def get_keywords_history():
    """Mengambil daftar riwayat keyword beserta jumlah paper yang didapat."""
    with SessionLocal() as db:
        keywords = db.query(Keyword).all()
        result = []
        for kw in keywords:
            sessions = db.query(ScrapingSession).filter_by(keyword_id=kw.id).all()
            total_papers = sum(s.new_papers_count for s in sessions)
            last_session = max(sessions, key=lambda x: x.started_at).started_at if sessions else kw.created_at

            result.append({
                'id': kw.id,
                'keyword': kw.keyword_text,
                'last_scraped': last_session.strftime("%Y-%m-%d %H:%M:%S"),
                'total_sessions': len(sessions),
                'total_papers': total_papers
            })
        return jsonify({'keywords': result})

@history_bp.route('/api/history/keyword/<int:keyword_id>', methods=['GET'])
def get_keyword_papers(keyword_id):
    """Mengambil semua detail paper dari satu keyword tertentu (5 sumber API)."""
    with SessionLocal() as db:
        kw_obj = db.query(Keyword).get(keyword_id)
        kw_text = kw_obj.keyword_text if kw_obj else 'teknologi'

        sessions = db.query(ScrapingSession.id).filter_by(keyword_id=keyword_id).all()
        session_ids = [s[0] for s in sessions]

        models = [
            (SemanticScholarPaper, SessionSemanticScholarPaper, 'Semantic Scholar', 'ss'),
            (ArxivPaper, SessionArxivPaper, 'arXiv', 'ax'),
            (IeeePaper, SessionIeeePaper, 'IEEE Xplore', 'ie'),
            (PubmedPaper, SessionPubmedPaper, 'PubMed', 'pm'),
            (CrossrefPaper, SessionCrossrefPaper, 'Crossref', 'cr')
        ]

        papers_dict = {}
        for m_paper, m_rel, src_name, prefix in models:
            results = db.query(m_paper).join(m_rel).filter(
                m_rel.session_id.in_(session_ids),
                m_rel.is_duplicate.is_(False)
            ).all()
            for p in results:
                papers_dict[f"{prefix}_{p.id}"] = {
                    'title': p.title, 'abstract': p.abstract, 'authors': p.authors,
                    'year': p.year, 'source': src_name, 'paper_url': p.paper_url, 'pdf_url': p.pdf_url,
                    'keyword_text': kw_text
                }

        return jsonify({'papers': list(papers_dict.values())})

@history_bp.route('/api/history/all', methods=['GET'])
def get_all_history():
    """Mengambil seluruh paper tersimpan dari 5 sumber API."""
    with SessionLocal() as db:
        models = [
            (SemanticScholarPaper, SessionSemanticScholarPaper, 'Semantic Scholar', 'ss'),
            (ArxivPaper, SessionArxivPaper, 'arXiv', 'ax'),
            (IeeePaper, SessionIeeePaper, 'IEEE Xplore', 'ie'),
            (PubmedPaper, SessionPubmedPaper, 'PubMed', 'pm'),
            (CrossrefPaper, SessionCrossrefPaper, 'Crossref', 'cr')
        ]

        papers = []
        for m_paper, m_rel, src_name, _ in models:
            results = db.query(m_paper, Keyword.keyword_text).outerjoin(
                m_rel, m_paper.id == m_rel.paper_id
            ).outerjoin(
                ScrapingSession, m_rel.session_id == ScrapingSession.id
            ).outerjoin(
                Keyword, ScrapingSession.keyword_id == Keyword.id
            ).all()
            for p, kw_text in results:
                papers.append({
                    'title': p.title, 'abstract': p.abstract, 'authors': p.authors,
                    'year': p.year, 'source': src_name, 'paper_url': p.paper_url, 'pdf_url': p.pdf_url,
                    'keyword_text': kw_text or 'teknologi'
                })

        return jsonify({'papers': papers})