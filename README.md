# PromptProtect

**LLM Prompt Injection Defense Middleware** — HackNusa 2026, Track 2 (AI vs AI: Cyber Defense).

PromptProtect melindungi aplikasi berbasis LLM dari serangan *prompt injection* dengan **tiga komponen pertahanan** yang saling melengkapi:

1. **Spotlighting (provenance)** — menandai konten tak terpercaya dengan delimiter + datamarking (`<<UNTRUSTED_DATA>>`) agar LLM hilir dapat membedakan data dari instruksi. Ini lapis *provenance*, bukan detektor.
2. **ML classifier (indirect injection)** — RoBERTa (`DegreeJr/promptprotect-roberta`) yang di-*fine-tune* pada dataset **BIPIA**, di-*hosting* di HuggingFace Hub, dimuat via `transformers` pipeline. Kuat mendeteksi *indirect prompt injection* (perintah jahat yang tertanam di konten eksternal, mis. eksfiltrasi data).
3. **Heuristic layer (direct jailbreak)** — daftar pola regex (`services/jailbreak_heuristic.py`) untuk frasa jailbreak *langsung* dalam Bahasa Inggris & Indonesia (mis. "ignore all previous instructions", "you are now DAN", "abaikan instruksi sebelumnya").

> **Kenapa perlu komponen ke-3?** Distribusi data training BIPIA berfokus pada *indirect* prompt injection, sehingga model ML punya *blind spot*: jailbreak langsung generik seperti "Ignore all previous instructions" atau "You are now DAN" konsisten di-skor **benign** dengan keyakinan tinggi (terverifikasi lewat audit). Layer heuristik menutup gap distribusi ini secara deterministik. Kedua detektor digabung dengan **logika OR** — bila salah satu menandai konten sebagai injeksi, verdict akhir = injeksi.

## Arsitektur

```
React + Vite + Tailwind  ──/api/analyze──▶  FastAPI + Uvicorn
                                                 │
                        Layer 1: spotlight()          (services/spotlight.py)   — provenance
                        Layer 2: classify()  ┐        (services/classifier.py)  — indirect injection (ML)
                        Layer 3: detect()    ┴─ OR ─▶ (services/jailbreak_heuristic.py) — direct jailbreak (regex)
                                                 │
                        detection_source: ml_model | heuristic_pattern | both | none
```

## Struktur folder

```
backend/     FastAPI app (app/api, app/core, app/models, app/services)
frontend/    React + Vite + Tailwind CSS
ml/          notebook, script, data, model (training di Colab)
docs/        dokumentasi
```

## Menjalankan

### Backend
```bash
# dari root proyek
venv\Scripts\activate              # Windows PowerShell: venv\Scripts\Activate.ps1
cd backend
uvicorn app.main:app --reload --port 8000
```
- Health: `GET http://127.0.0.1:8000/health`
- Analyze: `POST http://127.0.0.1:8000/api/analyze` body `{"content": "..."}`
- Stats: `GET http://127.0.0.1:8000/api/stats` — analitik agregat (total, blocked, breakdown per sumber, rata-rata confidence/latency)
- Logs: `GET http://127.0.0.1:8000/api/logs?limit=50&offset=0` — audit trail request terakhir

### Analytics & Audit Log
Setiap panggilan `/api/analyze` dicatat ke SQLite (`backend/promptprotect.db`, via SQLAlchemy):
timestamp, preview input (dipotong 200 char) + hash SHA-256 (privacy-safe), verdict,
confidence, `detection_source`, dan latency. Frontend menyediakan tab **Dashboard**
(kartu statistik, bar chart breakdown sumber deteksi, dan tabel audit log).

### Frontend
```bash
cd frontend
npm install
npm run dev        # http://localhost:5173  (proxy /api -> :8000)
```

## Konfigurasi
Salin `backend/.env.example` ke `backend/.env` dan isi:
- `GROQ_API_KEY` — untuk demo LLM (Groq, gratis)
- `HF_MODEL_ID` — id model RoBERTa di HuggingFace Hub
