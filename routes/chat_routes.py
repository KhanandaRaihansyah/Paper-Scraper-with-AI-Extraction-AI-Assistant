from flask import Blueprint, request, jsonify
from services.rag_service import answer_paper_chat
from models.models import SessionLocal, PaperExtraction

chat_bp = Blueprint('chat_bp', __name__)

@chat_bp.route('/api/chat/status', methods=['GET'])
def get_chat_status():
    """Mengembalikan status repositori pengetahuan beserta daftar keyword yang tersedia."""
    with SessionLocal() as db:
        extractions = db.query(PaperExtraction).filter_by(extraction_status='success').all()
        count = len(extractions)

        # Kelompokkan jumlah paper per keyword
        kw_counts = {}
        for item in extractions:
            kw = item.search_keyword or 'Umum'
            kw_counts[kw] = kw_counts.get(kw, 0) + 1

        keywords_list = [{'keyword': k, 'count': v} for k, v in kw_counts.items()]

        return jsonify({
            "total_extracted": count,
            "ready": count > 0,
            "keywords": keywords_list
        })

@chat_bp.route('/api/chat/ask', methods=['POST'])
def ask_chat():
    """Endpoint utama untuk mengajukan pertanyaan ke AI RAG Assistant."""
    data = request.json or {}
    question = data.get('question', '').strip()
    keyword = data.get('keyword', 'all')

    if not question:
        return jsonify({'error': 'Pertanyaan tidak boleh kosong'}), 400

    result = answer_paper_chat(question, keyword=keyword)
    return jsonify(result)
