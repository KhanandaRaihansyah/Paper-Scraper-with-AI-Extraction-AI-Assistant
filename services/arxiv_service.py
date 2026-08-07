import urllib.request
import urllib.parse
import feedparser

# Tambahkan parameter start
def fetch_arxiv(keyword, start=0, max_results=100):
    query = urllib.parse.quote(f"all:{keyword}")
    # Masukkan variabel start ke dalam URL
    url = f"http://export.arxiv.org/api/query?search_query={query}&start={start}&max_results={max_results}"
    
    try:
        response = urllib.request.urlopen(url, timeout=10)
        feed_data = response.read()
        feed = feedparser.parse(feed_data)
    except Exception:
        return []
        
    papers = []
    for entry in feed.entries:
        authors = ", ".join([author.name for author in entry.authors]) if hasattr(entry, 'authors') else ""
        
        year = None
        if hasattr(entry, 'published'):
            try:
                year = int(entry.published[:4])
            except ValueError:
                pass
        
        pdf_url = None
        for link in entry.links:
            if link.type == 'application/pdf':
                pdf_url = link.href
                break
                
        title = entry.title.replace('\n', ' ') if entry.title else ""
        abstract = entry.summary.replace('\n', ' ') if entry.summary else ""
                
        paper_data = {
            'title': title,
            'abstract': abstract,
            'authors': authors,
            'year': year,
            'external_id': entry.id.split('/abs/')[-1] if '/abs/' in entry.id else entry.id,
            'paper_url': entry.id,
            'pdf_url': pdf_url,
            'source': 'arxiv'
        }
        papers.append(paper_data)
        
    return papers