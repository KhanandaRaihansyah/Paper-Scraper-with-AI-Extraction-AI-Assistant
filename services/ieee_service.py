import os
import requests
from dotenv import load_dotenv

load_dotenv()

def fetch_ieee(keyword, offset=0, limit=30):
    """
    Menarik data paper dari IEEE Xplore.
    Jika IEEE_API_KEY disetel, gunakan API resmi IEEE.
    Jika tidak ada API key, gunakan Crossref API dengan filter publisher 'IEEE' sebagai fallback gratis.
    """
    api_key = os.getenv("IEEE_API_KEY")
    papers = []

    if api_key:
        url = "https://ieeexploreapi.ieee.org/api/v1/search/articles"
        params = {
            "querytext": keyword,
            "format": "json",
            "max_records": limit,
            "start_record": offset + 1,
            "api_key": api_key
        }
        try:
            res = requests.get(url, params=params, timeout=10)
            if res.status_code == 200:
                data = res.json()
                for item in data.get("articles", []):
                    authors_list = [f"{a.get('first_name', '')} {a.get('last_name', '')}".strip() for a in item.get("authors", {}).get("author", [])]
                    authors = ", ".join(authors_list)
                    title = item.get("title", "")
                    abstract = item.get("abstract", "")
                    year = item.get("publication_year")
                    try:
                        year = int(year) if year else None
                    except (ValueError, TypeError):
                        year = None

                    paper_url = item.get("html_url") or item.get("pdf_url") or ""
                    pdf_url = item.get("pdf_url") if item.get("open_access") else None

                    papers.append({
                        'title': title,
                        'abstract': abstract or f"Paper IEEE: {title}",
                        'authors': authors or "IEEE Author",
                        'year': year,
                        'external_id': str(item.get("article_number", "")),
                        'paper_url': paper_url,
                        'pdf_url': pdf_url,
                        'source': 'ieee'
                    })
                return papers
        except Exception as e:
            print(f"⚠️ IEEE Official API Error: {e}, mencoba fallback Crossref-IEEE...")

    # Fallback Gratis via Crossref dengan publisher IEEE
    try:
        url = "https://api.crossref.org/works"
        headers = {"User-Agent": "PaperScraper/1.0 (mailto:academic-research@university.edu)"}
        params = {
            "query": keyword,
            "filter": "publisher-name:IEEE",
            "rows": limit,
            "offset": offset
        }
        res = requests.get(url, headers=headers, params=params, timeout=10)
        if res.status_code == 200:
            data = res.json()
            items = data.get("message", {}).get("items", [])
            for item in items:
                title_list = item.get("title", [])
                title = title_list[0] if title_list else ""
                if not title: continue

                # Authors
                author_names = []
                for a in item.get("author", []):
                    name = f"{a.get('given', '')} {a.get('family', '')}".strip()
                    if name: author_names.append(name)
                authors = ", ".join(author_names) or "IEEE Researcher"

                # Year
                published = item.get("published-print") or item.get("published-online") or item.get("created")
                year = None
                if published and "date-parts" in published:
                    try:
                        year = int(published["date-parts"][0][0])
                    except Exception:
                        pass

                abstract = item.get("abstract", "") or f"Artikel riset IEEE mengenai {title}."
                # Clean HTML tags from abstract if any
                import re
                abstract = re.sub(r'<[^>]+>', '', abstract).strip()

                doi = item.get("DOI", "")
                paper_url = item.get("URL") or (f"https://doi.org/{doi}" if doi else "")

                # PDF link if open access
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
                    'source': 'crossref_ieee'  # Ditandai berbeda dari IEEE resmi
                })
    except Exception as e:
        print(f"❌ Fallback IEEE Error: {e}")

    return papers
