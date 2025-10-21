/* ====== Data + Utilities ====== */
let galleryData = [];
let flattenedImages = [];
const filterState = { subject: false, date: false };

/* Parse/format helpers */
function parseDDMMYYYY(ddmmyyyy) {
    const parts = String(ddmmyyyy).split('-');
    if (parts.length !== 3) return null;
    let [dd, mm, yyyy] = parts;
    dd = dd.padStart(2, '0'); mm = mm.padStart(2, '0');
    const iso = `${yyyy}-${mm}-${dd}`;
    const ts = new Date(`${iso}T00:00:00`).getTime();
    return { iso, ts, raw: ddmmyyyy };
}
function toDDMMYYYYFromISO(iso) {
    if (!iso) return null;
    const parts = iso.split('-');
    if (parts.length !== 3) return null;
    return `${parts[2]}-${parts[1]}-${parts[0]}`;
}

/* Flatten images for filtering */
function getFlattenedImages(data) {
    const arr = [];
    (data || []).forEach(d => {
        (d.subjects || []).forEach(s => {
            (s.images || []).forEach(p => arr.push({ date: d.date, subject: s.subject, path: p }));
        });
    });
    return arr;
}

/* ====== Fetching (with fallback sample) ====== */
async function fetchData() {
    try {
        const res = await fetch('info.json');
        if (!res.ok) throw new Error('fetch failed');
        galleryData = await res.json();
    } catch (e) {
        console.warn('Could not fetch info.json, using embedded sample data. Error:', e);
        galleryData = [
            { "date": "21-12-2009", "subjects": [{ "subject": "Physics", "images": ["images/21-12-2009/phy1.jpg", "images/21-12-2009/phy2.jpg"] }, { "subject": "Chemistry", "images": ["images/21-12-2009/chem1.jpg", "images/21-12-2009/chem2.jpg"] }] },
            { "date": "10-01-2010", "subjects": [{ "subject": "Biology", "images": ["images/10-01-2010/bio1.jpg", "images/10-01-2010/bio2.jpg", "images/10-01-2010/bio3.jpg"] }, { "subject": "Physics", "images": ["images/10-01-2010/phy3.jpg"] }] }
        ];
    }

    flattenedImages = getFlattenedImages(galleryData);
    populateFilterOptions(galleryData);
    renderGroupedImages(galleryData, 'image-container');
    updateHomepageStats();
}

/* ====== Rendering ====== */
function renderImages(data, containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    if (!data || data.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📚</div>
                <h3>No Notes Found</h3>
                <p>Try adjusting your filters or check back later for new notes.</p>
            </div>
        `;
        return;
    }

    const grid = document.createElement('div');
    grid.className = 'image-grid';

    data.forEach(item => {
        const card = document.createElement('div');
        card.className = 'image-card';
        card.innerHTML = `
      <div class="image-wrapper">
        <img src="${item.path}" alt="${item.subject} ${item.date}" loading="lazy" onclick="openImageInNewTab('${item.path}')">
      </div>
      <div class="image-info">
        <p><strong>Subject:</strong> ${item.subject}</p>
        <p><strong>Date:</strong> ${item.date}</p>
        <div class="button-group">
          <button class="preview-btn" onclick="openPreview('${item.path}', '${item.subject}', '${item.date}')" title="Preview image">
            <span>👁️ Preview</span>
          </button>
          <button class="download-btn-separate" onclick="downloadImage('${item.path}', '${item.subject}_${item.date}')" title="Download image">
            <span>📥 Download</span>
          </button>
        </div>
      </div>
    `;
        grid.appendChild(card);
    });

    container.appendChild(grid);
}

function renderGroupedImages(data, containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';

    const enriched = (data || []).map(d => ({ raw: d.date, dateObj: parseDDMMYYYY(d.date), subjects: d.subjects })).filter(x => x.dateObj !== null);
    enriched.sort((a, b) => b.dateObj.ts - a.dateObj.ts);

    enriched.forEach(dItem => {
        const dateSection = document.createElement('div');
        dateSection.className = 'date-group';
        dateSection.innerHTML = `<h3>📅 Date: ${dItem.raw}</h3>`;

        (dItem.subjects || []).forEach(s => {
            const subjectSection = document.createElement('div');
            subjectSection.className = 'subject-group';
            subjectSection.innerHTML = `<h4>Subject: ${s.subject}</h4>`;

            const imageGrid = document.createElement('div');
            imageGrid.className = 'image-grid';

            (s.images || []).forEach(p => {
                const card = document.createElement('div');
                card.className = 'image-card';
                card.innerHTML = `
          <div class="image-wrapper">
            <img src="${p}" alt="${s.subject} on ${dItem.raw}" loading="lazy" onclick="openImageInNewTab('${p}')">
          </div>
          <div class="image-info">
            <p><strong>Subject:</strong> ${s.subject}</p>
            <p><strong>Date:</strong> ${dItem.raw}</p>
            <div class="button-group">
              <button class="preview-btn" onclick="openPreview('${p}', '${s.subject}', '${dItem.raw}')" title="Preview image">
                <span>👁️ Preview</span>
              </button>
              <button class="download-btn-separate" onclick="downloadImage('${p}', '${s.subject}_${dItem.raw}')" title="Download image">
                <span>📥 Download</span>
              </button>
            </div>
          </div>
        `;
                imageGrid.appendChild(card);
            });

            subjectSection.appendChild(imageGrid);
            dateSection.appendChild(subjectSection);
        });

        container.appendChild(dateSection);
    });
}

/* ====== Filters population & helpers ====== */
function populateFilterOptions(data) {
    const subjectSelect = document.getElementById('subject-filter');
    const daySelect = document.getElementById('day-filter');
    const monthSelect = document.getElementById('month-filter');
    const yearSelect = document.getElementById('year-filter');
    const subjects = new Set();
    const days = new Set();
    const months = new Set();
    const years = new Set();

    (data || []).forEach(d => {
        const parsed = parseDDMMYYYY(d.date);
        if (parsed) {
            const [day, month, year] = d.date.split('-');
            days.add(day);
            months.add(month);
            years.add(year);
        }
        (d.subjects || []).forEach(s => subjects.add(s.subject));
    });

    // Populate subjects
    subjectSelect.innerHTML = '<option value="">Any</option>';
    Array.from(subjects).sort((a, b) => a.localeCompare(b)).forEach(sub => {
        const opt = document.createElement('option'); 
        opt.value = sub; 
        opt.textContent = sub; 
        subjectSelect.appendChild(opt);
    });

    // Populate day dropdown
    daySelect.innerHTML = '<option value="">Any</option>';
    Array.from(days).sort((a, b) => parseInt(a) - parseInt(b)).forEach(day => {
        const opt = document.createElement('option'); 
        opt.value = day; 
        opt.textContent = day; 
        daySelect.appendChild(opt);
    });

    // Populate month dropdown
    monthSelect.innerHTML = '<option value="">Any</option>';
    Array.from(months).sort((a, b) => parseInt(a) - parseInt(b)).forEach(month => {
        const opt = document.createElement('option'); 
        opt.value = month; 
        opt.textContent = getMonthName(month); 
        monthSelect.appendChild(opt);
    });

    // Populate year dropdown
    yearSelect.innerHTML = '<option value="">Any</option>';
    Array.from(years).sort((a, b) => parseInt(b) - parseInt(a)).forEach(year => {
        const opt = document.createElement('option'); 
        opt.value = year; 
        opt.textContent = year; 
        yearSelect.appendChild(opt);
    });

    updateFilterStatus();
    subjectSelect.onchange = applyCombinedFilter;
}

function getMonthName(monthNum) {
    const months = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ];
    return months[parseInt(monthNum) - 1] || monthNum;
}

function clearSubjects() {
    document.getElementById('subject-filter').value = '';
    applyCombinedFilter();
}
function clearDate() {
    document.getElementById('day-filter').value = '';
    document.getElementById('month-filter').value = '';
    document.getElementById('year-filter').value = '';
    applyCombinedFilter();
}

function updateFilterStatus() {
    const el = document.getElementById('filter-status');
    if (el) el.textContent = `Subject: ${filterState.subject ? 'ON' : 'OFF'} · Date: ${filterState.date ? 'ON' : 'OFF'}`;
}

/* ====== Toggle filters & getters ====== */
function toggleFilter(filterType) {
    filterState[filterType] = !filterState[filterType];
    const controls = document.getElementById(`${filterType}-filter-controls`);
    const btn = document.getElementById(`toggle-${filterType}-btn`);
    if (filterState[filterType]) {
        controls.classList.add('enabled');
        btn.textContent = `Disable ${capitalize(filterType)} Filter`;
    } else {
        controls.classList.remove('enabled');
        btn.textContent = `Enable ${capitalize(filterType)} Filter`;
    }
    updateFilterStatus();
    applyCombinedFilter();
}
function capitalize(s) { return s.charAt(0).toUpperCase() + s.slice(1); }

function getSelectedSubject() {
    if (!filterState.subject) return null;
    const sel = document.getElementById('subject-filter');
    return sel.value || null;
}
function getSelectedDateFilters() {
    if (!filterState.date) return null;
    const day = document.getElementById('day-filter').value;
    const month = document.getElementById('month-filter').value;
    const year = document.getElementById('year-filter').value;
    
    // Return null if no date filters are selected
    if (!day && !month && !year) return null;
    
    return { day, month, year };
}

/* ====== Main filtering logic ====== */
function applyCombinedFilter() {
    const subject = getSelectedSubject();
    const dateFilters = getSelectedDateFilters();

    // Filter the original grouped data structure
    let filteredData = galleryData.slice();

    // Apply date filtering first
    if (filterState.date && dateFilters) {
        filteredData = filteredData.filter(dItem => {
            const [day, month, year] = dItem.date.split('-');
            
            const matchesDay = !dateFilters.day || day === dateFilters.day;
            const matchesMonth = !dateFilters.month || month === dateFilters.month;
            const matchesYear = !dateFilters.year || year === dateFilters.year;
            
            return matchesDay && matchesMonth && matchesYear;
        });
    }

    // Apply subject filtering
    if (filterState.subject && subject) {
        filteredData = filteredData.map(dItem => {
            const filteredSubjects = dItem.subjects.filter(s => s.subject === subject);
            return { ...dItem, subjects: filteredSubjects };
        }).filter(dItem => dItem.subjects.length > 0);
    }

    // Use the grouped display function to match the main gallery style
    renderGroupedImages(filteredData, 'filtered-image-container');
}

/* ====== Reset + View management ====== */
function resetAllFilters() {
    filterState.subject = false; filterState.date = false;
    document.getElementById('subject-filter-controls').classList.remove('enabled');
    document.getElementById('date-filter-controls').classList.remove('enabled');
    document.getElementById('toggle-subject-btn').textContent = 'Enable Subject Filter';
    document.getElementById('toggle-date-btn').textContent = 'Enable Date Filter';
    clearSubjects(); clearDate(); updateFilterStatus(); applyCombinedFilter();
}

function showView(viewId) {
    document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
    const target = document.getElementById(viewId);
    if (target) target.classList.remove('hidden');
    if (viewId === 'filter-view') applyCombinedFilter();
    if (viewId === 'gallery-view') renderGroupedImages(galleryData, 'image-container');
}

/* ====== Statistics & Homepage ====== */
function calculateStats() {
    const totalImages = flattenedImages.length;
    const uniqueSubjects = new Set(flattenedImages.map(img => img.subject)).size;
    const uniqueDates = new Set(flattenedImages.map(img => img.date)).size;
    
    // Calculate date range
    const dates = Array.from(new Set(flattenedImages.map(img => img.date)));
    const sortedDates = dates.sort((a, b) => {
        const dateA = parseDDMMYYYY(a);
        const dateB = parseDDMMYYYY(b);
        return dateA.ts - dateB.ts;
    });
    
    const oldestDate = sortedDates[0] || 'N/A';
    const newestDate = sortedDates[sortedDates.length - 1] || 'N/A';
    
    // Calculate subject breakdown
    const subjectBreakdown = {};
    flattenedImages.forEach(img => {
        subjectBreakdown[img.subject] = (subjectBreakdown[img.subject] || 0) + 1;
    });
    
    return {
        totalImages,
        uniqueSubjects,
        uniqueDates,
        oldestDate,
        newestDate,
        subjectBreakdown
    };
}

function updateHomepageStats() {
    const stats = calculateStats();
    const statsContainer = document.getElementById('home-stats');
    
    if (!statsContainer) return;
    
    // Update hero stats dynamically
    const heroStats = document.querySelectorAll('.stat-number-large');
    if (heroStats.length >= 3) {
        heroStats[0].textContent = stats.totalImages;
        heroStats[1].textContent = stats.uniqueSubjects;
        heroStats[2].textContent = stats.uniqueDates;
    }
    
    // Update hero stat labels
    const heroLabels = document.querySelectorAll('.stat-label-large');
    if (heroLabels.length >= 3) {
        heroLabels[0].textContent = 'Notes Shared';
        heroLabels[1].textContent = 'Subjects Covered';
        heroLabels[2].textContent = 'Study Days';
    }
    
    const subjectBreakdownHTML = Object.entries(stats.subjectBreakdown)
        .sort((a, b) => b[1] - a[1])
        .map(([subject, count]) => `<span class="subject-stat">${subject}: ${count}</span>`)
        .join(' • ');
    
    statsContainer.innerHTML = `
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">${stats.totalImages}</div>
                <div class="stat-label">Total Images</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${stats.uniqueSubjects}</div>
                <div class="stat-label">Subjects</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${stats.uniqueDates}</div>
                <div class="stat-label">Days of Notes</div>
            </div>
        </div>
        <div class="stats-details">
            <div class="date-range">
                <strong>Date Range:</strong> ${stats.oldestDate} to ${stats.newestDate}
            </div>
            <div class="subject-breakdown">
                <strong>Subject Breakdown:</strong><br>
                <div class="subject-list">${subjectBreakdownHTML}</div>
            </div>
        </div>
    `;
}

/* ====== Image Actions ====== */
function openImageInNewTab(imagePath) {
    window.open(imagePath, '_blank');
}

function downloadImage(imagePath, filename) {
    // Create a temporary anchor element to trigger download
    const link = document.createElement('a');
    link.href = imagePath;
    link.download = filename || 'image';
    link.target = '_blank';
    
    // Append to body, click, and remove
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

/* ====== Preview Modal Functions ====== */
function openPreview(imagePath, subject, date) {
    const overlay = document.getElementById('preview-overlay');
    const previewImage = document.getElementById('preview-image');
    const previewInfo = document.getElementById('preview-info');
    
    // Set the image source
    previewImage.src = imagePath;
    previewImage.alt = `${subject} - ${date}`;
    
    // Set the info text
    previewInfo.textContent = `${subject} • ${date}`;
    
    // Show the overlay
    overlay.classList.add('active');
    
    // Prevent body scroll
    document.body.style.overflow = 'hidden';
}

function closePreview() {
    const overlay = document.getElementById('preview-overlay');
    
    // Hide the overlay
    overlay.classList.remove('active');
    
    // Restore body scroll
    document.body.style.overflow = '';
    
    // Clear the image source after animation
    setTimeout(() => {
        const previewImage = document.getElementById('preview-image');
        previewImage.src = '';
    }, 300);
}

// Close preview on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closePreview();
    }
});

/* ====== Init ====== */
document.addEventListener('DOMContentLoaded', () => { fetchData(); });
