def is_valid_paper(paper_data):
    # 1. Cek ketersediaan 5 field wajib
    required_fields = ['title', 'abstract', 'authors', 'year', 'paper_url']
    for field in required_fields:
        if not paper_data.get(field):
            return False
    
    # 2. Cek tahun publikasi (>= 2020)
    try:
        year = int(paper_data['year'])
        if year < 2020:
            return False
    except (ValueError, TypeError):
        return False
        
    return True