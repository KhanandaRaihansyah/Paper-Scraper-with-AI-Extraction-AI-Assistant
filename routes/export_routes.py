import os
import time
from flask import Blueprint, request, send_file, jsonify
from models.models import (
    SessionLocal, ScrapingSession,
    SemanticScholarPaper, ArxivPaper, IeeePaper, PubmedPaper, CrossrefPaper,
    SessionSemanticScholarPaper, SessionArxivPaper, SessionIeeePaper, SessionPubmedPaper, SessionCrossrefPaper
)
from services.export_service import export_to_csv, export_to_excel
from services.pdf_service import download_pdf, create_zip_from_paths

export_bp = Blueprint('export_bp', __name__)

def get_papers_for_export(req, db):
    """Fungsi pembantu untuk mengambil data paper berdasarkan parameter filter (5 sumber API)."""
    session_id = req.args.get('session_id')
    keyword_id = req.args.get('keyword_id')
    
    models = [
        (SemanticScholarPaper, SessionSemanticScholarPaper, 'Semantic Scholar', 'ss'),
        (ArxivPaper, SessionArxivPaper, 'arXiv', 'ax'),
        (IeeePaper, SessionIeeePaper, 'IEEE Xplore', 'ie'),
        (PubmedPaper, SessionPubmedPaper, 'PubMed', 'pm'),
        (CrossrefPaper, SessionCrossrefPaper, 'Crossref', 'cr')
    ]

    papers_dict = {}

    if session_id:
        for m_paper, m_rel, src_name, prefix in models:
            results = db.query(m_paper).join(m_rel).filter(
                m_rel.session_id == session_id,
                m_rel.is_duplicate.is_(False)
            ).all()
            for p in results:
                papers_dict[f"{prefix}_{p.id}"] = {
                    'title': p.title, 'abstract': p.abstract, 'authors': p.authors,
                    'year': p.year, 'source': src_name, 'paper_url': p.paper_url, 'pdf_url': p.pdf_url
                }
    elif keyword_id:
        sessions = db.query(ScrapingSession.id).filter_by(keyword_id=keyword_id).all()
        session_ids = [s[0] for s in sessions]
        for m_paper, m_rel, src_name, prefix in models:
            results = db.query(m_paper).join(m_rel).filter(
                m_rel.session_id.in_(session_ids),
                m_rel.is_duplicate.is_(False)
            ).all()
            for p in results:
                papers_dict[f"{prefix}_{p.id}"] = {
                    'title': p.title, 'abstract': p.abstract, 'authors': p.authors,
                    'year': p.year, 'source': src_name, 'paper_url': p.paper_url, 'pdf_url': p.pdf_url
                }
    else:
        for m_paper, _, src_name, prefix in models:
            results = db.query(m_paper).all()
            for p in results:
                papers_dict[f"{prefix}_{p.id}"] = {
                    'title': p.title, 'abstract': p.abstract, 'authors': p.authors,
                    'year': p.year, 'source': src_name, 'paper_url': p.paper_url, 'pdf_url': p.pdf_url
                }

    return list(papers_dict.values())

@export_bp.route('/api/export/csv', methods=['GET'])
def export_csv():
    try:
        with SessionLocal() as db:
            papers = get_papers_for_export(request, db)
        if not papers: return jsonify({'error': 'Tidak ada data'}), 404

        os.makedirs('exports', exist_ok=True)
        filepath = os.path.join('exports', 'hasil_scraping.csv')
        export_to_csv(papers, filepath)
        return send_file(filepath, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_bp.route('/api/export/excel', methods=['GET'])
def export_excel():
    try:
        with SessionLocal() as db:
            papers = get_papers_for_export(request, db)
        if not papers: return jsonify({'error': 'Tidak ada data'}), 404

        os.makedirs('exports', exist_ok=True)
        filepath = os.path.join('exports', 'hasil_scraping.xlsx')
        export_to_excel(papers, filepath)
        return send_file(filepath, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_bp.route('/api/export/pdf-zip', methods=['GET'])
def export_pdf_zip():
    try:
        with SessionLocal() as db:
            papers = get_papers_for_export(request, db)
        if not papers: return jsonify({'error': 'Tidak ada data'}), 404

        os.makedirs('downloads/pdf', exist_ok=True)
        os.makedirs('exports', exist_ok=True)

        downloaded_paths = []
        for idx, p in enumerate(papers):
            if p['pdf_url']:
                safe_title = "".join([c for c in p['title'] if c.isalnum() or c==' ']).rstrip()[:60]
                pdf_path = os.path.join('downloads/pdf', f"{safe_title}.pdf")

                if os.path.exists(pdf_path):
                    downloaded_paths.append(pdf_path)
                else:
                    if idx > 0:
                        time.sleep(2)
                    if download_pdf(p['pdf_url'], pdf_path):
                        downloaded_paths.append(pdf_path)

        if not downloaded_paths:
            return jsonify({'error': 'Tidak ada PDF Open-Access yang berhasil diunduh'}), 404

        zip_path = os.path.join('exports', 'kumpulan_pdf.zip')
        create_zip_from_paths(downloaded_paths, zip_path)
        return send_file(zip_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500