<div align="center">

```
 █████╗ ███████╗ ██████╗██╗██╗███████╗██╗   ██╗
██╔══██╗██╔════╝██╔════╝██║██║██╔════╝╚██╗ ██╔╝
███████║███████╗██║     ██║██║█████╗   ╚████╔╝ 
██╔══██║╚════██║██║     ██║██║██╔══╝    ╚██╔╝  
██║  ██║███████║╚██████╗██║██║██║        ██║   
╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝╚═╝╚═╝        ╚═╝  
```

**Turn any video into ASCII art — in seconds.**

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?style=flat-square&logo=fastapi&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-4.9+-5C3EE8?style=flat-square&logo=opencv&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-00ff9d?style=flat-square)

</div>

---

## Apa itu ASCIIfy?

**ASCIIfy** adalah web app yang mengubah video biasa menjadi **ASCII art video** — video yang tersusun dari karakter teks berwarna, menghasilkan estetika visual yang unik dan keren. Perfect untuk konten kreator, video editor, dan siapapun yang ingin memberikan sentuhan artistik berbeda pada videonya.

### Fitur Utama

- 🎨 **Mode Berwarna** — ASCII art dengan warna asli dari video
- ⬜ **Mode Monokrom** — Estetika klasik hitam putih
- ⚡ **4 Level Resolusi** — 80 / 100 / 120 / 150 karakter per baris
- 🎬 **Pilihan FPS** — 10 / 15 / 24 / 30 fps output
- 📥 **Download MP4** — Hasil langsung bisa didownload dan dipakai
- 🖥️ **Preview Real-time** — Lihat hasilnya langsung di browser sebelum download

---

## Demo

```
@@@@@@@@####SSSSS%%%???***+++;;;:::,,,....
@@@@####SSSS%%%???***+++;;;:::,,,....     
####SSSS%%%???***+++;;;:::,,,....         
  .,;+*?%S#@@@####SS%%??**++;;::,,..      
      .,:;+*?%S##@@@@###SS%%??*+;;:,.     
           .,;+*?%SS##@@@###S%%?*+;:.     
                .,;+*?%S##@@@@##S%?+      
```

---

## Cara Menjalankan (Lokal)

### Syarat
- Python 3.8 ke atas
- Git

### Langkah 1 — Clone repository

```bash
git clone https://github.com/NAMA_KAMU/asciify.git
cd asciify
```

### Langkah 2 — Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Langkah 3 — Jalankan server

```bash
python -m uvicorn main:app --reload --port 8000
```

### Langkah 4 — Buka browser

```
http://localhost:8000
```

> Jangan tutup terminal selama menggunakan website!

---

## Cara Pakai

| Langkah | Aksi |
|---|---|
| 1 | Upload video (drag & drop atau klik Pilih File) |
| 2 | Pilih resolusi, mode warna, dan FPS |
| 3 | Klik **Mulai Konversi** dan tunggu proses selesai |
| 4 | Preview muncul → klik **Download MP4** |

---

## Batasan

| | Batas |
|---|---|
| ⏱️ Durasi video | Maksimal 30 detik |
| 📦 Ukuran file | Maksimal 100MB |
| 🎞️ Format input | MP4, MOV, AVI, WebM |
| 💾 Format output | MP4 (H.264) |

---

## Estimasi Waktu Proses

| Resolusi | 15 detik | 30 detik |
|---|---|---|
| 80 chars | ~30 dtk | ~1 menit |
| 100 chars | ~1 menit | ~2 menit |
| 120 chars | ~2 menit | ~3-4 menit |
| 150 chars | ~3 menit | ~5-6 menit |

> 💡 **Sweet spot terbaik:** Resolusi 100 + 15fps

---

## Struktur Proyek

```
asciify/
├── backend/
│   ├── main.py          ← Server FastAPI
│   ├── converter.py     ← Engine konversi ASCII
│   ├── requirements.txt
│   └── temp/            ← File sementara (auto-created)
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
├── render.yaml          ← Konfigurasi Render.com
├── railway.json         ← Konfigurasi Railway.app
├── Procfile
└── README.md
```

---

## Deploy ke Cloud (Gratis)

### Render.com

1. Login di [render.com](https://render.com) pakai akun GitHub
2. **New +** → **Web Service** → pilih repo `asciify`
3. Isi konfigurasi:

| Field | Value |
|---|---|
| Runtime | Python 3 |
| Build Command | `pip install -r backend/requirements.txt` |
| Start Command | `cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT` |

4. Klik **Create Web Service** → tunggu build selesai
5. Update `const API` di `frontend/js/app.js` dengan URL Render kamu

### Railway.app

1. Login di [railway.app](https://railway.app) pakai akun GitHub
2. **New Project** → **Deploy from GitHub repo** → pilih `asciify`
3. Otomatis terbaca dari `railway.json`
4. **Settings** → **Networking** → **Generate Domain**

---

## Troubleshooting

**Tampilan CSS tidak muncul**
→ Buka via `http://localhost:8000` bukan double-click file HTML

**Error saat upload video**
→ Pastikan folder `backend/temp/uploads` dan `backend/temp/outputs` ada

**`uvicorn` tidak dikenal**
→ Pakai `python -m uvicorn` bukan `uvicorn` langsung

**Preview video kosong**
→ Pastikan `converter.py` sudah menggunakan codec `avc1`

---

## Tech Stack

| Layer | Teknologi |
|---|---|
| Backend | Python, FastAPI, Uvicorn |
| Processing | OpenCV, NumPy |
| Frontend | HTML, CSS, Vanilla JS |
| Font | Share Tech Mono, Syne |

---

<div align="center">

Made with ☕ and too many ASCII characters

</div>