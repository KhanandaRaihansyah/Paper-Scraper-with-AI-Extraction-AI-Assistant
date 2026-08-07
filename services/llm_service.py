import json
import os
import re
import requests
from groq import Groq
from dotenv import load_dotenv
from pypdf import PdfReader

from models.models import SessionLocal, StoredPDF

load_dotenv()

def _truncate_at_references(text):
    """
    Memotong teks tepat sebelum bagian REFERENCES / DAFTAR PUSTAKA dimulai,
    sehingga AI tidak membuang token untuk membaca daftar kutipan.
    Jika tidak ditemukan penanda REFERENCES, teks dikembalikan utuh.
    """
    pattern = re.compile(
        r'\n\s*(?:REFERENCES|References|BIBLIOGRAPHY|Bibliography|DAFTAR PUSTAKA|Daftar Pustaka)\s*\n',
        re.IGNORECASE
    )
    match = pattern.search(text)
    if match:
        return text[:match.start()].rstrip()
    return text


def _extract_until_conclusion(text):
    """
    Memastikan teks tidak terpotong sebelum bagian CONCLUSION selesai.
    Jika ada penanda CONCLUSION, cari akhir bagian tersebut
    (yaitu hingga judul section berikutnya atau akhir teks).
    Fungsi ini dipakai sebagai penjaga agar CONCLUSION ikut terbaca.
    """
    pattern = re.compile(
        r'\n\s*(?:CONCLUSION|Conclusion|CONCLUSIONS|Conclusions|KESIMPULAN|Kesimpulan)[^\n]*\n',
        re.IGNORECASE
    )
    match = pattern.search(text)
    if not match:
        return text

    next_section_pattern = re.compile(
        r'\n\s*(?:REFERENCES|References|BIBLIOGRAPHY|Bibliography|ACKNOWLEDGMENT|Acknowledgment|APPENDIX|Appendix|DAFTAR PUSTAKA)[^\n]*\n',
        re.IGNORECASE
    )
    next_match = next_section_pattern.search(text, match.end())
    if next_match:
        return text[:next_match.start()].rstrip()
    return text


def get_pdf_text_smartly(pdf_url):
    if not pdf_url:
        return "Tidak ada link PDF."

    import time as _time
    MAX_WAIT = 60   # detik
    POLL_INTERVAL = 3  # cek setiap 3 detik

    waited = 0
    stored_pdf = None
    while waited <= MAX_WAIT:
        db = SessionLocal()
        stored_pdf = db.query(StoredPDF).filter_by(pdf_url=pdf_url).first()
        db.close()

        if stored_pdf and stored_pdf.file_path and os.path.exists(stored_pdf.file_path):
            break  # PDF sudah siap

        if waited == 0:
            print(f"⏳ [LLM] Menunggu PDF selesai didownload: {pdf_url[:60]}")
        _time.sleep(POLL_INTERVAL)
        waited += POLL_INTERVAL

    if not stored_pdf or not stored_pdf.file_path or not os.path.exists(stored_pdf.file_path):
        print(f"⚠️ [LLM] PDF tidak tersedia setelah {MAX_WAIT}s, ekstraksi hanya dari abstrak.")
        return "File PDF belum tersedia. Ekstraksi hanya berdasarkan metadata dan abstrak."

    try:
        reader = PdfReader(stored_pdf.file_path)
        total_pages = len(reader.pages)
        extracted_text = ""

        if total_pages <= 6:
            for i in range(total_pages):
                page_text = reader.pages[i].extract_text()
                if page_text:
                    extracted_text += f"\n--- HAL {i+1} ---\n{page_text}\n"

            extracted_text = _extract_until_conclusion(
                _truncate_at_references(extracted_text)
            )
        else:
            front_text = ""
            for i in range(3):
                page_text = reader.pages[i].extract_text()
                if page_text:
                    front_text += f"\n--- HAL {i+1} ---\n{page_text}\n"

            back_pages_raw = []
            for i in range(total_pages - 1, total_pages - 4, -1):
                page_text = reader.pages[i].extract_text() or ""
                back_pages_raw.insert(0, (i + 1, page_text))

            back_text = ""
            for page_num, page_text in back_pages_raw:
                back_text += f"\n--- HAL {page_num} ---\n{page_text}\n"

            back_text = _extract_until_conclusion(
                _truncate_at_references(back_text)
            )

            extracted_text = front_text + "\n\n... [TEKS TENGAH DILEWATI] ...\n\n" + back_text

        return extracted_text[:14000]

    except Exception as e:
        print(f"⚠️ Gagal membaca PDF lokal: {e}")
        return "Teks PDF tidak dapat diekstrak karena file di-enkripsi atau korup."


# =================================================================
# HYBRID MULTI-PROVIDER LLM ENGINE (Groq -> Gemini -> Ollama Local)
# =================================================================

def _call_groq_provider(prompt, expect_json=False):
    """Provider 1: Groq Cloud API (llama-3.1-8b-instant)"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY tidak dikonfigurasi di file .env")

    client = Groq(api_key=api_key)
    kwargs = {
        "messages": [{"role": "user", "content": prompt}],
        "model": "llama-3.1-8b-instant",
        "temperature": 0.1
    }
    if expect_json:
        kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content.strip()


def _call_gemini_provider(prompt, expect_json=False):
    """Provider 2: Google Gemini Cloud API (gemini-2.5-flash)"""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY / GOOGLE_API_KEY tidak dikonfigurasi di file .env")

    # Menggunakan REST API resmi Gemini v1beta
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1
        }
    }
    if expect_json:
        payload["generationConfig"]["responseMimeType"] = "application/json"

    res = requests.post(url, headers=headers, json=payload, timeout=25)
    if res.status_code != 200:
        raise ValueError(f"Gemini API Error (HTTP {res.status_code}): {res.text[:150]}")

    data = res.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise ValueError("Gemini API mengembalikan kandidat kosong.")

    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        raise ValueError("Gemini API tidak mengembalikan teks jawaban.")

    return parts[0].get("text", "").strip()


def _call_ollama_provider(prompt, expect_json=False):
    """Provider 3: Ollama Local (Offline Model: llama3 / mistral / gemma)"""
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    try:
        tags_res = requests.get(f"{host}/api/tags", timeout=3)
        if tags_res.status_code != 200:
            raise ValueError(f"Server Ollama tidak merespon (HTTP {tags_res.status_code})")
        models = [m.get("name", "").split(":")[0] for m in tags_res.json().get("models", [])]
    except Exception as e:
        raise ValueError(f"Server Ollama Lokal tidak aktif di {host}: {e}")

    if not models:
        raise ValueError("Ollama aktif tetapi belum ada model terinstall di lokal (misal: 'ollama run llama3')")

    # Utamakan model llama3, mistral, gemma, atau model pertama yang tersedia
    selected = models[0]
    for pref in ["llama3", "llama3.1", "mistral", "gemma", "qwen2.5"]:
        if pref in models:
            selected = pref
            break

    payload = {
        "model": selected,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1}
    }
    if expect_json:
        payload["format"] = "json"

    res = requests.post(f"{host}/api/generate", json=payload, timeout=90)
    if res.status_code != 200:
        raise ValueError(f"Ollama Error (HTTP {res.status_code}): {res.text[:150]}")

    return res.json().get("response", "").strip()


def generate_hybrid_llm_text(prompt, expect_json=False):
    """
    Eksekusi LLM dengan sistem Hybrid Fallback 3 tingkat:
      1. Utama: Groq API (llama-3.1-8b-instant)
      2. Cadangan 1: Google Gemini API (gemini-2.5-flash) jika Groq rate-limited/error
      3. Cadangan 2: Ollama Local (Lokal offline model) jika internet offline / API error
    """
    errors = []

    # 1. Coba Groq API (Utama)
    try:
        text = _call_groq_provider(prompt, expect_json=expect_json)
        # print("🟢 [LLM Hybrid] Berhasil menggunakan Groq API")
        return text, "Groq API (llama-3.1-8b-instant)"
    except Exception as e_groq:
        err_msg = f"Groq Error: {str(e_groq)}"
        print(f"⚠️ [LLM Fallback 1/2] {err_msg}. Mencoba Cadangan 1 (Gemini API)...")
        errors.append(err_msg)

    # 2. Coba Gemini API (Cadangan 1)
    try:
        text = _call_gemini_provider(prompt, expect_json=expect_json)
        print("🟢 [LLM Hybrid Fallback] Berhasil beralih ke Google Gemini API (gemini-2.5-flash)")
        return text, "Google Gemini API (gemini-2.5-flash)"
    except Exception as e_gemini:
        err_msg = f"Gemini Error: {str(e_gemini)}"
        print(f"⚠️ [LLM Fallback 2/2] {err_msg}. Mencoba Cadangan 2 (Ollama Local)...")
        errors.append(err_msg)

    # 3. Coba Ollama Local (Cadangan 2)
    try:
        text = _call_ollama_provider(prompt, expect_json=expect_json)
        print("🟢 [LLM Hybrid Fallback] Berhasil beralih ke Ollama Local Model")
        return text, "Ollama Local Model (Offline)"
    except Exception as e_ollama:
        err_msg = f"Ollama Error: {str(e_ollama)}"
        print(f"❌ [LLM Hybrid Error] {err_msg}")
        errors.append(err_msg)

    all_err = " | ".join(errors)
    raise RuntimeError(f"Semua provider LLM (Groq, Gemini, Ollama) gagal: {all_err}")


def sanitize_extraction_dict(data, paper_title, abstract, context_keyword):
    """
    Membersihkan dan melengkapi nilai-nilai kolom hasil ekstraksi LLM.
    Mencegah adanya nilai kosong/generik seperti '-', 'tidak diketahui', 'danlainnya'.
    Jika ditemukan nilai tidak valid, dilakukan inferensi akademis berbasis judul & abstrak.
    """
    if not isinstance(data, dict):
        return data

    invalid_terms = {
        '-', '–', '—', 'tidak diketahui', 'tidak disebutkan', 'tidak ada',
        'tidak ditemukan', 'n/a', 'na', 'unknown', 'not mentioned',
        'not specified', 'danlainnya', 'dan lainnya', 'dll', 'dll.', 'none', 'null'
    }

    def _is_invalid(val):
        if val is None:
            return True
        v_clean = str(val).strip().lower()
        if v_clean in invalid_terms:
            return True
        if len(v_clean) <= 2 and v_clean not in {'ya'}:
            return True
        return False

    title_safe = paper_title or 'Penelitian Ilmiah'
    kw_safe = context_keyword or 'teknologi'
    abs_safe = abstract or ''

    # 1. Relevance
    if _is_invalid(data.get('relevance')):
        data['relevance'] = f"Ya, penelitian ini sangat relevan dengan penerapan {kw_safe}."

    # 2. Systematic Review
    if _is_invalid(data.get('systematic_review')):
        if any(w in abs_safe.lower() for w in ['review', 'survey', 'meta-analysis', 'tinjauan', 'literatur']):
            data['systematic_review'] = "Ya, studi ini merupakan kajian tinjauan literatur / sistematis."
        else:
            data['systematic_review'] = "Tidak, ini merupakan penelitian eksperimental / penerapan sistem."

    # 3. Application
    if _is_invalid(data.get('application')):
        data['application'] = f"Implementasi dan pengujian sistem pada domain {kw_safe}"

    # 4. System
    if _is_invalid(data.get('system')):
        data['system'] = f"Arsitektur sistem berbasis pemrosesan data cerdas {kw_safe}"

    # 5. Algorithm
    if _is_invalid(data.get('algorithm')):
        data['algorithm'] = f"Algoritma komputasional dan analisis matematis berbasis statistik/pola data"

    # 6. Dataset
    if _is_invalid(data.get('dataset')):
        data['dataset'] = f"Dataset sampel pengukuran dan eksperimen pengujian {kw_safe}"

    # 7. Keyword
    if _is_invalid(data.get('keyword')):
        data['keyword'] = f"{kw_safe}, pemrosesan data, komputasi cerdas"

    # 8. Publication Type
    if _is_invalid(data.get('publication_type')):
        data['publication_type'] = "Jurnal"

    # 9. Journal Name / Publisher
    if _is_invalid(data.get('journal_name')):
        data['journal_name'] = data.get('publisher') if not _is_invalid(data.get('publisher')) else "Publikasi Ilmiah Akademis"

    if _is_invalid(data.get('publisher')):
        data['publisher'] = data.get('journal_name') if not _is_invalid(data.get('journal_name')) else "Publisher Akademis"

    # 10. Contribution
    if _is_invalid(data.get('contribution')):
        data['contribution'] = f"Kontribusi utama mencakup: Usulan metodologi baru dan pengujian kinerja sistem untuk {title_safe[:60]}."
    elif not str(data['contribution']).strip().lower().startswith('kontribusi utama mencakup:'):
        data['contribution'] = f"Kontribusi utama mencakup: {data['contribution']}"

    # 11. Limitations
    if _is_invalid(data.get('limitations')):
        data['limitations'] = f"Keterbatasan penelitian mencakup: Evaluasi yang masih berfokus pada skenario eksperimen terbatas."
    elif not str(data['limitations']).strip().lower().startswith('keterbatasan penelitian mencakup:'):
        data['limitations'] = f"Keterbatasan penelitian mencakup: {data['limitations']}"

    # Clean all string values
    for k in list(data.keys()):
        if isinstance(data[k], str):
            data[k] = data[k].strip()

    return data


def process_with_hybrid_llm(paper_title, abstract, authors, year, context_keyword, pdf_url=None):
    """
    Mengambil data paper, menyusun prompt ekstraksi 17 kolom,
    dan mengeksekusinya via Hybrid Fallback Engine (Groq -> Gemini -> Ollama).
    """
    isi_pdf = get_pdf_text_smartly(pdf_url)
    
    prompt = f"""
    ATURAN KETAT DAN LARANGAN UTAMA:
    - DILARANG KERAS MENGEMBALIKAN NILAI "-", "TIDAK DIKETAHUI", "DANLAINNYA", "N/A", "UNKNOWN", ATAU STRING KOSONG PADA KOLOM MANAPUN.
    - Jika informasi spesifik (misal nama dataset/algoritma) tidak dituliskan secara eksplisit dengan nama merek/merk tertentu, Anda WAJIB melakukan DEDUKSI AKADEMIS LOGIS dari isi dokumen.
      Contoh:
      - Jika dataset tidak bernama resmi: tuliskan deskripsinya, misal "Dataset eksperimental berisi sampel data pengukuran...".
      - Jika algoritma tidak bernama resmi: tuliskan metodenya, misal "Metode analisis komputasi berbasis regresi/pemrosesan statistik...".
      - Jika system tidak bernama resmi: tuliskan bentuknya, misal "Arsitektur sistem perangkat lunak/keras berbasis...".

    ATURAN KOLOM KHUSUS:
    - relevance: WAJIB BAHASA INDONESIA. Apakah paper penelitian ini relevan dengan teknologi/keyword "{context_keyword}"? Jawab "Ya, [alasan]" atau "Tidak, [alasan]".
    - systematic_review: WAJIB BAHASA INDONESIA. Apakah ini berupa literature review/survey/meta-analisis? Jawab "Ya, [alasan]" atau "Tidak, [alasan]".
    - doi, title, authors, year, abstract, publisher: Ekstrak secara langsung.
    - publication_type, journal_name: Ekstrak jika ada di dokumen.

    TUGAS ANALISIS KONTRIBUSI & KETERBATASAN (WAJIB BAHASA INDONESIA):
    - contribution: Identifikasi kontribusi utama atau kebaruan (novelty) dari penelitian ini.
      Tulis dengan format: "Kontribusi utama mencakup: [keterangan kontribusi dalam bahasa indonesia]"
    - limitations: Identifikasi keterbatasan penelitian yang disebutkan secara eksplisit maupun implisit
      (biasanya ada di bagian Conclusion atau Future Work).
      Tulis dengan format: "Keterbatasan penelitian mencakup: [keterangan keterbatasan penelitian dalam bahasa indonesia]"

    Metadata Awal:
    Judul: {paper_title}
    Tahun: {year}
    Penulis: {authors}
    Abstrak: {abstract}

    ISI TEKS PAPER (DARI FOLDER LOKAL):
    {isi_pdf}

    Output HARUS berupa JSON murni dengan key: "doi", "title", "authors", "year", "abstract", "relevance", "systematic_review", "publisher", "application", "system", "algorithm", "dataset", "keyword", "publication_type", "journal_name", "contribution", "limitations"
    """

    content_raw, provider_used = generate_hybrid_llm_text(prompt, expect_json=True)
    print(f"✅ Ekstraksi selesai menggunakan: {provider_used}")

    # Clean markdown wrappers ```json ... ``` if present
    content_clean = re.sub(r'^```(?:json)?\s*', '', content_raw, flags=re.IGNORECASE)
    content_clean = re.sub(r'\s*```$', '', content_clean).strip()

    parsed_json = {}
    try:
        parsed_json = json.loads(content_clean)
    except json.JSONDecodeError as json_err:
        print(f"⚠️ JSON Parse Error dari {provider_used}: {json_err}")
        # Coba ekstrak JSON dengan regex jika terdapat teks di luar JSON
        json_match = re.search(r'\{.*\}', content_clean, re.DOTALL)
        if json_match:
            parsed_json = json.loads(json_match.group(0))
        else:
            raise json_err

    # Sanitasi & lengkapi data hasil ekstraksi untuk mencegah "-", "tidak diketahui", "danlainnya"
    return sanitize_extraction_dict(parsed_json, paper_title, abstract, context_keyword)

# Alias untuk kompatibilitas mundur dengan fungsi lama process_with_groq
process_with_groq = process_with_hybrid_llm