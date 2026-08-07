let currentSessionId = null;
let currentKeywordId = null;
let pollInterval = null;
let extractedTitles = new Set(); // Ingatan global untuk mencegah duplikat
let allExtractionRecords = []; // Tempat menyimpan seluruh data ekstraksi untuk live filter

// ==========================================
// TOAST NOTIFICATION COMPONENT SYSTEM (UI/UX)
// ==========================================
function showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toastContainer');
    if (!container) {
        alert(message);
        return;
    }

    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };
    const titles = {
        success: 'Berhasil',
        error: 'Gagal / Error',
        warning: 'Peringatan',
        info: 'Informasi'
    };

    const icon = icons[type] || 'ℹ️';
    const title = titles[type] || 'Notifikasi';

    const toast = document.createElement('div');
    toast.className = `toast-item toast-${type}`;
    toast.innerHTML = `
        <div class="toast-icon">${icon}</div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div>${message}</div>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('toast-out');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ==========================================
// 1. FUNGSI NAVIGASI TAB UTAMA
// ==========================================
function switchTab(evt, tabId) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.add('hidden');
        tab.style.display = 'none'; 
    });
    
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    const targetTab = document.getElementById(tabId);
    if (targetTab) {
        targetTab.classList.remove('hidden');
        targetTab.style.display = 'block'; 
    }
    
    if (evt && evt.currentTarget) {
        evt.currentTarget.classList.add('active');
    }
}

// ==========================================
// 2. FUNGSI EXPORT & RENDER TABEL
// ==========================================
async function exportData(type, sessionId = null, keywordId = null) {
    let url = `/api/export/${type}?`;
    if (sessionId) url += `session_id=${sessionId}`;
    else if (keywordId) url += `keyword_id=${keywordId}`;

    if (type !== 'pdf-zip') {
        window.location.href = url;
        return;
    }

    const btn = event.target;
    const originalText = btn.innerText;
    
    btn.innerText = '⏳ Mengemas ZIP...';
    btn.disabled = true;
    showToast("Proses unduh PDF massal dimulai. Mohon jangan tutup halaman ini.", "info");

    try {
        const response = await fetch(url);
        if (!response.ok) {
            const errData = await response.json();
            alert("Gagal mengunduh: " + (errData.error || "Terjadi kesalahan server."));
            btn.innerText = originalText;
            btn.disabled = false;
            return;
        }

        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `kumpulan_pdf_scraper_${Date.now()}.zip`;
        document.body.appendChild(a);
        a.click();
        
        a.remove();
        window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
        alert("Terjadi kesalahan jaringan.");
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
}

function getSourceBadge(source) {
    const src = (source || '').toLowerCase();
    if (src.includes('semantic')) {
        return `<span class="badge ss">Semantic Scholar</span>`;
    } else if (src.includes('arxiv')) {
        return `<span class="badge ax">arXiv</span>`;
    } else if (src.includes('ieee')) {
        return `<span class="badge ie">IEEE Xplore</span>`;
    } else if (src.includes('pubmed')) {
        return `<span class="badge pm">PubMed</span>`;
    } else if (src.includes('crossref')) {
        return `<span class="badge cr">Crossref</span>`;
    }
    return `<span class="badge" style="background:#6b7280;">${source}</span>`;
}

function renderTable(tableId, papers) {
    const tbody = document.querySelector(`#${tableId} tbody`);
    if (!tbody) return;

    tbody.innerHTML = ''; 
    if (!papers || papers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">Tidak ada data paper.</td></tr>';
        return;
    }

    papers.forEach((p, index) => {
        const abstractHtml = p.abstract 
            ? `<details class="abstract-details">
                   <summary class="abstract-summary">Lihat Abstrak</summary>
                   <div class="abstract-text">${p.abstract}</div>
               </details>`
            : `<span style="color: #9ca3af; font-size: 12px; font-style: italic;">Tidak tersedia</span>`;

        // Logika Pencegahan Tombol Duplikat
        const isExtracted = extractedTitles.has(p.title);
        let aiButtonHtml = '';
        
        if (isExtracted) {
            aiButtonHtml = `<button class="btn-extract" style="background:#059669; cursor:not-allowed;" disabled>✅ Terekstrak</button>`;
        } else {
            const paperKw = p.keyword_text || (window.currentKeywordText || '') || document.getElementById('keyword')?.value || 'teknologi';
            aiButtonHtml = `<button class="btn-extract" onclick="extractPaperWithAI(this)" 
                        data-title="${(p.title || '').replace(/"/g, '&quot;')}"
                        data-abstract="${(p.abstract || '').replace(/"/g, '&quot;')}"
                        data-authors="${(p.authors || '').replace(/"/g, '&quot;')}"
                        data-year="${p.year || ''}"
                        data-source="${p.source}"
                        data-pdf="${p.pdf_url || ''}"
                        data-url="${p.paper_url || ''}"
                        data-keyword="${paperKw.replace(/"/g, '&quot;')}">
                        ✨ Ekstrak AI
                    </button>`;
        }

        const row = `
            <tr>
                <td>${index + 1}</td>
                <td><strong>${p.title}</strong><br><small>${p.authors || 'Tidak ada info penulis'}</small></td>
                <td>${abstractHtml}</td>
                <td>${p.year || '-'}</td>
                <td>${getSourceBadge(p.source)}</td>
                <td>
                    <a href="${p.paper_url}" target="_blank" class="btn-link">Buka Link</a>
                    ${p.pdf_url ? `<a href="${p.pdf_url}" target="_blank" class="btn-link" style="background:#059669; margin-left: 2px;">Lihat PDF</a>` : ''}
                    ${aiButtonHtml}
                </td>
            </tr>
        `;
        tbody.innerHTML += row;
    });
}

// ==========================================
// 3. FITUR SCRAPING & HISTORY
// ==========================================
document.getElementById('scrapeForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const keyword = document.getElementById('keyword').value;
    const amount = document.getElementById('amount').value;
    const source = document.querySelector('input[name="source"]:checked').value;
    const btn = document.getElementById('btnScrape');

    btn.disabled = true;
    btn.innerText = 'Memulai...';
    document.getElementById('progressArea').classList.remove('hidden');
    document.getElementById('resultArea').classList.add('hidden');
    
    try {
        const response = await fetch('/api/scrape', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ keyword, amount, source })
        });
        const data = await response.json();
        if (data.session_id) {
            currentSessionId = data.session_id;
            showToast("Sesi scraping berhasil dimulai!", "info");
            pollInterval = setInterval(checkStatus, 2000); 
        } else {
            showToast("Error: " + (data.error || "Gagal memulai scraping"), "error");
            btn.disabled = false;
            btn.innerText = 'Mulai Scraping';
        }
    } catch (err) {
        showToast("Gagal menghubungi server.", "error");
        btn.disabled = false;
    }
});

async function checkStatus() {
    try {
        const response = await fetch(`/api/scrape/status/${currentSessionId}`);
        const data = await response.json();
        
        const totalProcessed = data.new_papers_count + data.duplicate_skipped_count + data.invalid_skipped_count;
        let percentage = (totalProcessed / data.requested_amount) * 100;
        if (percentage > 100) percentage = 100;
        
        document.getElementById('progressFill').style.width = `${percentage}%`;
        document.getElementById('progressText').innerText = `Status: ${data.status.toUpperCase()} | Tersimpan: ${data.new_papers_count}`;

        if (data.status === 'completed' || data.status === 'failed') {
            clearInterval(pollInterval);
            document.getElementById('btnScrape').disabled = false;
            document.getElementById('btnScrape').innerText = 'Mulai Scraping';
            fetchResults();
        }
    } catch (err) {
        console.error(err);
    }
}

async function fetchResults() {
    const response = await fetch(`/api/scrape/result/${currentSessionId}`);
    const data = await response.json();
    document.getElementById('progressArea').classList.add('hidden');
    document.getElementById('resultArea').classList.remove('hidden');
    renderTable('resultTable', data.papers);
}

async function loadKeywordsHistory() {
    const response = await fetch('/api/history/keywords');
    const data = await response.json();
    const grid = document.getElementById('keywordList');
    grid.innerHTML = '';
    
    data.keywords.forEach(kw => {
        const card = document.createElement('div');
        card.className = 'keyword-card';
        card.innerHTML = `<h4>${kw.keyword}</h4><p><small>Total Paper: ${kw.total_papers}</small></p>`;
        card.onclick = () => loadKeywordDetail(kw.id, kw.keyword);
        grid.appendChild(card);
    });
}

async function loadKeywordDetail(keywordId, keywordText) {
    currentKeywordId = keywordId;
    window.currentKeywordText = keywordText;
    document.getElementById('keywordDetailArea').classList.remove('hidden');
    document.getElementById('keywordDetailTitle').innerText = `Detail Keyword: ${keywordText}`;
    const response = await fetch(`/api/history/keyword/${keywordId}`);
    const data = await response.json();
    renderTable('keywordDetailTable', data.papers);
}

async function loadAllHistory() {
    const response = await fetch('/api/history/all');
    const data = await response.json();
    renderTable('allHistoryTable', data.papers);
}

function toggleAllAbstracts(btn) {
    const table = btn.closest('table');
    if (!table) return;
    const isExpanding = btn.innerText.includes('Buka');
    const allDetails = table.querySelectorAll('tbody details.abstract-details');
    allDetails.forEach(details => {
        if (isExpanding) details.setAttribute('open', '');
        else details.removeAttribute('open');
    });
    if (isExpanding) {
        btn.innerText = 'Tutup Semua';
        btn.classList.add('active-toggle');
    } else {
        btn.innerText = 'Buka Semua';
        btn.classList.remove('active-toggle');
    }
}

// ==========================================
// 4. FITUR AI LLM & ROBOT MASSAL
// ==========================================
// 4. FITUR AI LLM & ROBOT MASSAL
// ==========================================
async function extractPaperWithAI(btn) {
    const title = btn.getAttribute('data-title');
    const abstract = btn.getAttribute('data-abstract');
    const authors = btn.getAttribute('data-authors');
    const year = btn.getAttribute('data-year');
    const source = btn.getAttribute('data-source');
    const pdf_url = btn.getAttribute('data-pdf');
    const paper_url = btn.getAttribute('data-url');
    const keywordInput = btn.getAttribute('data-keyword') || document.getElementById('keyword')?.value || 'teknologi';

    btn.innerHTML = '⏳ Berpikir...';
    btn.disabled = true;

    try {
        const response = await fetch('/api/extract', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, abstract, authors, year, source, pdf_url, paper_url, keyword: keywordInput }) 
        });
        
        const result = await response.json();
        if (response.ok) {
            btn.innerHTML = '✅ Terekstrak';
            btn.style.background = '#059669'; 
            loadExtractions(); 
            return true; 
        } else {
            btn.innerHTML = '❌ Gagal';
            btn.style.background = '#ef4444'; 
            btn.disabled = false;
            return false; 
        }
    } catch (e) {
        btn.innerHTML = '❌ Error';
        btn.style.background = '#ef4444';
        btn.disabled = false;
        return false;
    }
}

async function extractAllInVisibleTab(masterBtn) {
    const visibleTab = document.querySelector('.tab-content:not(.hidden)');
    if (!visibleTab) return;

    const allBtns = visibleTab.querySelectorAll('.btn-extract');
    const unextractedBtns = Array.from(allBtns).filter(btn => !btn.innerText.includes('Terekstrak'));

    if (unextractedBtns.length === 0) {
        alert("Semua paper di tabel ini sudah selesai diekstrak AI.");
        return;
    }

    if (!confirm(`Terdapat ${unextractedBtns.length} paper yang siap diekstrak.\nRobot akan memprosesnya otomatis.\nLanjutkan?`)) return;

    const originalText = masterBtn.innerHTML;
    masterBtn.disabled = true;
    let successCount = 0;
    let failCount = 0;

    for (let i = 0; i < unextractedBtns.length; i++) {
        const currentBtn = unextractedBtns[i];
        masterBtn.innerHTML = `⏳ Memproses... (${i + 1}/${unextractedBtns.length})`;
        currentBtn.scrollIntoView({ behavior: 'smooth', block: 'center' });

        const isSuccess = await extractPaperWithAI(currentBtn);
        if (isSuccess) successCount++;
        else failCount++;

        if (i < unextractedBtns.length - 1) {
            await new Promise(resolve => setTimeout(resolve, 12000));
        }
    }

    masterBtn.innerHTML = originalText;
    masterBtn.disabled = false;
    showToast(`🎉 Ekstraksi Selesai!\nBerhasil: ${successCount} | Gagal: ${failCount}`, "success");
}

function updateYearRangeFilter(val) {
    const label = document.getElementById('yearRangeMinLabel');
    if (label) label.innerText = val;
    filterExtractionsTable();
}

function populateKeywordFilterSelect() {
    const select = document.getElementById('keywordFilterSelect');
    if (!select) return;

    const currentValue = select.value || 'all';
    const kwCounts = {};

    allExtractionRecords.forEach(item => {
        const kw = (item.search_keyword || item.keyword || 'Umum').trim();
        if (kw) {
            kwCounts[kw] = (kwCounts[kw] || 0) + 1;
        }
    });

    select.innerHTML = '<option value="all">🔑 Semua Keyword Paper</option>';
    Object.keys(kwCounts).sort().forEach(kw => {
        const opt = document.createElement('option');
        opt.value = kw;
        opt.innerText = `🔑 ${kw} (${kwCounts[kw]} Paper)`;
        if (kw === currentValue) opt.selected = true;
        select.appendChild(opt);
    });
}

function filterExtractionsTable() {
    const searchInput = document.getElementById('extractionsSearchInput')?.value.toLowerCase().trim() || '';
    const minYear = parseInt(document.getElementById('yearRangeSlider')?.value || '2015');
    const relevanceFilter = document.getElementById('relevanceFilterSelect')?.value || 'all';
    const keywordFilter = document.getElementById('keywordFilterSelect')?.value || 'all';

    const filtered = allExtractionRecords.filter(item => {
        // 1. Filter Min Year
        const paperYear = parseInt(item.year) || 0;
        if (paperYear > 0 && paperYear < minYear) return false;

        // 2. Filter Relevance
        if (relevanceFilter === 'ya' && (!item.relevance || !item.relevance.toLowerCase().startsWith('ya'))) return false;
        if (relevanceFilter === 'tidak' && (item.relevance && item.relevance.toLowerCase().startsWith('ya'))) return false;

        // 3. Filter Keyword
        if (keywordFilter !== 'all') {
            const itemKw = (item.search_keyword || item.keyword || '').toLowerCase().trim();
            const filterKw = keywordFilter.toLowerCase().trim();
            if (itemKw !== filterKw && !itemKw.includes(filterKw)) return false;
        }

        // 4. Filter Search Text
        if (searchInput) {
            const haystack = [
                item.title, item.abstract, item.authors, item.algorithm,
                item.dataset, item.system, item.application, item.contribution,
                item.limitations, item.keyword, item.search_keyword, item.publisher, item.journal_name
            ].map(v => (v || '').toLowerCase()).join(' ');

            if (!haystack.includes(searchInput)) return false;
        }

        return true;
    });

    renderExtractionsTable(filtered);
}

function renderExtractionsTable(records) {
    const tbody = document.querySelector('#extractionsTable tbody');
    const countBadge = document.getElementById('filterCountBadge');
    if (!tbody) return;

    tbody.innerHTML = '';
    if (countBadge) {
        countBadge.innerText = `Menampilkan ${records.length} dari ${allExtractionRecords.length} Paper`;
    }

    if (!records || records.length === 0) {
        tbody.innerHTML = '<tr><td colspan="16" style="text-align:center; color:#9ca3af; padding: 20px;">Tidak ada data paper yang sesuai dengan filter pencarian.</td></tr>';
        return;
    }

    records.forEach((item, index) => {
        const row = `
            <tr>
                <td>${index + 1}</td>
                <td><strong>${item.relevance || '-'}</strong></td>
                <td><strong>${item.systematic_review || '-'}</strong></td>
                <td>${item.title || '-'}</td>
                <td>${item.year || '-'}</td>
                <td>${item.authors || '-'}</td>
                <td>${item.publisher || '-'}</td>
                <td>${item.application || '-'}</td>
                <td>${item.system || '-'}</td>
                <td>${item.algorithm || '-'}</td>
                <td>${item.dataset || '-'}</td>
                <td><span class="badge" style="background:#4f46e5; font-size:11px;">${item.search_keyword || item.keyword || '-'}</span></td>
                <td>${item.publication_type || '-'}</td>
                <td>${item.journal_name || '-'}</td>
                <td>
                    ${item.paper_url ? `<a href="${item.paper_url}" target="_blank" class="btn-link">Buka Link</a>` : '-'}
                </td>
                <td>
                    ${item.pdf_url ? `<a href="${item.pdf_url}" target="_blank" class="btn-link" style="background:#059669;">Unduh PDF</a>` : '-'}
                </td>
            </tr>
        `;
        tbody.innerHTML += row;
    });
}

async function loadExtractions() {
    try {
        const response = await fetch('/api/extractions');
        const data = await response.json();
        extractedTitles.clear();
        allExtractionRecords = data.extractions || [];

        allExtractionRecords.forEach(item => {
            if (item.original_title) extractedTitles.add(item.original_title);
            else if (item.title) extractedTitles.add(item.title);
        });

        populateKeywordFilterSelect();
        filterExtractionsTable();
    } catch (e) {
        console.error('Gagal memuat ekstraksi:', e);
    }
}

async function exportExtractions(type) {
    const selectedKw = document.getElementById('keywordFilterSelect')?.value || 'all';
    let url = `/api/extractions/export/${type}`;
    if (selectedKw !== 'all') {
        url += `?keyword=${encodeURIComponent(selectedKw)}`;
    }

    if (type !== 'pdf-zip') {
        window.location.href = url;
        return;
    }
    const btn = event.target;
    const originalText = btn.innerText;
    btn.innerText = '⏳ Mengemas ZIP...';
    btn.disabled = true;
    
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error("Gagal mengunduh ZIP");
        
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `kumpulan_pdf_ekstraksi_ai_${Date.now()}.zip`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
        showToast("Terjadi kesalahan jaringan.", "error");
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
}

async function exportRangkumanReview() {
    const selectedKw = document.getElementById('keywordFilterSelect')?.value || 'all';
    let url = '/api/extractions/export/rangkuman-review';
    if (selectedKw !== 'all') {
        url += `?keyword=${encodeURIComponent(selectedKw)}`;
    }

    const btn = event.target;
    const originalText = btn.innerText;
    btn.innerText = '⏳ Membuat dokumen...';
    btn.disabled = true;

    try {
        const response = await fetch(url);
        if (!response.ok) {
            const err = await response.json();
            showToast('Gagal: ' + (err.error || 'Terjadi kesalahan'), "error");
            return;
        }
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `rangkuman_review_${Date.now()}.docx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(downloadUrl);
        showToast("Dokumen rangkuman review berhasil dibuat!", "success");
    } catch (error) {
        showToast('Terjadi kesalahan jaringan: ' + error.message, "error");
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
}

// ==========================================
// 5. AUTO-START SAAT WEB DIMUAT
// ==========================================
document.addEventListener('DOMContentLoaded', async () => {
    // Muat data ekstraksi diam-diam di belakang layar
    await loadExtractions();
    await checkChatStatus();
    
    // Buka tab pertama secara otomatis agar tidak layar putih
    const defaultTabBtn = document.querySelector('.tab-btn');
    if (defaultTabBtn) {
        defaultTabBtn.click();
    }
});

// ==========================================
// 6. FITUR CHAT AI ASSISTANT (RAG / VECTOR DB)
// ==========================================
let chatKeywordsData = [];

async function checkChatStatus() {
    try {
        const response = await fetch('/api/chat/status');
        const data = await response.json();
        chatKeywordsData = data.keywords || [];

        const select = document.getElementById('chatKeywordSelect');
        if (select) {
            const currentSelected = select.value || 'all';
            select.innerHTML = `<option value="all">🌐 Semua Keyword Paper (${data.total_extracted || 0} Paper)</option>`;
            chatKeywordsData.forEach(item => {
                const opt = document.createElement('option');
                opt.value = item.keyword;
                opt.innerText = `📄 ${item.keyword} (${item.count} Paper)`;
                if (item.keyword === currentSelected) opt.selected = true;
                select.appendChild(opt);
            });
        }

        onChatKeywordChange(data.total_extracted);
    } catch (e) {
        console.error('Gagal mengecek status chat:', e);
    }
}

function onChatKeywordChange(overrideTotal = null) {
    const select = document.getElementById('chatKeywordSelect');
    const badge = document.getElementById('chatStatusBadge');
    if (!badge) return;

    const selectedKw = select?.value || 'all';
    let count = 0;

    if (selectedKw === 'all') {
        if (overrideTotal !== null) {
            count = overrideTotal;
        } else {
            count = chatKeywordsData.reduce((acc, item) => acc + item.count, 0);
        }
        badge.innerText = `📚 Repositori: ${count} Paper`;
    } else {
        const found = chatKeywordsData.find(item => item.keyword === selectedKw);
        count = found ? found.count : 0;
        badge.innerText = `📚 Repositori [${selectedKw}]: ${count} Paper`;
    }

    if (count > 0) {
        badge.style.backgroundColor = '#dcfce7';
        badge.style.color = '#166534';
    } else {
        badge.style.backgroundColor = '#fef3c7';
        badge.style.color = '#92400e';
    }
}

function useSampleQuestion(text) {
    const input = document.getElementById('chatInput');
    if (input) {
        input.value = text;
        document.getElementById('chatForm')?.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
    }
}

function parseSimpleMarkdown(text) {
    if (!text) return '';
    let html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    // Bold **text**
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Italic *text*
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    // Code `code`
    html = html.replace(/`(.*?)`/g, '<code style="background:#f1f5f9; padding:2px 6px; border-radius:4px; font-size:12px;">$1</code>');

    // Simple markdown tables
    const lines = html.split('\n');
    let inTable = false;
    let tableHtml = '';
    let processedLines = [];

    for (let i = 0; i < lines.length; i++) {
        let line = lines[i].trim();
        if (line.startsWith('|') && line.endsWith('|')) {
            if (line.includes('---')) continue; // Skip header separator line
            const cells = line.split('|').slice(1, -1);
            if (!inTable) {
                inTable = true;
                tableHtml = '<table><thead><tr>' + cells.map(c => `<th>${c.trim()}</th>`).join('') + '</tr></thead><tbody>';
            } else {
                tableHtml += '<tr>' + cells.map(c => `<td>${c.trim()}</td>`).join('') + '</tr>';
            }
        } else {
            if (inTable) {
                inTable = false;
                tableHtml += '</tbody></table>';
                processedLines.push(tableHtml);
                tableHtml = '';
            }
            if (line.startsWith('- ') || line.startsWith('* ')) {
                processedLines.push(`• ${line.substring(2)}<br>`);
            } else if (line.length === 0) {
                processedLines.push('<br>');
            } else {
                processedLines.push(line + '<br>');
            }
        }
    }
    if (inTable) {
        tableHtml += '</tbody></table>';
        processedLines.push(tableHtml);
    }

    return processedLines.join('');
}

document.getElementById('chatForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const input = document.getElementById('chatInput');
    const question = input.value.trim();
    if (!question) return;

    const chatBox = document.getElementById('chatBox');
    const btn = document.getElementById('btnSendChat');
    const selectedKeyword = document.getElementById('chatKeywordSelect')?.value || 'all';

    // 1. Tampilkan pesan user
    const kwBadgeText = selectedKeyword !== 'all' ? ` <span style="font-size: 0.75rem; background: #e0e7ff; color: #4338ca; padding: 2px 8px; border-radius: 12px; font-weight: 600;">🔑 Keyword: ${selectedKeyword}</span>` : '';
    const userBubble = `
        <div class="chat-message user-message">
            <div class="avatar">👤</div>
            <div class="message-content">${question.replace(/</g, '&lt;').replace(/>/g, '&gt;')}${kwBadgeText}</div>
        </div>
    `;
    chatBox.insertAdjacentHTML('beforeend', userBubble);
    input.value = '';
    chatBox.scrollTop = chatBox.scrollHeight;

    // 2. Tampilkan loading bot
    const loadingId = 'loading-' + Date.now();
    const loadingBubble = `
        <div class="chat-message bot-message" id="${loadingId}">
            <div class="avatar">🤖</div>
            <div class="message-content" style="color: #6b7280; font-style: italic;">
                ⏳ Assistant sedang menganalisis repositori paper ${selectedKeyword !== 'all' ? `[Keyword: ${selectedKeyword}]` : ''} dan menyusun jawaban...
            </div>
        </div>
    `;
    chatBox.insertAdjacentHTML('beforeend', loadingBubble);
    chatBox.scrollTop = chatBox.scrollHeight;

    btn.disabled = true;

    try {
        const response = await fetch('/api/chat/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question, keyword: selectedKeyword })
        });
        const data = await response.json();

        const loadingElem = document.getElementById(loadingId);
        if (loadingElem) loadingElem.remove();

        let citedHtml = '';
        if (data.cited_papers && data.cited_papers.length > 0) {
            citedHtml = `
                <details style="margin-top: 12px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px 12px; font-size: 12px;">
                    <summary style="cursor: pointer; font-weight: bold; color: #475569;">📚 Sitasi Paper yang Digunakan (${data.cited_papers.length})</summary>
                    <ul style="margin-top: 6px; padding-left: 18px; color: #64748b;">
                        ${data.cited_papers.map(p => `<li><strong>[Paper #${p.index}]</strong> ${p.title} (${p.year || '-'}) ${p.paper_url ? `<a href="${p.paper_url}" target="_blank" style="color: #2563eb;">Link</a>` : ''}</li>`).join('')}
                    </ul>
                </details>
            `;
        }

        const formattedAnswer = parseSimpleMarkdown(data.answer || data.error || 'Terjadi kesalahan.');

        const botBubble = `
            <div class="chat-message bot-message">
                <div class="avatar">🤖</div>
                <div class="message-content">
                    ${formattedAnswer}
                    ${citedHtml}
                </div>
            </div>
        `;
        chatBox.insertAdjacentHTML('beforeend', botBubble);
        chatBox.scrollTop = chatBox.scrollHeight;

    } catch (err) {
        const loadingElem = document.getElementById(loadingId);
        if (loadingElem) loadingElem.remove();

        const errorBubble = `
            <div class="chat-message bot-message">
                <div class="avatar">🤖</div>
                <div class="message-content" style="color: #dc2626;">
                    ❌ Terjadi kesalahan jaringan saat menghubungkan ke AI RAG Assistant.
                </div>
            </div>
        `;
        chatBox.insertAdjacentHTML('beforeend', errorBubble);
        chatBox.scrollTop = chatBox.scrollHeight;
    } finally {
        btn.disabled = false;
    }
});