import requests
import re

def fetch_pubmed(keyword, offset=0, limit=30):
    """
    Menarik data paper medis, healthcare & biomedical IoT dari PubMed / Europe PMC API.
    API ini gratis dan tidak memerlukan API key.
    """
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    params = {
        "query": keyword,
        "format": "json",
        "pageSize": limit,
        "resultType": "core",
        "synonym": "true"
    }

    # Europe PMC tidak menggunakan offset numerik murni, tetapi kita bisa menggunakan page
    page = (offset // limit) + 1
    params["page"] = page

    headers = {"User-Agent": "PaperScraper/1.0 (mailto:academic-research@university.edu)"}

    papers = []
    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        if res.status_code != 200:
            return []

        data = res.json()
        results = data.get("resultList", {}).get("result", [])

        for item in results:
            title = item.get("title", "").rstrip(".")
            if not title:
                continue

            authors = item.get("authorString", "Biomedical Researcher")
            abstract = item.get("abstractText", "") or f"Publikasi PubMed mengenai {title}."
            abstract = re.sub(r'<[^>]+>', '', abstract).strip()

            year = item.get("pubYear")
            try:
                year = int(year) if year else None
            except (ValueError, TypeError):
                year = None

            pmcid = item.get("pmcid")
            doi = item.get("doi")
            pmid = item.get("id")

            paper_url = f"https://europepmc.org/article/MED/{pmid}" if pmid else (f"https://doi.org/{doi}" if doi else "")

            # Cari Open Access PDF URL
            pdf_url = None
            for ft in item.get("fullTextUrlList", {}).get("fullTextUrl", []):
                if ft.get("documentStyle") == "pdf":
                    pdf_url = ft.get("url")
                    break
            if not pdf_url and pmcid:
                pdf_url = f"https://europepmc.org/backend/ptpmcrender.fcgi?accid={pmcid}&blobtype=pdf"

            papers.append({
                'title': title,
                'abstract': abstract,
                'authors': authors,
                'year': year,
                'external_id': pmid or doi or title[:30],
                'paper_url': paper_url,
                'pdf_url': pdf_url,
                'source': 'pubmed'
            })
    except Exception as e:
        print(f"❌ Europe PMC / PubMed API Error: {e}")

    return papers
