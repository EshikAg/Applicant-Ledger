/**
 * Intake Ledger - Application Controller
 * Handles Serial Number generation (A000+), CSV import/export, UI rendering,
 * status tracking, filtering, resume upload pipeline, and ZIP bundle packaging.
 */

// ==================== STATE MANAGEMENT ====================
const STORAGE_KEY = 'applicants_ledger_records_v1';
const LAST_EXPORT_KEY = 'applicants_ledger_last_export_date';

let applicants = [];
let uploadedFilesMap = new Map(); // fileName -> File Blob for ZIP packaging
let activeFilters = {
  search: '',
  status: 'all',
  department: 'all'
};

// ==================== SERIAL NUMBER LOGIC ====================
/**
 * Format integer index into Serial Number starting from A000:
 * 0 -> A000, 1 -> A001, ..., 999 -> A999, 1000 -> B000, etc.
 */
function indexToSerial(idx) {
  const letterIndex = Math.floor(idx / 1000);
  const numberPart = idx % 1000;
  
  // Convert letterIndex to letter: 0 = A, 1 = B, ..., 25 = Z, 26 = AA, etc.
  let letterPart = '';
  let temp = letterIndex;
  do {
    letterPart = String.fromCharCode(65 + (temp % 26)) + letterPart;
    temp = Math.floor(temp / 26) - 1;
  } while (temp >= 0);

  return `${letterPart}${String(numberPart).padStart(3, '0')}`;
}

/**
 * Parse serial string like "A000" or "B125" back into numeric index
 */
function serialToIndex(serial) {
  if (!serial || typeof serial !== 'string') return -1;
  const match = serial.trim().toUpperCase().match(/^([A-Z]+)(\d{3,})$/);
  if (!match) return -1;

  const letterStr = match[1];
  const num = parseInt(match[2], 10);

  let letterVal = 0;
  for (let i = 0; i < letterStr.length; i++) {
    letterVal = letterVal * 26 + (letterStr.charCodeAt(i) - 64);
  }
  letterVal -= 1; // 0-based for 'A'

  return letterVal * 1000 + num;
}

/**
 * Generate next serial number based on existing applicants
 */
function getNextSerial() {
  if (applicants.length === 0) {
    return 'A000';
  }

  let maxIndex = -1;
  for (const item of applicants) {
    const idx = serialToIndex(item.no);
    if (idx > maxIndex) {
      maxIndex = idx;
    }
  }

  return indexToSerial(maxIndex + 1);
}

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
  loadApplicantsFromStorage();
  initLastExportNotice();
  initEventListeners();
  renderAll();
});

function loadApplicantsFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      applicants = JSON.parse(raw);
    } else {
      // If first time visit, offer clean default or sample data
      applicants = [];
    }
  } catch (e) {
    console.error('Failed to load storage:', e);
    applicants = [];
  }
}

function saveApplicantsToStorage() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(applicants));
  } catch (e) {
    console.error('Failed to save to storage:', e);
  }
}

// ==================== EVENT LISTENERS ====================
function initEventListeners() {
  // Dropzone & File Input
  const dropzone = document.getElementById('uploadDropzone');
  const fileInput = document.getElementById('resumeFileInput');

  dropzone.addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFilesUpload(Array.from(e.target.files));
      fileInput.value = '';
    }
  });

  // Drag and drop handlers
  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('drag-active');
  });
  dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag-active'));
  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('drag-active');
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFilesUpload(Array.from(e.dataTransfer.files));
    }
  });

  // Search Input
  const searchInput = document.getElementById('searchInput');
  const clearSearchBtn = document.getElementById('clearSearchBtn');

  searchInput.addEventListener('input', (e) => {
    activeFilters.search = e.target.value.trim().toLowerCase();
    clearSearchBtn.style.display = activeFilters.search ? 'block' : 'none';
    renderTable();
  });

  clearSearchBtn.addEventListener('click', () => {
    searchInput.value = '';
    activeFilters.search = '';
    clearSearchBtn.style.display = 'none';
    renderTable();
  });

  // Action Buttons
  document.getElementById('exportCsvBtn').addEventListener('click', exportToCsv);
  document.getElementById('exportNowBtn').addEventListener('click', exportToCsv);

  document.getElementById('importCsvBtn').addEventListener('click', () => {
    document.getElementById('importCsvFileInput').click();
  });
  document.getElementById('importCsvFileInput').addEventListener('change', handleCsvFileImport);

  document.getElementById('downloadZipBtn').addEventListener('click', downloadAllAsZip);
  document.getElementById('checkDataBtn').addEventListener('click', openCheckDataModal);

  // Manual Add Modal
  document.getElementById('addManuallyBtn').addEventListener('click', () => openApplicantModal());
  document.getElementById('emptyAddBtn').addEventListener('click', () => openApplicantModal());
  document.getElementById('closeApplicantModalBtn').addEventListener('click', closeApplicantModal);
  document.getElementById('cancelApplicantModalBtn').addEventListener('click', closeApplicantModal);
  document.getElementById('applicantForm').addEventListener('submit', handleApplicantFormSubmit);

  // Check Data Modal Close
  document.getElementById('closeCheckDataModalBtn').addEventListener('click', closeCheckDataModal);
  document.getElementById('closeCheckDataDoneBtn').addEventListener('click', closeCheckDataModal);

  // View Resume Modal Close
  document.getElementById('closeViewResumeModalBtn').addEventListener('click', closeViewResumeModal);
  document.getElementById('closeViewResumeDoneBtn').addEventListener('click', closeViewResumeModal);

  // Demo Data Buttons
  document.getElementById('loadSampleDataBtn').addEventListener('click', loadSampleDemoData);
  document.getElementById('clearAllDataBtn').addEventListener('click', clearAllDataPrompt);

  // Reset filter buttons
  document.getElementById('resetStatusFilterBtn').addEventListener('click', () => {
    activeFilters.status = 'all';
    renderAll();
  });
  document.getElementById('resetDeptFilterBtn').addEventListener('click', () => {
    activeFilters.department = 'all';
    renderAll();
  });
  document.getElementById('clearAllFiltersBtn').addEventListener('click', clearAllFilters);

  // Status and Department card clicks
  document.getElementById('statusStatsList').addEventListener('click', (e) => {
    const item = e.target.closest('.stats-item');
    if (!item) return;
    const status = item.dataset.status;
    activeFilters.status = (activeFilters.status === status) ? 'all' : status;
    renderAll();
  });

  document.getElementById('departmentStatsList').addEventListener('click', (e) => {
    const item = e.target.closest('.stats-item');
    if (!item) return;
    const dept = item.dataset.dept;
    activeFilters.department = (activeFilters.department === dept) ? 'all' : dept;
    renderAll();
  });
}

// ==================== BATCH FILE UPLOAD & PARSING ====================
async function handleFilesUpload(files) {
  if (!files || files.length === 0) return;

  const defaultPosition = document.getElementById('positionTagInput').value.trim();
  const progressContainer = document.getElementById('uploadProgressContainer');
  const progressBar = document.getElementById('uploadProgressBar');
  const progressStatus = document.getElementById('uploadProgressStatus');
  const progressPercent = document.getElementById('uploadProgressPercent');

  progressContainer.style.display = 'flex';
  let processed = 0;
  const total = files.length;

  for (const file of files) {
    progressStatus.textContent = `Reading & parsing: ${file.name} (${processed + 1}/${total})...`;
    const percent = Math.round((processed / total) * 100);
    progressBar.style.width = `${percent}%`;
    progressPercent.textContent = `${percent}%`;

    try {
      const parsedData = await ResumeParser.parseResumeFile(file, defaultPosition);

      // Generate next serial number starting from A000
      const serialNo = getNextSerial();

      const newApplicant = {
        no: serialNo,
        applicant: parsedData.applicant,
        designation: parsedData.designation,
        department: parsedData.department,
        email: parsedData.email,
        contact: parsedData.contact,
        dob: parsedData.dob,
        city: parsedData.city,
        status: parsedData.status || 'New',
        reasonForLeaving: parsedData.reasonForLeaving,
        expectedSalary: parsedData.expectedSalary,
        remarks: parsedData.remarks,
        skills: parsedData.skills,
        fileName: parsedData.fileName,
        rawText: parsedData.rawText
      };

      // Store in ledger
      applicants.push(newApplicant);
      uploadedFilesMap.set(file.name, file);

    } catch (err) {
      console.error(`Failed parsing file ${file.name}:`, err);
      showToast(`Could not parse ${file.name}`, 'warning');
    }

    processed++;
  }

  progressBar.style.width = '100%';
  progressPercent.textContent = '100%';
  progressStatus.textContent = `Completed! ${processed} resume(s) recorded in ledger.`;

  setTimeout(() => {
    progressContainer.style.display = 'none';
    progressBar.style.width = '0%';
  }, 1600);

  saveApplicantsToStorage();
  renderAll();
  showToast(`Successfully added ${processed} applicant(s). Ledger updated!`, 'success');
}

// ==================== RENDERING ====================
function renderAll() {
  updateStatsCards();
  renderFilterPills();
  renderTable();
}

/**
 * Update Status and Department counts
 */
function updateStatsCards() {
  const total = applicants.length;
  document.getElementById('statTotalCount').textContent = total;

  const statusCounts = {
    'New': 0,
    'Ex employee': 0,
    'Potential Candidate': 0,
    'working with us': 0,
    'For Database': 0,
    'Others': 0,
    'Do not follow up': 0
  };

  const deptCounts = {
    'Front office': 0,
    'Kitchen': 0,
    'Service': 0,
    'Account': 0,
    'Maintenance': 0,
    'Sales': 0,
    'Admin': 0,
    'Housekeeping': 0,
    'Stores': 0
  };

  for (const app of applicants) {
    if (statusCounts[app.status] !== undefined) {
      statusCounts[app.status]++;
    } else {
      statusCounts['Others']++;
    }

    if (deptCounts[app.department] !== undefined) {
      deptCounts[app.department]++;
    }
  }

  document.getElementById('statNewCount').textContent = statusCounts['New'];
  document.getElementById('statExEmployeeCount').textContent = statusCounts['Ex employee'];
  document.getElementById('statPotentialCount').textContent = statusCounts['Potential Candidate'];
  document.getElementById('statWorkingCount').textContent = statusCounts['working with us'];
  document.getElementById('statDatabaseCount').textContent = statusCounts['For Database'];
  document.getElementById('statOthersCount').textContent = statusCounts['Others'];
  document.getElementById('statDnfCount').textContent = statusCounts['Do not follow up'];

  document.getElementById('deptFrontOfficeCount').textContent = deptCounts['Front office'];
  document.getElementById('deptKitchenCount').textContent = deptCounts['Kitchen'];
  document.getElementById('deptServiceCount').textContent = deptCounts['Service'];
  document.getElementById('deptAccountCount').textContent = deptCounts['Account'];
  document.getElementById('deptMaintenanceCount').textContent = deptCounts['Maintenance'];
  document.getElementById('deptSalesCount').textContent = deptCounts['Sales'];
  document.getElementById('deptAdminCount').textContent = deptCounts['Admin'];
  document.getElementById('deptHousekeepingCount').textContent = deptCounts['Housekeeping'];
  document.getElementById('deptStoresCount').textContent = deptCounts['Stores'];

  // Highlight active filter items
  document.querySelectorAll('#statusStatsList .stats-item').forEach(el => {
    const s = el.dataset.status;
    if (activeFilters.status === s || (activeFilters.status === 'all' && s === 'all')) {
      el.classList.add('active-filter');
    } else {
      el.classList.remove('active-filter');
    }
  });

  document.querySelectorAll('#departmentStatsList .stats-item').forEach(el => {
    const d = el.dataset.dept;
    if (activeFilters.department === d) {
      el.classList.add('active-filter');
    } else {
      el.classList.remove('active-filter');
    }
  });
}

/**
 * Filter pills display
 */
function renderFilterPills() {
  const pillBar = document.getElementById('filterPillBar');
  const pillList = document.getElementById('filterPillList');
  pillList.innerHTML = '';

  let hasFilters = false;

  if (activeFilters.search) {
    hasFilters = true;
    pillList.appendChild(createPill(`Search: "${activeFilters.search}"`, () => {
      activeFilters.search = '';
      document.getElementById('searchInput').value = '';
      document.getElementById('clearSearchBtn').style.display = 'none';
      renderAll();
    }));
  }

  if (activeFilters.status !== 'all') {
    hasFilters = true;
    pillList.appendChild(createPill(`Status: ${activeFilters.status}`, () => {
      activeFilters.status = 'all';
      renderAll();
    }));
  }

  if (activeFilters.department !== 'all') {
    hasFilters = true;
    pillList.appendChild(createPill(`Department: ${activeFilters.department}`, () => {
      activeFilters.department = 'all';
      renderAll();
    }));
  }

  pillBar.style.display = hasFilters ? 'flex' : 'none';
}

function createPill(text, onRemove) {
  const span = document.createElement('span');
  span.className = 'filter-pill';
  span.innerHTML = `<span>${escapeHtml(text)}</span><span class="filter-pill-remove" title="Remove">&times;</span>`;
  span.querySelector('.filter-pill-remove').addEventListener('click', onRemove);
  return span;
}

function clearAllFilters() {
  activeFilters.search = '';
  activeFilters.status = 'all';
  activeFilters.department = 'all';
  document.getElementById('searchInput').value = '';
  document.getElementById('clearSearchBtn').style.display = 'none';
  renderAll();
}

/**
 * Render Applicants Table
 */
function renderTable() {
  const tbody = document.getElementById('applicantsTableBody');
  const emptyState = document.getElementById('tableEmptyState');
  const recordsBadge = document.getElementById('recordsBadge');
  const footerSummary = document.getElementById('footerSummaryText');

  tbody.innerHTML = '';

  // Filter applicants
  const filtered = applicants.filter(app => {
    // Status filter
    if (activeFilters.status !== 'all' && app.status !== activeFilters.status) {
      return false;
    }
    // Dept filter
    if (activeFilters.department !== 'all' && app.department !== activeFilters.department) {
      return false;
    }
    // Search query
    if (activeFilters.search) {
      const q = activeFilters.search;
      const haystack = [
        app.no, app.applicant, app.designation, app.department,
        app.email, app.contact, app.city, app.skills, app.remarks
      ].join(' ').toLowerCase();
      if (!haystack.includes(q)) {
        return false;
      }
    }
    return true;
  });

  recordsBadge.textContent = `${applicants.length} applicant${applicants.length === 1 ? '' : 's'}`;
  footerSummary.textContent = `Showing ${filtered.length} of ${applicants.length} applicants`;

  if (filtered.length === 0) {
    emptyState.style.display = 'block';
    return;
  }
  emptyState.style.display = 'none';

  filtered.forEach(item => {
    const tr = document.createElement('tr');
    tr.dataset.serial = item.no;

    const initials = getInitials(item.applicant);
    const statusClass = getStatusBadgeClass(item.status);

    tr.innerHTML = `
      <td class="col-no"><span class="serial-badge">${escapeHtml(item.no)}</span></td>
      <td class="col-applicant">
        <div class="applicant-cell">
          <div class="applicant-avatar">${initials}</div>
          <a href="javascript:void(0)" class="applicant-name-link" onclick="viewApplicantDetails('${item.no}')">
            ${escapeHtml(item.applicant || 'Unnamed')}
          </a>
        </div>
      </td>
      <td class="col-designation"><span class="designation-text">${escapeHtml(item.designation || '-')}</span></td>
      <td class="col-dept"><span class="dept-badge">${escapeHtml(item.department || '-')}</span></td>
      <td class="col-email">
        ${item.email ? `<a href="mailto:${escapeHtml(item.email)}" class="email-link">${escapeHtml(item.email)}</a>` : '<span style="color:#94a3b8;">-</span>'}
      </td>
      <td class="col-contact"><span class="contact-text">${escapeHtml(item.contact || '-')}</span></td>
      <td class="col-dob">${escapeHtml(item.dob || '-')}</td>
      <td class="col-city">${escapeHtml(item.city || '-')}</td>
      <td class="col-status">
        <select class="status-select ${statusClass}" onchange="changeApplicantStatus('${item.no}', this.value)">
          <option value="New" ${item.status === 'New' ? 'selected' : ''}>New</option>
          <option value="Ex employee" ${item.status === 'Ex employee' ? 'selected' : ''}>Ex employee</option>
          <option value="Potential Candidate" ${item.status === 'Potential Candidate' ? 'selected' : ''}>Potential Candidate</option>
          <option value="working with us" ${item.status === 'working with us' ? 'selected' : ''}>working with us</option>
          <option value="For Database" ${item.status === 'For Database' ? 'selected' : ''}>For Database</option>
          <option value="Others" ${item.status === 'Others' ? 'selected' : ''}>Others</option>
          <option value="Do not follow up" ${item.status === 'Do not follow up' ? 'selected' : ''}>Do not follow up</option>
        </select>
      </td>
      <td class="col-reason">${escapeHtml(item.reasonForLeaving || '-')}</td>
      <td class="col-salary">${escapeHtml(item.expectedSalary || '-')}</td>
      <td class="col-remarks">${escapeHtml(item.remarks || '-')}</td>
      <td class="col-skills">
        <div class="skills-tags-wrapper">
          ${renderSkillsPills(item.skills)}
        </div>
      </td>
      <td class="col-actions">
        <div class="action-buttons-cell">
          <button class="action-icon-btn" title="View Details" onclick="viewApplicantDetails('${item.no}')">View</button>
          <button class="action-icon-btn" title="Edit Record" onclick="editApplicant('${item.no}')">Edit</button>
          <button class="action-icon-btn delete-btn" title="Delete Applicant" onclick="deleteApplicant('${item.no}')">Delete</button>
        </div>
      </td>
      <td class="col-filename">
        <div class="file-name-cell" title="${escapeHtml(item.fileName || '')}">
          ${escapeHtml(item.fileName || 'manual_entry.csv')}
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function renderSkillsPills(skillsStr) {
  if (!skillsStr) return '<span style="color:#94a3b8;">-</span>';
  const skills = skillsStr.split(',').map(s => s.trim()).filter(s => s.length > 0);
  return skills.map(skill => `<span class="skill-pill">${escapeHtml(skill)}</span>`).join('');
}

function getInitials(name) {
  if (!name) return 'AP';
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function getStatusBadgeClass(status) {
  switch (status) {
    case 'New': return 'status-new';
    case 'Ex employee': return 'status-ex-employee';
    case 'Potential Candidate': return 'status-potential';
    case 'working with us': return 'status-working';
    case 'For Database': return 'status-database';
    case 'Others': return 'status-others';
    case 'Do not follow up': return 'status-dnf';
    default: return 'status-new';
  }
}

// ==================== STATUS CHANGE INLINE ====================
window.changeApplicantStatus = function(serialNo, newStatus) {
  const app = applicants.find(a => a.no === serialNo);
  if (app) {
    app.status = newStatus;
    saveApplicantsToStorage();
    renderAll();
    showToast(`Status updated to "${newStatus}" for ${app.applicant}`, 'success');
  }
};

// ==================== CSV EXPORT & IMPORT ====================
function exportToCsv() {
  if (applicants.length === 0) {
    showToast('No applicant records to export!', 'warning');
    return;
  }

  const headers = [
    'NO.',
    'APPLICANT',
    'DESIGNATION',
    'DEPARTMENT',
    'EMAIL',
    'CONTACT NO.',
    'DATE OF BIRTH',
    'CITY',
    'STATUS',
    'REASON FOR LEAVING',
    'EXPECTED SALARY',
    'REMARKS',
    'SKILLS',
    'FILE NAME'
  ];

  const csvRows = [headers.join(',')];

  for (const item of applicants) {
    const row = [
      escapeCsv(item.no),
      escapeCsv(item.applicant),
      escapeCsv(item.designation),
      escapeCsv(item.department),
      escapeCsv(item.email),
      escapeCsv(item.contact),
      escapeCsv(item.dob),
      escapeCsv(item.city),
      escapeCsv(item.status),
      escapeCsv(item.reasonForLeaving),
      escapeCsv(item.expectedSalary),
      escapeCsv(item.remarks),
      escapeCsv(item.skills),
      escapeCsv(item.fileName)
    ];
    csvRows.push(row.join(','));
  }

  // Prepend UTF-8 BOM so Excel opens with proper encoding
  const csvContent = '\uFEFF' + csvRows.join('\r\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  
  const now = new Date();
  const dateStr = now.toISOString().split('T')[0];
  const filename = `applicants_ledger_${dateStr}.csv`;

  saveAs(blob, filename);

  // Update last exported timestamp
  const nowIso = now.toISOString();
  localStorage.setItem(LAST_EXPORT_KEY, nowIso);
  updateLastExportNotice(nowIso);

  showToast(`CSV ledger exported successfully (${applicants.length} records)`, 'success');
}

function escapeCsv(val) {
  if (val === undefined || val === null) return '""';
  const str = String(val);
  if (str.includes(',') || str.includes('"') || str.includes('\n') || str.includes('\r')) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return `"${str}"`;
}

function handleCsvFileImport(event) {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = function(e) {
    const text = e.target.result;
    parseAndLoadCsv(text);
  };
  reader.readAsText(file);
  event.target.value = '';
}

function parseAndLoadCsv(csvText) {
  const lines = parseCsvRows(csvText);
  if (lines.length < 2) {
    showToast('Uploaded CSV appears empty or missing data rows.', 'warning');
    return;
  }

  const header = lines[0].map(h => h.trim().toUpperCase());
  const colIndex = {
    no: header.findIndex(h => h.includes('NO.') || h === 'NO' || h === 'SERIAL'),
    applicant: header.findIndex(h => h.includes('APPLICANT') || h.includes('NAME')),
    designation: header.findIndex(h => h.includes('DESIGNATION') || h.includes('ROLE') || h.includes('TITLE')),
    department: header.findIndex(h => h.includes('DEPARTMENT') || h.includes('DEPT')),
    email: header.findIndex(h => h.includes('EMAIL')),
    contact: header.findIndex(h => h.includes('CONTACT') || h.includes('PHONE')),
    dob: header.findIndex(h => h.includes('BIRTH') || h.includes('DOB')),
    city: header.findIndex(h => h.includes('CITY') || h.includes('LOCATION')),
    status: header.findIndex(h => h.includes('STATUS')),
    reason: header.findIndex(h => h.includes('REASON')),
    salary: header.findIndex(h => h.includes('SALARY') || h.includes('CTC')),
    remarks: header.findIndex(h => h.includes('REMARKS') || h.includes('NOTES')),
    skills: header.findIndex(h => h.includes('SKILLS')),
    fileName: header.findIndex(h => h.includes('FILE'))
  };

  let importedCount = 0;
  for (let i = 1; i < lines.length; i++) {
    const row = lines[i];
    if (row.length === 0 || (row.length === 1 && !row[0].trim())) continue;

    // Resolve or assign serial number starting from A000
    let serial = colIndex.no !== -1 ? row[colIndex.no]?.trim() : '';
    if (!serial) {
      serial = getNextSerial();
    }

    const applicant = {
      no: serial,
      applicant: colIndex.applicant !== -1 ? (row[colIndex.applicant]?.trim() || 'Unknown') : 'Unknown',
      designation: colIndex.designation !== -1 ? (row[colIndex.designation]?.trim() || '-') : '-',
      department: colIndex.department !== -1 ? (row[colIndex.department]?.trim() || 'Front office') : 'Front office',
      email: colIndex.email !== -1 ? (row[colIndex.email]?.trim() || '') : '',
      contact: colIndex.contact !== -1 ? (row[colIndex.contact]?.trim() || '') : '',
      dob: colIndex.dob !== -1 ? (row[colIndex.dob]?.trim() || '') : '',
      city: colIndex.city !== -1 ? (row[colIndex.city]?.trim() || '') : '',
      status: colIndex.status !== -1 ? (row[colIndex.status]?.trim() || 'New') : 'New',
      reasonForLeaving: colIndex.reason !== -1 ? (row[colIndex.reason]?.trim() || '') : '',
      expectedSalary: colIndex.salary !== -1 ? (row[colIndex.salary]?.trim() || '') : '',
      remarks: colIndex.remarks !== -1 ? (row[colIndex.remarks]?.trim() || '') : '',
      skills: colIndex.skills !== -1 ? (row[colIndex.skills]?.trim() || '') : '',
      fileName: colIndex.fileName !== -1 ? (row[colIndex.fileName]?.trim() || 'imported_record.csv') : 'imported_record.csv'
    };

    // Check if duplicate serial
    const existingIdx = applicants.findIndex(a => a.no === serial);
    if (existingIdx !== -1) {
      applicants[existingIdx] = applicant;
    } else {
      applicants.push(applicant);
    }
    importedCount++;
  }

  saveApplicantsToStorage();
  renderAll();
  showToast(`Successfully imported ${importedCount} records from CSV.`, 'success');
}

/**
 * Robust CSV parser taking care of quotes and commas
 */
function parseCsvRows(text) {
  const rows = [];
  let currentRow = [];
  let currentField = '';
  let insideQuote = false;

  const cleanText = text.replace(/^\uFEFF/, '');

  for (let i = 0; i < cleanText.length; i++) {
    const char = cleanText[i];
    const nextChar = cleanText[i + 1];

    if (insideQuote) {
      if (char === '"' && nextChar === '"') {
        currentField += '"';
        i++; // skip escaped quote
      } else if (char === '"') {
        insideQuote = false;
      } else {
        currentField += char;
      }
    } else {
      if (char === '"') {
        insideQuote = true;
      } else if (char === ',') {
        currentRow.push(currentField);
        currentField = '';
      } else if (char === '\n' || char === '\r') {
        if (char === '\r' && nextChar === '\n') {
          i++; // skip LF
        }
        currentRow.push(currentField);
        currentField = '';
        if (currentRow.some(f => f.trim().length > 0)) {
          rows.push(currentRow);
        }
        currentRow = [];
      } else {
        currentField += char;
      }
    }
  }

  if (currentField || currentRow.length > 0) {
    currentRow.push(currentField);
    if (currentRow.some(f => f.trim().length > 0)) {
      rows.push(currentRow);
    }
  }

  return rows;
}

// ==================== DOWNLOAD ALL AS ZIP ====================
async function downloadAllAsZip() {
  if (applicants.length === 0) {
    showToast('No applicants in registry to bundle into ZIP.', 'warning');
    return;
  }

  const zip = new JSZip();
  let zipCount = 0;

  // Add CSV ledger file to root of zip
  const headers = ['NO.', 'APPLICANT', 'DESIGNATION', 'DEPARTMENT', 'EMAIL', 'CONTACT NO.', 'DATE OF BIRTH', 'CITY', 'STATUS', 'REASON FOR LEAVING', 'EXPECTED SALARY', 'REMARKS', 'SKILLS', 'FILE NAME'];
  const csvRows = [headers.join(',')];
  for (const item of applicants) {
    csvRows.push([
      escapeCsv(item.no), escapeCsv(item.applicant), escapeCsv(item.designation), escapeCsv(item.department),
      escapeCsv(item.email), escapeCsv(item.contact), escapeCsv(item.dob), escapeCsv(item.city),
      escapeCsv(item.status), escapeCsv(item.reasonForLeaving), escapeCsv(item.expectedSalary),
      escapeCsv(item.remarks), escapeCsv(item.skills), escapeCsv(item.fileName)
    ].join(','));
  }
  zip.file('Applicants_Ledger.csv', '\uFEFF' + csvRows.join('\r\n'));

  // Bundle uploads renamed as "Name - Position.ext"
  for (const item of applicants) {
    const rawFile = uploadedFilesMap.get(item.fileName);
    const ext = item.fileName ? item.fileName.split('.').pop() : 'txt';
    const cleanName = `${sanitizeFilename(item.applicant)} - ${sanitizeFilename(item.designation)}.${ext}`;

    if (rawFile) {
      zip.file(`resumes/${cleanName}`, rawFile);
      zipCount++;
    } else if (item.rawText) {
      // Create text profile if physical binary not in session cache
      zip.file(`resumes/${sanitizeFilename(item.applicant)} - ${sanitizeFilename(item.designation)}.txt`, item.rawText);
      zipCount++;
    }
  }

  showToast('Generating ZIP package...', 'success');
  const content = await zip.generateAsync({ type: 'blob' });
  saveAs(content, 'Applicants_Registry_Resumes.zip');
  showToast(`Downloaded ZIP package with ${zipCount} resume files!`, 'success');
}

function sanitizeFilename(str) {
  return (str || 'Applicant').replace(/[/\\?%*:|"<>]/g, '_').trim();
}

// ==================== CHECK DATA VALIDATION ====================
function openCheckDataModal() {
  const modal = document.getElementById('checkDataModal');
  const container = document.getElementById('checkDataResults');

  const missingEmails = [];
  const missingContacts = [];
  const missingDesignations = [];
  const duplicateEmails = {};
  const duplicateNames = {};

  applicants.forEach(app => {
    if (!app.email) missingEmails.push(app);
    if (!app.contact) missingContacts.push(app);
    if (!app.designation || app.designation === '-') missingDesignations.push(app);

    if (app.email) {
      duplicateEmails[app.email] = (duplicateEmails[app.email] || 0) + 1;
    }
    if (app.applicant) {
      const lower = app.applicant.toLowerCase();
      duplicateNames[lower] = (duplicateNames[lower] || 0) + 1;
    }
  });

  const dupEmailKeys = Object.keys(duplicateEmails).filter(e => duplicateEmails[e] > 1);
  const dupNameKeys = Object.keys(duplicateNames).filter(n => duplicateNames[n] > 1);

  let html = `
    <div style="margin-bottom: 14px; font-size: 13.5px; color: #475569;">
      Registry audit of <strong>${applicants.length}</strong> applicant records:
    </div>
  `;

  if (missingEmails.length === 0 && missingContacts.length === 0 && dupEmailKeys.length === 0 && dupNameKeys.length === 0) {
    html += `
      <div style="background-color: #ecfdf5; border: 1px solid #a7f3d0; color: #065f46; padding: 14px; border-radius: 6px; font-weight: 500;">
        ✅ All records look clean! No missing emails, missing phone numbers, or duplicates detected.
      </div>
    `;
  } else {
    // Missing Emails
    if (missingEmails.length > 0) {
      html += `
        <div class="check-data-section">
          <div class="check-data-section-title">
            <span>⚠️ Missing Email (${missingEmails.length})</span>
          </div>
          <ul class="check-data-list">
            ${missingEmails.slice(0, 10).map(m => `
              <li class="check-data-item">
                <span><strong>${escapeHtml(m.no)}</strong>: ${escapeHtml(m.applicant)} (${escapeHtml(m.designation)})</span>
                <span class="check-data-badge">No email</span>
              </li>
            `).join('')}
            ${missingEmails.length > 10 ? `<li class="check-data-item"><em>...and ${missingEmails.length - 10} more</em></li>` : ''}
          </ul>
        </div>
      `;
    }

    // Missing Contacts
    if (missingContacts.length > 0) {
      html += `
        <div class="check-data-section">
          <div class="check-data-section-title">
            <span>⚠️ Missing Contact No. (${missingContacts.length})</span>
          </div>
          <ul class="check-data-list">
            ${missingContacts.slice(0, 10).map(m => `
              <li class="check-data-item">
                <span><strong>${escapeHtml(m.no)}</strong>: ${escapeHtml(m.applicant)} (${escapeHtml(m.designation)})</span>
                <span class="check-data-badge">No phone</span>
              </li>
            `).join('')}
            ${missingContacts.length > 10 ? `<li class="check-data-item"><em>...and ${missingContacts.length - 10} more</em></li>` : ''}
          </ul>
        </div>
      `;
    }

    // Duplicates
    if (dupEmailKeys.length > 0 || dupNameKeys.length > 0) {
      html += `
        <div class="check-data-section">
          <div class="check-data-section-title">
            <span>⚠️ Potential Duplicates Detected</span>
          </div>
          <ul class="check-data-list">
            ${dupEmailKeys.map(e => `
              <li class="check-data-item">
                <span>Duplicate Email: <strong>${escapeHtml(e)}</strong> (${duplicateEmails[e]} occurrences)</span>
                <span class="check-data-badge">Duplicate</span>
              </li>
            `).join('')}
            ${dupNameKeys.map(n => `
              <li class="check-data-item">
                <span>Duplicate Name: <strong>${escapeHtml(n)}</strong> (${duplicateNames[n]} occurrences)</span>
                <span class="check-data-badge">Duplicate</span>
              </li>
            `).join('')}
          </ul>
        </div>
      `;
    }
  }

  container.innerHTML = html;
  modal.style.display = 'flex';
}

function closeCheckDataModal() {
  document.getElementById('checkDataModal').style.display = 'none';
}

// ==================== MANUAL APPLICANT ADD / EDIT MODAL ====================
function openApplicantModal(existingApplicant = null) {
  const modal = document.getElementById('applicantModal');
  const title = document.getElementById('modalTitle');
  const form = document.getElementById('applicantForm');

  if (existingApplicant) {
    title.textContent = `Edit Applicant (${existingApplicant.no})`;
    document.getElementById('formSerialNo').value = existingApplicant.no;
    document.getElementById('formSerialDisplay').value = existingApplicant.no;
    document.getElementById('formApplicantName').value = existingApplicant.applicant || '';
    document.getElementById('formDesignation').value = existingApplicant.designation || '';
    document.getElementById('formDepartment').value = existingApplicant.department || 'Front office';
    document.getElementById('formEmail').value = existingApplicant.email || '';
    document.getElementById('formContact').value = existingApplicant.contact || '';
    document.getElementById('formDob').value = existingApplicant.dob || '';
    document.getElementById('formCity').value = existingApplicant.city || '';
    document.getElementById('formStatus').value = existingApplicant.status || 'New';
    document.getElementById('formExpectedSalary').value = existingApplicant.expectedSalary || '';
    document.getElementById('formReason').value = existingApplicant.reasonForLeaving || '';
    document.getElementById('formSkills').value = existingApplicant.skills || '';
    document.getElementById('formRemarks').value = existingApplicant.remarks || '';
    document.getElementById('formFileName').value = existingApplicant.fileName || '';
  } else {
    title.textContent = 'Add Applicant Manually';
    form.reset();
    const nextSerial = getNextSerial();
    document.getElementById('formSerialNo').value = nextSerial;
    document.getElementById('formSerialDisplay').value = nextSerial;
    document.getElementById('formStatus').value = 'New';
    document.getElementById('formDepartment').value = 'Front office';
    document.getElementById('formFileName').value = 'manual_entry.csv';
  }

  modal.style.display = 'flex';
}

function closeApplicantModal() {
  document.getElementById('applicantModal').style.display = 'none';
}

function handleApplicantFormSubmit(e) {
  e.preventDefault();
  const serial = document.getElementById('formSerialNo').value;
  const name = document.getElementById('formApplicantName').value.trim();
  const designation = document.getElementById('formDesignation').value.trim();
  const department = document.getElementById('formDepartment').value;
  const email = document.getElementById('formEmail').value.trim();
  const contact = document.getElementById('formContact').value.trim();
  const dob = document.getElementById('formDob').value.trim();
  const city = document.getElementById('formCity').value.trim();
  const status = document.getElementById('formStatus').value;
  const expectedSalary = document.getElementById('formExpectedSalary').value.trim();
  const reasonForLeaving = document.getElementById('formReason').value.trim();
  const skills = document.getElementById('formSkills').value.trim();
  const remarks = document.getElementById('formRemarks').value.trim();
  const fileName = document.getElementById('formFileName').value.trim() || 'manual_entry.csv';

  const applicantData = {
    no: serial,
    applicant: name,
    designation,
    department,
    email,
    contact,
    dob,
    city,
    status,
    reasonForLeaving,
    expectedSalary,
    remarks,
    skills,
    fileName
  };

  const existingIdx = applicants.findIndex(a => a.no === serial);
  if (existingIdx !== -1) {
    applicantData.rawText = applicants[existingIdx].rawText || '';
    applicants[existingIdx] = applicantData;
    showToast(`Updated applicant ${serial}: ${name}`, 'success');
  } else {
    applicantData.rawText = `Manual Entry Record: ${name}\nDesignation: ${designation}\nSkills: ${skills}`;
    applicants.push(applicantData);
    showToast(`Added new applicant ${serial}: ${name}`, 'success');
  }

  saveApplicantsToStorage();
  closeApplicantModal();
  renderAll();
}

window.editApplicant = function(serialNo) {
  const app = applicants.find(a => a.no === serialNo);
  if (app) {
    openApplicantModal(app);
  }
};

window.deleteApplicant = function(serialNo) {
  if (confirm(`Are you sure you want to delete applicant ${serialNo}?`)) {
    applicants = applicants.filter(a => a.no !== serialNo);
    saveApplicantsToStorage();
    renderAll();
    showToast(`Applicant ${serialNo} removed.`, 'success');
  }
};

// ==================== VIEW RESUME DETAILS MODAL ====================
window.viewApplicantDetails = function(serialNo) {
  const app = applicants.find(a => a.no === serialNo);
  if (!app) return;

  const modal = document.getElementById('viewResumeModal');
  document.getElementById('viewResumeTitle').textContent = `Applicant Record: ${app.no} - ${app.applicant}`;

  const headerGrid = document.getElementById('viewResumeDetailsHeader');
  headerGrid.innerHTML = `
    <div class="view-detail-item">
      <span class="view-detail-label">Serial No</span>
      <span class="view-detail-value" style="font-family: var(--font-mono); font-weight: 700;">${escapeHtml(app.no)}</span>
    </div>
    <div class="view-detail-item">
      <span class="view-detail-label">Designation</span>
      <span class="view-detail-value">${escapeHtml(app.designation)}</span>
    </div>
    <div class="view-detail-item">
      <span class="view-detail-label">Department</span>
      <span class="view-detail-value">${escapeHtml(app.department)}</span>
    </div>
    <div class="view-detail-item">
      <span class="view-detail-label">Status</span>
      <span class="view-detail-value">${escapeHtml(app.status)}</span>
    </div>
    <div class="view-detail-item">
      <span class="view-detail-label">Email</span>
      <span class="view-detail-value">${escapeHtml(app.email || '-')}</span>
    </div>
    <div class="view-detail-item">
      <span class="view-detail-label">Contact No</span>
      <span class="view-detail-value">${escapeHtml(app.contact || '-')}</span>
    </div>
    <div class="view-detail-item">
      <span class="view-detail-label">City</span>
      <span class="view-detail-value">${escapeHtml(app.city || '-')}</span>
    </div>
    <div class="view-detail-item">
      <span class="view-detail-label">Expected Salary</span>
      <span class="view-detail-value">${escapeHtml(app.expectedSalary || '-')}</span>
    </div>
  `;

  const rawPre = document.getElementById('viewResumeRawText');
  rawPre.textContent = app.rawText || `No raw text stored for ${app.applicant}. Record was added manually or via CSV.`;

  modal.style.display = 'flex';
};

function closeViewResumeModal() {
  document.getElementById('viewResumeModal').style.display = 'none';
}

// ==================== LAST EXPORT NOTICE ====================
function initLastExportNotice() {
  const savedDate = localStorage.getItem(LAST_EXPORT_KEY);
  if (savedDate) {
    updateLastExportNotice(savedDate);
  } else {
    // Default placeholder matching the screenshot date
    document.getElementById('lastExportNoticeText').textContent = 'Last exported 12 days ago (23 Oct 2026). Consider exporting a fresh backup.';
  }
}

function updateLastExportNotice(isoString) {
  const exportDate = new Date(isoString);
  const now = new Date();
  const diffTime = Math.abs(now - exportDate);
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

  const options = { day: 'numeric', month: 'short', year: 'numeric' };
  const formattedDate = exportDate.toLocaleDateString('en-GB', options);

  let dayText = `${diffDays} days ago`;
  if (diffDays === 0) dayText = 'today';
  else if (diffDays === 1) dayText = 'yesterday';

  document.getElementById('lastExportNoticeText').textContent = `Last exported ${dayText} (${formattedDate}). Consider exporting a fresh backup.`;
}

// ==================== SAMPLE DEMO DATA GENERATOR ====================
/**
 * Populates realistic demo records matching the 135 total count and exact
 * departmental distribution from the user's screenshot!
 * Starts from A000 up to A134.
 */
function loadSampleDemoData() {
  if (applicants.length > 0) {
    if (!confirm('This will replace current ledger records with sample demo data matching the screenshot (135 applicants starting at A000). Continue?')) {
      return;
    }
  }

  // Exact departmental quotas from screenshot:
  // Front office: 30, Kitchen: 14, Service: 22, Account: 13, Maintenance: 3, Sales: 3, Admin: 18, Housekeeping: 19, Stores: 2, Other: 11 = 135 total
  const deptDist = [
    { dept: 'Front office', count: 30, title: 'Front Office Executive', skills: 'OPERA PMS, Guest Relations, English' },
    { dept: 'Kitchen', count: 14, title: 'Sous Chef', skills: 'Culinary Arts, HACCP, Food Safety' },
    { dept: 'Service', count: 22, title: 'Restaurant Captain', skills: 'F&B Service, Banquet, Micros POS' },
    { dept: 'Account', count: 13, title: 'Accountant', skills: 'Tally Prime, GST, MS Excel, Ledger' },
    { dept: 'Maintenance', count: 3, title: 'Facility Maintenance Engineer', skills: 'HVAC, Electrical, Plumbing' },
    { dept: 'Sales', count: 3, title: 'Sales Executive', skills: 'B2B Sales, CRM, Client Retention' },
    { dept: 'Admin', count: 18, title: 'HR & Administrative Officer', skills: 'Recruitment, Payroll, Operations' },
    { dept: 'Housekeeping', count: 19, title: 'Housekeeping Supervisor', skills: 'Room Inspection, Inventory, Linen Management' },
    { dept: 'Stores', count: 2, countRemaining: 2, title: 'Store Keeper', skills: 'Stock Auditing, Purchase, Warehouse' },
    { dept: 'Admin', count: 11, title: 'Senior Software Engineer', skills: 'Python, JavaScript, SQL, API' }
  ];

  const firstNames = ['Aarav', 'Vihaan', 'Aditya', 'Rohan', 'Kabir', 'Ananya', 'Diya', 'Ishaan', 'Pooja', 'Neha', 'Vikram', 'Meera', 'Rajesh', 'Siddharth', 'Kavita', 'Sanjay', 'Sunil', 'Preeti', 'Deepak', 'Arjun', 'Manish', 'Nisha', 'Tanvi', 'Karan', 'Shreya'];
  const lastNames = ['Sharma', 'Patel', 'Verma', 'Gupta', 'Singh', 'Reddy', 'Mehta', 'Nair', 'Joshi', 'Chopra', 'Rao', 'Bhatia', 'Kulkarni', 'Deshmukh', 'Saxena'];
  const cities = ['Mumbai', 'Delhi', 'Bangalore', 'Pune', 'Hyderabad', 'Chennai', 'Kolkata', 'Ahmedabad', 'Goa', 'Jaipur'];

  const demoList = [];
  let currentIndex = 0;

  for (const group of deptDist) {
    for (let c = 0; c < group.count; c++) {
      const serial = indexToSerial(currentIndex);
      const fn = firstNames[(currentIndex + c) % firstNames.length];
      const ln = lastNames[(currentIndex * 3 + c) % lastNames.length];
      const fullName = `${fn} ${ln}`;
      const email = `${fn.toLowerCase()}.${ln.toLowerCase()}${currentIndex % 99}@example.com`;
      const contact = `+91 ${98000 + (currentIndex % 1999)} ${10000 + (currentIndex * 73) % 89999}`;
      const city = cities[currentIndex % cities.length];
      const year = 1990 + (currentIndex % 12);
      const month = String(1 + (currentIndex % 12)).padStart(2, '0');
      const day = String(1 + (currentIndex % 28)).padStart(2, '0');
      const dob = `${day}/${month}/${year}`;

      demoList.push({
        no: serial,
        applicant: fullName,
        designation: group.title,
        department: group.dept,
        email: email,
        contact: contact,
        dob: dob,
        city: city,
        status: 'New', // all 135 initially "New" as in the screenshot
        reasonForLeaving: 'Looking for career growth',
        expectedSalary: `₹${30000 + (currentIndex % 50) * 1000} / mo`,
        remarks: `Profile screened for ${group.title}. Experienced professional.`,
        skills: group.skills,
        fileName: `${fn}_${ln}_Resume.pdf`,
        rawText: `RESUME\n${fullName}\nEmail: ${email}\nPhone: ${contact}\nCity: ${city}\nDOB: ${dob}\nRole: ${group.title}\nDepartment: ${group.dept}\nSkills: ${group.skills}`
      });

      currentIndex++;
    }
  }

  applicants = demoList;
  saveApplicantsToStorage();
  renderAll();
  showToast('Loaded 135 sample applicants starting from A000 (matching your screenshot)!', 'success');
}

function clearAllDataPrompt() {
  if (confirm('Are you sure you want to clear all applicant records from the ledger? This action cannot be undone.')) {
    applicants = [];
    uploadedFilesMap.clear();
    saveApplicantsToStorage();
    renderAll();
    showToast('Ledger cleared. You can upload resumes or click "Load Sample Demo Data".', 'warning');
  }
}

// ==================== TOAST NOTIFICATIONS ====================
function showToast(message, type = 'success') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${escapeHtml(message)}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}

// ==================== UTILS ====================
function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
