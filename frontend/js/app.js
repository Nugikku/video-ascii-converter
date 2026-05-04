// =============================================
//   ASCIIfy — Frontend App Logic
// =============================================

const API = 'http://localhost:8000';

// State
let currentJobId = null;
let pollTimer = null;
let settings = {
  char_width: 100,
  colored: true,
  output_fps: 15,
};

// ── DOM refs ──
const uploadZone   = document.getElementById('uploadZone');
const fileInput    = document.getElementById('fileInput');
const fileInfo     = document.getElementById('fileInfo');
const fileName     = document.getElementById('fileName');
const fileMeta     = document.getElementById('fileMeta');
const btnRemove    = document.getElementById('btnRemove');
const btnConvert   = document.getElementById('btnConvert');
const progressCont = document.getElementById('progressContainer');
const progressBar  = document.getElementById('progressBar');
const progressPct  = document.getElementById('progressPct');
const progressStat = document.getElementById('progressStatus');
const progressLog  = document.getElementById('progressLog');
const stepResult   = document.getElementById('step-result');
const resultVideo  = document.getElementById('resultVideo');
const resultStats  = document.getElementById('resultStats');
const btnDownload  = document.getElementById('btnDownload');
const btnReset     = document.getElementById('btnReset');
const toast        = document.getElementById('toast');
const toastMsg     = document.getElementById('toastMsg');

// ── Upload Zone ──
uploadZone.addEventListener('click', () => fileInput.click());

uploadZone.addEventListener('dragover', e => {
  e.preventDefault();
  uploadZone.classList.add('dragover');
});

uploadZone.addEventListener('dragleave', () => {
  uploadZone.classList.remove('dragover');
});

uploadZone.addEventListener('drop', e => {
  e.preventDefault();
  uploadZone.classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  if (file) handleFile(file);
});

fileInput.addEventListener('change', e => {
  if (e.target.files[0]) handleFile(e.target.files[0]);
});

btnRemove.addEventListener('click', () => {
  resetFileUI();
});

function handleFile(file) {
  const allowed = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/webm'];
  if (!allowed.includes(file.type)) {
    showToast('Format tidak didukung. Gunakan MP4, MOV, AVI, atau WebM.');
    return;
  }

  if (file.size > 100 * 1024 * 1024) {
    showToast('File terlalu besar. Maksimal 100MB.');
    return;
  }

  // Preview metadata via video element
  const tempURL = URL.createObjectURL(file);
  const tempVid = document.createElement('video');
  tempVid.src = tempURL;
  tempVid.onloadedmetadata = () => {
    const dur = tempVid.duration;
    if (dur > 30) {
      showToast(`Durasi video ${dur.toFixed(0)} detik. Maksimal 30 detik.`);
      URL.revokeObjectURL(tempURL);
      return;
    }
    const sizeMB = (file.size / 1024 / 1024).toFixed(1);
    fileName.textContent = file.name;
    fileMeta.textContent = `${dur.toFixed(1)}s · ${sizeMB} MB · ${file.type.split('/')[1].toUpperCase()}`;

    uploadZone.classList.add('hidden');
    fileInfo.classList.remove('hidden');
    btnConvert.disabled = false;

    // Simpan file ke state untuk upload nanti
    fileInput._selectedFile = file;
    URL.revokeObjectURL(tempURL);
  };
}

function resetFileUI() {
  fileInput.value = '';
  fileInput._selectedFile = null;
  fileInfo.classList.add('hidden');
  uploadZone.classList.remove('hidden');
  btnConvert.disabled = true;
  currentJobId = null;
  clearInterval(pollTimer);
  progressCont.classList.add('hidden');
  progressBar.style.width = '0%';
  progressPct.textContent = '0%';
}

// ── Settings ──
document.getElementById('settingWidth').addEventListener('click', e => {
  const btn = e.target.closest('.btn-choice');
  if (!btn) return;
  document.querySelectorAll('#settingWidth .btn-choice').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  settings.char_width = parseInt(btn.dataset.val);
});

document.getElementById('settingColor').addEventListener('click', e => {
  const btn = e.target.closest('.btn-choice');
  if (!btn) return;
  document.querySelectorAll('#settingColor .btn-choice').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  settings.colored = btn.dataset.val === 'true';
});

document.getElementById('settingFps').addEventListener('click', e => {
  const btn = e.target.closest('.btn-choice');
  if (!btn) return;
  document.querySelectorAll('#settingFps .btn-choice').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  settings.output_fps = parseInt(btn.dataset.val);
});

// ── Convert ──
btnConvert.addEventListener('click', async () => {
  const file = fileInput._selectedFile;
  if (!file) return;

  btnConvert.disabled = true;
  btnConvert.querySelector('.btn-convert-text').textContent = '⏳ Mengupload...';
  progressCont.classList.remove('hidden');
  stepResult.classList.add('hidden');
  setProgress(0, 'Mengupload video...');
  logMsg('Upload dimulai...');

  try {
    // 1. Upload
    const formData = new FormData();
    formData.append('file', file);
    const uploadRes = await fetch(`${API}/api/upload`, { method: 'POST', body: formData });
    const uploadData = await uploadRes.json();

    if (!uploadRes.ok) {
      throw new Error(uploadData.detail || 'Upload gagal');
    }

    currentJobId = uploadData.job_id;
    setProgress(10, 'Upload berhasil, memulai konversi...');
    logMsg('✓ Upload selesai. Job ID: ' + currentJobId.slice(0, 8) + '...');

    // 2. Start conversion
    btnConvert.querySelector('.btn-convert-text').textContent = '⚙️ Memproses...';
    const convRes = await fetch(
      `${API}/api/convert-settings/${currentJobId}?char_width=${settings.char_width}&colored=${settings.colored}&output_fps=${settings.output_fps}`,
      { method: 'POST' }
    );
    const convData = await convRes.json();

    if (!convRes.ok) {
      throw new Error(convData.detail || 'Konversi gagal dimulai');
    }

    logMsg(`⚙️  Konversi dimulai... (${settings.char_width} chars, ${settings.colored ? 'berwarna' : 'mono'}, ${settings.output_fps}fps)`);

    // 3. Poll status
    pollTimer = setInterval(pollStatus, 1000);

  } catch (err) {
    showToast(err.message);
    btnConvert.disabled = false;
    btnConvert.querySelector('.btn-convert-text').textContent = '▶ Mulai Konversi';
    setProgress(0, 'Error.');
  }
});

async function pollStatus() {
  if (!currentJobId) return;

  try {
    const res = await fetch(`${API}/api/status/${currentJobId}`);
    const data = await res.json();

    if (data.status === 'processing') {
      const pct = Math.max(10, data.progress);
      setProgress(pct, `Memproses frame... ${pct}%`);

    } else if (data.status === 'done') {
      clearInterval(pollTimer);
      setProgress(100, 'Selesai! ✓');
      logMsg('✓ Konversi berhasil!');
      showResult();

    } else if (data.status === 'error') {
      clearInterval(pollTimer);
      showToast('Error: ' + data.error);
      btnConvert.disabled = false;
      btnConvert.querySelector('.btn-convert-text').textContent = '▶ Mulai Konversi';
    }
  } catch (e) {
    // Network error, coba lagi
  }
}

function setProgress(pct, status) {
  progressBar.style.width = pct + '%';
  progressPct.textContent = pct + '%';
  progressStat.textContent = status;
}

function logMsg(msg) {
  progressLog.innerHTML += `<span>${msg}</span><br>`;
}

async function showResult() {
  btnConvert.querySelector('.btn-convert-text').textContent = '▶ Mulai Konversi';
  btnConvert.disabled = false;

  const videoURL = `${API}/api/stream/${currentJobId}`;

  resultVideo.src = videoURL;
  resultVideo.load();

  resultStats.innerHTML = `
    <div><strong>Resolusi</strong>: ${settings.char_width} chars</div>
    <div><strong>Mode</strong>: ${settings.colored ? 'Berwarna' : 'Monokrom'}</div>
    <div><strong>Output FPS</strong>: ${settings.output_fps}</div>
    <div><strong>Status</strong>: <strong>✓ Siap</strong></div>
  `;

  stepResult.classList.remove('hidden');
  stepResult.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ── Download ──
btnDownload.addEventListener('click', () => {
  if (!currentJobId) return;
  const a = document.createElement('a');
  a.href = `${API}/api/download/${currentJobId}`;
  const baseName = (fileInput._selectedFile?.name || 'video').replace(/\.[^.]+$/, '');
  a.download = `${baseName}_ascii.mp4`;
  a.click();
});

// ── Reset ──
btnReset.addEventListener('click', async () => {
  // Cleanup job di server
  if (currentJobId) {
    try {
      await fetch(`${API}/api/cleanup/${currentJobId}`, { method: 'DELETE' });
    } catch (e) {}
  }
  resetFileUI();
  stepResult.classList.add('hidden');
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

// ── Toast ──
let toastTimer = null;
function showToast(msg) {
  toastMsg.textContent = msg;
  toast.classList.remove('hidden');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.add('hidden'), 4000);
}
