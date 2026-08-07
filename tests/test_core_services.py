"""
tests/test_core_services.py
===========================
Unit test untuk fungsi-fungsi core yang paling kritis:
  1. dedup_service.normalize_title  → 3 test
  2. dedup_service.is_duplicate     → 1 test (dengan DB in-memory)
  3. validation_service.is_valid_paper → 3 test (edge cases)

Jalankan: pytest tests/test_core_services.py -v
"""

import sys
import os

# Tambahkan root project ke sys.path agar import relatif bekerja
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# pyrefly: ignore [missing-import]
import pytest

# ─────────────────────────────────────────────────────────────
# TEST 1 — dedup_service.normalize_title
# ─────────────────────────────────────────────────────────────

from services.dedup_service import normalize_title

class TestNormalizeTitle:

    def test_huruf_kapital_dijadikan_lowercase(self):
        """Judul dengan HURUF BESAR harus menjadi lowercase."""
        result = normalize_title("Deep Learning For IoT Devices")
        assert result == "deep learning for iot devices"

    def test_tanda_baca_dihapus(self):
        """Tanda baca (titik, koma, titik dua, dll) harus dihapus."""
        result = normalize_title("A Survey: IoT, Security & Privacy")
        assert ":" not in result
        assert "," not in result
        assert "&" not in result

    def test_spasi_ganda_dinormalisasi(self):
        """Spasi berlebih (termasuk tab) harus dinormalisasi menjadi satu spasi."""
        result = normalize_title("  Machine   Learning  for   IoT  ")
        assert result == "machine learning for iot"

    def test_string_kosong_mengembalikan_string_kosong(self):
        """Input string kosong harus mengembalikan string kosong (bukan None/error)."""
        assert normalize_title("") == ""

    def test_none_mengembalikan_string_kosong(self):
        """Input None harus mengembalikan string kosong tanpa error."""
        assert normalize_title(None) == ""


# ─────────────────────────────────────────────────────────────
# TEST 2 — dedup_service.is_duplicate (dengan SQLite in-memory)
# ─────────────────────────────────────────────────────────────

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import Base, SemanticScholarPaper

@pytest.fixture
def db_session():
    """
    Buat database SQLite in-memory sementara untuk testing.
    Otomatis dibersihkan setelah tiap test.
    """
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


class TestIsDuplicate:

    def test_paper_baru_bukan_duplikat(self, db_session):
        """Judul yang belum ada di DB harus mengembalikan False."""
        from services.dedup_service import is_duplicate
        result = is_duplicate(db_session, "machine learning iot sensor")
        assert result is False

    def test_paper_yang_sudah_ada_adalah_duplikat(self, db_session):
        """Judul yang sudah ada di tabel SemanticScholarPaper harus mengembalikan True."""
        from services.dedup_service import is_duplicate

        # Masukkan 1 paper ke DB test
        paper = SemanticScholarPaper(
            title="Deep Learning for Smart Home",
            title_normalized="deep learning for smart home",
            abstract="A study on smart home automation.",
            authors="Doe, J.",
            year=2023,
            external_id="ss_test_001",
            paper_url="https://example.com/paper1"
        )
        db_session.add(paper)
        db_session.commit()

        # Cek paper yang sama → harus duplikat
        result = is_duplicate(db_session, "deep learning for smart home")
        assert result is True

    def test_title_normalized_kosong_bukan_duplikat(self, db_session):
        """Judul normalized kosong ('') harus mengembalikan False tanpa query ke DB."""
        from services.dedup_service import is_duplicate
        result = is_duplicate(db_session, "")
        assert result is False


# ─────────────────────────────────────────────────────────────
# TEST 3 — validation_service.is_valid_paper
# ─────────────────────────────────────────────────────────────

from services.validation_service import is_valid_paper

# Paper minimal yang valid (baseline untuk setiap test)
_VALID_PAPER = {
    'title': 'A Survey on IoT Security',
    'abstract': 'This paper surveys recent advances in IoT security.',
    'authors': 'Alice, Bob',
    'year': 2022,
    'paper_url': 'https://example.com/survey'
}


class TestIsValidPaper:

    def test_paper_lengkap_valid(self):
        """Paper dengan semua field wajib dan tahun >= 2020 harus valid."""
        assert is_valid_paper(_VALID_PAPER) is True

    def test_judul_kosong_tidak_valid(self):
        """Paper tanpa judul harus ditolak."""
        invalid = {**_VALID_PAPER, 'title': ''}
        assert is_valid_paper(invalid) is False

    def test_abstract_kosong_tidak_valid(self):
        """Paper tanpa abstrak harus ditolak."""
        invalid = {**_VALID_PAPER, 'abstract': None}
        assert is_valid_paper(invalid) is False

    def test_paper_url_kosong_tidak_valid(self):
        """Paper tanpa URL harus ditolak."""
        invalid = {**_VALID_PAPER, 'paper_url': None}
        assert is_valid_paper(invalid) is False

    def test_tahun_sebelum_2020_tidak_valid(self):
        """Paper dengan tahun 2019 atau lebih lama harus ditolak."""
        invalid = {**_VALID_PAPER, 'year': 2019}
        assert is_valid_paper(invalid) is False

    def test_tahun_tepat_2020_valid(self):
        """Paper dengan tahun tepat 2020 harus diterima (batas inklusif)."""
        valid = {**_VALID_PAPER, 'year': 2020}
        assert is_valid_paper(valid) is True

    def test_tahun_bukan_angka_tidak_valid(self):
        """Field year yang tidak bisa dikonversi ke int harus ditolak dengan graceful."""
        invalid = {**_VALID_PAPER, 'year': 'unknown'}
        assert is_valid_paper(invalid) is False
