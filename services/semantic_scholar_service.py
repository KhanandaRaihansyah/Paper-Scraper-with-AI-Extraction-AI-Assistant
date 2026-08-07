import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('SEMANTIC_SCHOLAR_API_KEY')

# Tambahkan parameter offset
def fetch_semantic_scholar(keyword, limit=100, offset=0):
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    headers = {}
    if API_KEY:
        headers['x-api-key'] = API_KEY

    params = {
        'query': keyword,
        'limit': limit,
        'offset': offset, # Parameter baru disisipkan ke API
        'fields': 'title,abstract,authors,year,url,openAccessPdf,externalIds'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code != 200:
            return []
    except requests.RequestException:
        return []
        
    data = response.json()
    papers = []
    
    for item in data.get('data', []):
        authors = ", ".join([a.get('name') for a in item.get('authors', [])]) if item.get('authors') else ""
        pdf_url = item['openAccessPdf'].get('url') if item.get('openAccessPdf') else None
            
        paper_data = {
            'title': item.get('title'),
            'abstract': item.get('abstract'),
            'authors': authors,
            'year': item.get('year'),
            'external_id': item.get('externalIds', {}).get('CorpusId'),
            'paper_url': item.get('url'),
            'pdf_url': pdf_url,
            'source': 'semantic_scholar'
        }
        papers.append(paper_data)
        
    return papers