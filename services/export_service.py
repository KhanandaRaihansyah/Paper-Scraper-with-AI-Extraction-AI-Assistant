import pandas as pd

def format_data_for_export(papers_data):
    """
    Menyiapkan dan merapikan nama kolom sebelum diekspor
    agar lebih ramah dibaca pengguna.
    """
    df = pd.DataFrame(papers_data)
    
    # Menghapus kolom internal/ID yang tidak perlu diekspor jika ada
    columns_to_drop = ['id', 'title_normalized', 'external_id', 'pdf_local_path', 'created_at']
    df = df.drop(columns=[col for col in columns_to_drop if col in df.columns], errors='ignore')
    
    # Mengubah nama kolom ke bahasa Indonesia yang rapi
    df.rename(columns={
        'title': 'Judul',
        'abstract': 'Abstrak',
        'authors': 'Penulis',
        'year': 'Tahun Publikasi',
        'source': 'Sumber (API)',
        'paper_url': 'Link Paper',
        'pdf_url': 'Link Download PDF',
        'pdf_downloaded': 'Status PDF Lokal'
    }, inplace=True, errors='ignore')
    
    return df

def export_to_csv(papers_data, file_path):
    """Mengekspor data ke format CSV."""
    if not papers_data:
        return False
        
    df = format_data_for_export(papers_data)
    df.to_csv(file_path, index=False, encoding='utf-8')
    return True

def export_to_excel(papers_data, file_path):
    """Mengekspor data ke format Excel menggunakan openpyxl."""
    if not papers_data:
        return False
        
    df = format_data_for_export(papers_data)
    # Gunakan engine openpyxl sesuai spesifikasi PRD
    df.to_excel(file_path, index=False, engine='openpyxl')
    return True