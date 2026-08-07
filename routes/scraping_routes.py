from flask import Blueprint, request, jsonify
from models.models import (
    SessionLocal, ScrapingSession, Keyword, 
    SemanticScholarPaper, ArxivPaper, IeeePaper, PubmedPaper, CrossrefPaper,
    SessionSemanticScholarPaper, SessionArxivPaper, SessionIeeePaper, SessionPubmedPaper, SessionCrossrefPaper
)
from services.orchestrator import start_scraping_background

scraping_bp = Blueprint('scraping_bp', __name__)

@scraping_bp.route('/api/scrape', methods=['POST'])
def start_scrape():
    """Endpoint untuk memulai sesi scraping baru."""
    data = request.json
    keyword_text = data.get('keyword', '').strip()
    
    requested_amount = int(data.get('amount', 10))
    source_option = data.get('source', 'all')

    if not keyword_text:
        return jsonify({'error': 'Keyword tidak boleh kosong'}), 400

    try:
        with SessionLocal() as db:
            keyword_norm = keyword_text.lower()
            keyword_obj = db.query(Keyword).filter_by(keyword_normalized=keyword_norm).first()
            if not keyword_obj:
                keyword_obj = Keyword(keyword_text=keyword_text, keyword_normalized=keyword_norm)
                db.add(keyword_obj)
                db.commit()

            session_obj = ScrapingSession(
                keyword_id=keyword_obj.id,
                requested_amount=requested_amount,
                source_option=source_option
            )
            db.add(session_obj)
            db.commit()
            session_id = session_obj.id

        start_scraping_background(session_id, keyword_text, requested_amount, source_option)
        return jsonify({'session_id': session_id, 'message': 'Scraping sedang berjalan di background...'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@scraping_bp.route('/api/scrape/status/<int:session_id>', methods=['GET'])
def scrape_status(session_id):
    """Endpoint untuk frontend mengecek progress scraping."""
    with SessionLocal() as db:
        session_obj = db.query(ScrapingSession).get(session_id)
        if not session_obj:
            return jsonify({'error': 'Sesi tidak ditemukan'}), 404

        return jsonify({
            'status': session_obj.status,
            'total_found': session_obj.total_found,
            'new_papers_count': session_obj.new_papers_count,
            'duplicate_skipped_count': session_obj.duplicate_skipped_count,
            'invalid_skipped_count': session_obj.invalid_skipped_count,
            'requested_amount': session_obj.requested_amount
        })


@scraping_bp.route('/api/scrape/result/<int:session_id>', methods=['GET'])
def scrape_result(session_id):
    """Endpoint untuk mengambil hasil paper dari satu sesi (5 sumber API)."""
    with SessionLocal() as db:
        session_obj = db.query(ScrapingSession).get(session_id)
        kw_text = session_obj.keyword.keyword_text if (session_obj and session_obj.keyword) else 'teknologi'

        queries = [
            (SemanticScholarPaper, SessionSemanticScholarPaper, 'Semantic Scholar'),
            (ArxivPaper, SessionArxivPaper, 'arXiv'),
            (IeeePaper, SessionIeeePaper, 'IEEE Xplore'),
            (PubmedPaper, SessionPubmedPaper, 'PubMed'),
            (CrossrefPaper, SessionCrossrefPaper, 'Crossref')
        ]

        papers = []
        for model_paper, model_rel, source_name in queries:
            results = db.query(model_paper).join(
                model_rel, model_paper.id == model_rel.paper_id
            ).filter(
                model_rel.session_id == session_id,
                model_rel.is_duplicate.is_(False)
            ).all()

            for p in results:
                papers.append({
                    'id': p.id, 'title': p.title, 'abstract': p.abstract, 'authors': p.authors,
                    'year': p.year, 'source': source_name, 'paper_url': p.paper_url, 'pdf_url': p.pdf_url,
                    'keyword_text': kw_text
                })

        return jsonify({'papers': papers})