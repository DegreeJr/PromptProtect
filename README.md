# Singkap AI

**LLM Prompt Injection Defense Middleware** — HackNusa 2026, Track 2 (AI vs AI: Cyber Defense).

Singkap AI melindungi aplikasi berbasis LLM dari serangan *indirect prompt injection* dengan dua lapis pertahanan:

1. **Spotlighting preprocessing** — menandai konten tak terpercaya dengan delimiter + datamarking agar LLM hilir dapat membedakan data dari instruksi.
2. **Injection classifier** — RoBERTa yang di-*fine-tune* pada dataset **BIPIA**, di-*hosting* di HuggingFace Hub, dimuat via `transformers` pipeline.

> Model di-training di **Kaggle** dan akan dipublikasikan ke HuggingFace Hub. Per Juli 2026 model **belum tersedia (masih training)**, sehingga classifier saat ini masih **mock heuristik**. Mesin lokal hanya menjalankan backend + frontend (inference nantinya dimuat dari Hub).

## Arsitektur

```
React + Vite + Tailwind  ──/api/analyze──▶  FastAPI + Uvicorn
                                                 │
                                    Layer 1: spotlight()  (services/spotlight.py)
                                    Layer 2: classify()   (services/classifier.py)
                                                 │
                                    RoBERTa @ HuggingFace Hub (inference)
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
