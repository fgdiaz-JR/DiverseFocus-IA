# 🧠 DiverseFocus-IA

> **An AI-powered, accessible learning platform built for neurodivergent learners.**
> DiverseFocus-IA uses Gemini Pro and OpenAI Whisper to simplify complex text, transcribe audio,
> and generate visual learning aids — all wrapped in a calm, low-stimulation interface designed
> for people with ADHD, Dyslexia, and Autism Spectrum Disorder.

[![CI/CD](https://github.com/fgdiaz-jr/diversefocus-ia/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/fgdiaz-jr/diversefocus-ia/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg)](https://fastapi.tiangolo.com)

---

## 📋 Table of Contents

- [Mission](#-mission)
- [Architecture](#-architecture)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Service Reference](#-service-reference)
- [MLOps Pipeline](#-mlops-pipeline)
- [Mobile App](#-mobile-app)
- [Kubernetes Deployment](#-kubernetes-deployment)
- [Secret Management](#-secret-management)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Mission

Neurodivergent learners—estimated at **15–20% of the global population**—often struggle with
dense text, audio-only content, and visually overwhelming interfaces. DiverseFocus-IA aims to
remove those barriers with AI that adapts content to the learner, not the other way around.

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Mobile App (React Native)                │
│                    iOS / Android — DiverseFocus IA              │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTPS / REST
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Gateway  :8000                           │
│          JWT Auth · Rate Limiting · CORS · Proxy                │
└──────┬─────────────────┬──────────────────┬────────────────────┘
       │                 │                  │
       ▼                 ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ AI Inference │  │ Voice/Video  │  │ User Profile │
│    :8001     │  │    :8002     │  │    :8003     │
│              │  │              │  │              │
│ Gemini Pro   │  │   Whisper    │  │  SQLite DB   │
│ Simplify     │  │  Transcribe  │  │  Profiles    │
│ Summarise    │  │  yt-dlp      │  │  Task Hist.  │
│ Visual Aids  │  │              │  │              │
└──────────────┘  └──────────────┘  └──────────────┘

         ┌──────────────────────────────────┐
         │        MLOps Pipeline            │
         │  DVC · Transformers · MLflow     │
         │  T5 fine-tuning · BLEU/ROUGE     │
         └──────────────────────────────────┘

         ┌──────────────────────────────────┐
         │     Kubernetes (k8s/)            │
         │  Namespace · Deployments         │
         │  Services · PVC · Ingress + TLS  │
         └──────────────────────────────────┘
```

---

## ✨ Features

| Feature | Description |
|---|---|
| 📖 **Text Simplification** | Rewrites complex content at Easy / Medium / Advanced levels |
| 🎙️ **Audio Transcription** | Whisper-powered transcription of uploaded audio files |
| 🎥 **Video Transcription** | Extract and transcribe audio from YouTube/Vimeo links |
| 🗺️ **Visual Mind-Maps** | AI-generated structured data for interactive concept diagrams |
| 📋 **Video Summarisation** | Key points, glossary, and quiz questions from any video |
| 📱 **Mobile App** | Calm, accessible React Native app for iOS and Android |
| 🔐 **JWT Auth** | Secure, stateless authentication across all services |
| 🚦 **Rate Limiting** | Per-IP throttling on all API routes |
| 🤖 **MLOps Pipeline** | DVC + MLflow for reproducible model training and versioning |
| ☸️ **Kubernetes Ready** | Full k8s manifests with health probes and secret injection |

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | FastAPI 0.111 + Uvicorn |
| **AI / ML** | Google Gemini Pro, OpenAI Whisper, Hugging Face Transformers (T5) |
| **Authentication** | python-jose (JWT) + passlib (bcrypt) |
| **Database** | SQLite + SQLAlchemy async + aiosqlite |
| **Video Download** | yt-dlp + ffmpeg |
| **MLOps** | DVC, MLflow, PyTorch, datasets, sacrebleu, rouge-score |
| **Mobile** | React Native 0.74, React Navigation, Axios, AsyncStorage |
| **Infrastructure** | Docker, Docker Compose, Kubernetes, GitHub Actions |
| **Registry** | GitHub Container Registry (ghcr.io) |

---

## 🚀 Quick Start

### Prerequisites

- Docker ≥ 24 and Docker Compose ≥ 2
- A [Google AI Studio](https://aistudio.google.com/app/apikey) API key
- Git

### 1. Clone the repository

```bash
git clone https://github.com/fgdiaz-jr/diversefocus-ia.git
cd diversefocus-ia
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env and fill in your GEMINI_API_KEY and JWT_SECRET
nano .env
```

### 3. Start all services

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| API Gateway | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| AI Inference | http://localhost:8001/docs |
| Voice/Video | http://localhost:8002/docs |
| User Profile | http://localhost:8003/docs |

### 4. Test the API

```bash
# Log in (demo user)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "demo1234"}'

# Simplify text (replace TOKEN with the access_token from above)
curl -X POST http://localhost:8000/api/v1/ai/simplify \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "The mitochondria is the organelle responsible for ATP synthesis.", "level": "easy"}'
```

---

## 📡 Service Reference

### API Gateway (`/api/v1`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/login` | Obtain a JWT token |
| `POST` | `/ai/simplify` | Simplify text (proxied → ai-inference) |
| `POST` | `/ai/transcribe` | Transcribe audio (proxied → voice-video) |
| `GET` | `/user/profile` | Get current user profile |
| `PUT` | `/user/profile` | Update profile and preferences |
| `POST` | `/user/tasks` | Create a task record |
| `GET` | `/user/tasks` | Get task history |
| `GET` | `/health` | Gateway health check |

### AI Inference (internal, port 8001)

| Method | Path | Body |
|---|---|---|
| `POST` | `/simplify` | `{"text": str, "level": "easy\|medium\|advanced"}` |
| `POST` | `/summarize-video` | `{"transcript": str}` |
| `POST` | `/generate-visual-aid` | `{"concept": str}` |

### Voice/Video (internal, port 8002)

| Method | Path | Body |
|---|---|---|
| `POST` | `/transcribe` | `multipart/form-data` with `file` field |
| `POST` | `/extract-video-transcript` | `{"video_url": str}` |

### User Profile (internal, port 8003)

| Method | Path | Description |
|---|---|---|
| `GET` | `/profile/{user_id}` | Get profile (auto-creates on first access) |
| `PUT` | `/profile/{user_id}` | Update username, email, preferences |
| `POST` | `/tasks` | Create task record |
| `GET` | `/tasks/{user_id}` | List task history |

---

## 🤖 MLOps Pipeline

The `mlops/` directory contains a full DVC pipeline for fine-tuning a T5 model on
neurodivergent-friendly text simplification.

```
mlops/
├── dvc.yaml              # Pipeline definition
├── .dvcignore
├── requirements.txt
└── scripts/
    ├── prepare_data.py   # Data cleaning & train/val/test split
    ├── train_model.py    # T5 fine-tuning with MLflow logging
    └── evaluate_model.py # BLEU + ROUGE evaluation
```

### Run the pipeline

```bash
cd mlops
pip install -r requirements.txt

# Start MLflow UI (in background)
mlflow ui &

# Run the full DVC pipeline
dvc repro

# View metrics
dvc metrics show
```

### Tracked by MLflow

- Hyperparameters: base model, epochs, batch size, learning rate
- Metrics: training loss, BLEU score, ROUGE-1/2/L
- Artifact: serialised model registered as `diversefocus-simplification`

---

## 📱 Mobile App

```
mobile/
├── package.json
└── src/
    ├── App.tsx                   # Navigation root
    ├── config/index.ts           # API base URL
    ├── services/api.ts           # Typed API client (Axios)
    └── screens/
        ├── HomeScreen.tsx        # Calm landing with feature cards
        ├── SimplifyScreen.tsx    # Text simplification with level picker
        ├── TranscribeScreen.tsx  # Audio upload + transcript + simplify
        └── ProfileScreen.tsx     # Profile and accessibility prefs
```

### Run locally

```bash
cd mobile
npm install
npm start         # Metro bundler
npm run android   # Android device/emulator
npm run ios       # iOS simulator (macOS only)
```

### Accessibility design principles

- Soft, low-saturation colour palette (no harsh reds/oranges)
- Large touch targets and generous line heights
- Every interactive element has `accessibilityLabel` and `accessibilityRole`
- `AccessibilityInfo.announceForAccessibility` for screen-reader feedback

---

## ☸️ Kubernetes Deployment

```bash
# 1. Apply namespace
kubectl apply -f k8s/namespace.yaml

# 2. Create secrets (fill in real values first)
kubectl create secret generic diversefocus-secrets \
  --namespace diversefocus \
  --from-literal=GEMINI_API_KEY=<your-key> \
  --from-literal=JWT_SECRET=$(openssl rand -hex 32) \
  --from-literal=WHISPER_MODEL=base \
  --from-literal=AI_INFERENCE_URL=http://ai-inference:8001 \
  --from-literal=VOICE_VIDEO_URL=http://voice-video:8002 \
  --from-literal=USER_PROFILE_URL=http://user-profile:8003

# 3. Apply all manifests
kubectl apply -f k8s/

# 4. Check rollout status
kubectl rollout status deployment/api-gateway -n diversefocus
kubectl rollout status deployment/ai-inference -n diversefocus

# 5. Access the gateway
kubectl get svc api-gateway -n diversefocus
```

### TLS / Ingress

The `k8s/ingress.yaml` uses **cert-manager** with a Let's Encrypt `ClusterIssuer`.
Install cert-manager first:

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/latest/download/cert-manager.yaml
```

---

## 🔐 Secret Management

**Never commit real secrets to source control.**

| Variable | Description | How to generate |
|---|---|---|
| `GEMINI_API_KEY` | Google AI Studio key | https://aistudio.google.com/app/apikey |
| `JWT_SECRET` | JWT signing secret | `openssl rand -hex 32` |
| `WHISPER_MODEL` | Whisper model size | `tiny` / `base` / `small` / `medium` / `large` |

**Recommended secret stores:**
- Local dev: `.env` file (gitignored)
- CI/CD: GitHub Actions Secrets (`Settings → Secrets → Actions`)
- Kubernetes: Sealed Secrets or External Secrets Operator
- Production: AWS Secrets Manager, HashiCorp Vault, or GCP Secret Manager

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/amazing-feature`
3. Make your changes and add tests
4. Run the test suite: `cd services/<service> && pytest tests/ -v`
5. Commit with a descriptive message
6. Push and open a Pull Request

Please follow [PEP 8](https://peps.python.org/pep-0008/) for Python and
[Conventional Commits](https://www.conventionalcommits.org) for commit messages.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Built with ❤️ for neurodivergent learners everywhere.
</p>