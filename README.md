# Paper-Scraper-with-AI-Extraction-AI-Assistant
Paper Scraper is a Python-based web application designed to streamline academic literature collection. Powered by Semantic Scholar and arXiv APIs, it automatically extracts paper metadata, enforces strict data validation and deduplication, filters publications from 2020 onwards, and provides seamless CSV/Excel exports alongside bulk PDF downloads packaged into a single ZIP file.

General Overview:

<img width="1102" height="944" alt="image" src="https://github.com/user-attachments/assets/bf7d26a8-fcfa-48ed-9e9e-3168b5d6bff0" />
This screenshot displays the main interface of the Paper Scraper web application, specifically showing the Search (Pencarian) tab. The tool is designed to search, scrape, and aggregate academic research papers automatically from multiple scholarly databases via their respective APIs.
UI Component Breakdown:

1. Main Navigation Tabs (Top Bar):- Pencarian / Search (Active): The configuration form used to initiate a new paper scraping task.
- Riwayat per Keyword (History by Keyword): Displays past search records filtered by specific keywords.
- Riwayat Semua (All History): Displays the complete log of all past search queries.
- Hasil Ekstraksi AI (AI Extraction Results): Shows key data points and information extracted from scraped papers using AI models.
- Ask AI Assistant (RAG): A Retrieval-Augmented Generation (RAG) powered conversational interface that allows users to ask questions directly about the contents of the collected papers.
