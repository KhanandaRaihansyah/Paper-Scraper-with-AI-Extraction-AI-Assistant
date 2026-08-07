import requests
import re

def fetch_crossref(keyword, offset=0, limit=30):
    """
    Menarik data paper lintas-penerbit (Elsevier, Springer, Nature, Wiley, dll.) dari Crossref REST API.
    API ini gratis dan tidak memerlukan API key.
    """
    url = "https://api.crossref.org/works"
    headers = {"User-Agent": "PaperScraper/1.0 (mailto:academic-research@university.edu)"}
    params = {
        "query": keyword,
        "rows": limit,
        "offset": offset,
        "sort": "relevance"
    }

    papers = []
    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        if res.status_code != 200:
            return []

        data = res.json()
        items = data.get("message", {}).get("items", [])

        for item in items:
            title_list = item.get("title", [])
            title = title_list[0] if title_list else ""
            if not title:
                continue

            # Authors
            author_names = []
            for a in item.get("author", []):
                name = f"{a.get('given', '')} {a.get('family', '')}".strip()
                if name:
                    author_names.append(name)
            authors = ", ".join(author_names) or "Crossref Author"

            # Year
            published = item.get("published-print") or item.get("published-online") or item.get("created")
            year = None
            if published and "date-parts" in published:
                try:
                    year = int(published["date-parts"][0][0])
                except (ValueError, TypeError, IndexError):
                    year = None

            abstract = item.get("abstract", "") or f"Publikasi riset Crossref mengenai {title}."
            abstract = re.sub(r'<[^>]+>', '', abstract).strip()

            doi = item.get("DOI", "")
            paper_url = item.get("URL") or (f"https://doi.org/{doi}" if doi else "")

            # Open Access PDF link if available
            pdf_url = None
            for link in item.get("link", []):
                if link.get("content-type") == "application/pdf":
                    pdf_url = link.get("URL")
                    break

            papers.append({
                'title': title,
                'abstract': abstract,
                'authors': authors,
                'year': year,
                'external_id': doi or title[:30],
                'paper_url': paper_url,
                'pdf_url': pdf_url,
                'source': 'crossref'
            })
    except Exception as e:
        print(f"❌ Crossref API Error: {e}")

    return papers
