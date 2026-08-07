import os
import re
import math
from collections import Counter
from groq import Groq
from dotenv import load_dotenv
from models.models import SessionLocal, PaperExtraction

load_dotenv()

def _tokenize(text):
    """Tokenisasi sederhana dan normalisasi kata untuk BM25 / TF-IDF similarity."""
    if not text:
        return []
    text_clean = re.sub(r'[^\w\s]', ' ', str(text).lower())
    words = text_clean.split()
    # Hapus stop words umum
    stopwords = {
        'the', 'a', 'an', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are',
        'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'this', 'that', 'these', 'those',
        'yang', 'dan', 'di', 'ke', 'dari', 'pada', 'dengan', 'untuk', 'secara', 'atau', 'ini', 'itu',
        'adalah', 'sebagai', 'dalam', 'oleh', 'bisa', 'dapat', 'menggunakan', 'digunakan', 'pada'
    }
    return [w for w in words if w not in stopwords and len(w) > 2]

def _compute_paper_relevance(query_tokens, paper_text, idf_dict):
    """Menghitung skor relevansi TF-IDF / BM25 sederhana antara query dan teks paper."""
    paper_tokens = _tokenize(paper_text)
    if not paper_tokens or not query_tokens:
        return 0.0

    tf = Counter(paper_tokens)
    score = 0.0
    doc_len = len(paper_tokens)

    for q in query_tokens:
        if q in tf:
            # TF-IDF term score
            term_tf = tf[q] / doc_len
            term_idf = idf_dict.get(q, 1.0)
            score += term_tf * term_idf

    return score

def rank_papers_for_query(query, records, top_k=20):
    """
    Memilih top_k paper yang paling relevan dengan pertanyaan pengguna.
    Jika total paper <= top_k, sertakan semua paper.
    """
    if len(records) <= top_k:
        return records

    query_tokens = _tokenize(query)
    if not query_tokens:
        return records[:top_k]

    # 1. Hitung Document Frequency (DF) & Inverse Document Frequency (IDF)
    N = len(records)
    doc_freq = Counter()
    paper_corpus = []

    for r in records:
        full_text = f"{r.title or ''} {r.abstract or ''} {r.algorithm or ''} {r.system or ''} {r.dataset or ''} {r.application or ''} {r.contribution or ''} {r.limitations or ''} {r.keyword or ''}"
        paper_corpus.append(full_text)
        unique_tokens = set(_tokenize(full_text))
        for token in unique_tokens:
            doc_freq[token] += 1

    idf_dict = {t: math.log((N + 1) / (df + 1)) + 1.0 for t, df in doc_freq.items()}

    # 2. Hitung skor per paper
    scored_records = []
    for idx, r in enumerate(records):
        score = _compute_paper_relevance(query_tokens, paper_corpus[idx], idf_dict)
        scored_records.append((score, r))

    # Urutkan berdasarkan skor tertinggi
    scored_records.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored_records[:top_k]]

def answer_paper_chat(user_question, keyword=None):
    """
    Fungsi utama RAG:
    1. Mengambil hasil ekstraksi dari database (opsional filter per keyword).
    2. Meranking & memilih paper paling relevan (TF-IDF).
    3. Menyusun prompt akademis & memanggil Hybrid LLM (Groq → Gemini → Ollama).
    4. Mengembalikan jawaban terstruktur beserta sitasi paper.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {
            "error": "GROQ_API_KEY tidak ditemukan di file .env",
            "answer": "GROQ_API_KEY belum dikonfigurasi.",
            "cited_papers": []
        }

    # ── TAHAP 1: Ambil data dari DB, tutup session sesegera mungkin ──
    all_records = []
    with SessionLocal() as db:
        query = db.query(PaperExtraction).filter_by(extraction_status='success')
        all_records = query.all()
        # Paksa SQLAlchemy load semua atribut sekarang (expunge-safe access)
        for r in all_records:
            _ = (r.title, r.abstract, r.authors, r.year, r.journal_name,
                 r.publisher, r.source_type, r.publication_type, r.algorithm,
                 r.system, r.dataset, r.application, r.contribution,
                 r.limitations, r.keyword, r.search_keyword, r.paper_url)
    # Session sudah ditutup di sini — semua atribut sudah di-cache di memory

    if not all_records:
        return {
            "answer": "⚠️ **Belum ada paper yang diekstrak AI.**\n\nSilakan lakukan ekstraksi paper terlebih dahulu pada tab **Pencarian** atau **Riwayat**, atau jalankan fitur **✨ Hasil Ekstraksi AI** agar repositori pengetahuan siap digunakan.",
            "total_papers": 0,
            "cited_papers": []
        }

    # Filter per keyword jika ditentukan
    target_records = all_records
    if keyword and keyword != 'all':
        kw_lower = keyword.lower().strip()
        matched = [
            r for r in all_records
            if (r.search_keyword and r.search_keyword.lower().strip() == kw_lower) or
               (r.keyword and kw_lower in r.keyword.lower())
        ]
        if matched:
            target_records = matched

    # ── TAHAP 2: Ranking paper & format konteks ──
    try:
        total_extracted = len(target_records)
        selected_records = rank_papers_for_query(user_question, target_records, top_k=20)

        context_blocks = []
        cited_papers_info = []

        for idx, r in enumerate(selected_records, 1):
            cited_papers_info.append({
                "index": idx,
                "title": r.title,
                "year": r.year,
                "authors": r.authors,
                "paper_url": r.paper_url
            })

            block = f"""
--- [PAPER {idx}] ---
Judul: {r.title}
Penulis: {r.authors or '-'}
Tahun: {r.year or '-'}
Keyword Pencarian: {r.search_keyword or '-'}
Sumber/Jurnal: {r.journal_name or r.publisher or r.source_type or '-'}
Tipe Publikasi: {r.publication_type or '-'}
Algoritma / Metode: {r.algorithm or '-'}
Sistem / Arsitektur: {r.system or '-'}
Dataset / Sampel: {r.dataset or '-'}
Aplikasi: {r.application or '-'}
Kontribusi / Novelty: {r.contribution or '-'}
Keterbatasan (Limitations): {r.limitations or '-'}
Abstrak: {r.abstract or '-'}
"""
            context_blocks.append(block)

        full_context = "\n".join(context_blocks)
        kw_title_str = f' KATEGORI KEYWORD "{keyword}"' if (keyword and keyword != 'all') else ''

        # ── TAHAP 3: Panggil Hybrid LLM ──
        prompt = f"""
Anda adalah **Academic AI Research Assistant** (Asisten Peneliti Akademik Senior).
Tugas Anda adalah menjawab pertanyaan pengguna secara komprehensif, kritis, akurat, dan akademis berdasarkan **Repositori Pengetahuan Paper{kw_title_str}** yang diberikan di bawah ini.

REPOSITORI PENGETAHUAN ({len(selected_records)} paper terpilih dari total {total_extracted} paper terekstrak{kw_title_str}):
{full_context}

PERTANYAAN PENGGUNA:
"{user_question}"

INSTRUKSI JAWABAN (WAJIB DITUTUTI):
1. **Bahasa**: Gunakan Bahasa Indonesia akademis yang jelas, sistematis, dan profesional.
2. **Kebenaran Empiris**: Jawab HANYA berdasarkan informasi yang ada pada repositori di atas. Lakukan komparasi logis jika diminta membandingkan.
3. **Sitasi**: Setiap kali menyebutkan fakta, algoritma, dataset, kontribusi, atau keterbatasan, sebutkan sitasinya dengan format `[Judul Paper, Tahun]` atau `[Paper #N]`.
4. **Struktur Jawaban**:
   - Berikan **Ringkasan Eksekutif / Jawaban Utama** di awal.
   - Gunakan **Tabel Komparatif (Markdown Table)** jika pertanyaan meminta perbandingan atau pemetaan algoritma/dataset.
   - Gunakan **Poin-poin Berisi Detail & Analisis Kritis**.
   - Berikan **Kesimpulan & Rekomendasi Riset Lanjutan**.
5. Jika pertanyaan tidak dapat dijawab dari repositori yang ada, jelaskan secara sopan paper mana yang mendekati dan apa keterbatasan informasi yang ada.
"""

        from services.llm_service import generate_hybrid_llm_text
        answer_text, provider_used = generate_hybrid_llm_text(prompt, expect_json=False)

        return {
            "answer": answer_text,
            "total_extracted": total_extracted,
            "used_papers_count": len(selected_records),
            "cited_papers": cited_papers_info,
            "provider_used": provider_used
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "answer": f"❌ **Terjadi kesalahan saat memproses jawaban AI:** {str(e)}",
            "cited_papers": []
        }
