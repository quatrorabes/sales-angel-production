# Sales Angel - Production Sales Automation Platform

## Structure

```
sales-angel-production/
├── database/          # Database operations + ML models
├── enrichment/        # Contact profiling + scoring
├── content/           # Email + call generation
├── automation/        # Sequences + LinkedIn
├── analytics/         # KPIs + ROI
├── api/               # FastAPI endpoints
├── config/            # Configuration
├── tests/             # Testing
├── api/main.py        # Main application (run this)
├── requirements.txt   # Dependencies
└── .env               # Environment variables
```

## Quick Start

### 1. Setup
```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
```

### 2. Update .env
Edit `.env` with your API keys

### 3. Run Locally
```bash
python -m uvicorn api.main:app --reload --port 8000
```

### 4. View Docs
Open: http://localhost:8000/docs

### 5. Deploy to Heroku
```bash
heroku create sales-angel-prod
heroku addons:create heroku-postgresql:hobby-dev
git push heroku main
```

## Endpoints

- `GET /health` - Health check
- `GET /system` - System status
- `POST /api/enrichment/single` - Enrich contact
- `POST /api/content/email` - Generate email
- `POST /api/automation/sequence` - Start sequence
- `GET /api/analytics/dashboard` - Dashboard metrics

## Swagger UI

All endpoints documented at `/docs` when running locally

## Production Deployment

```bash
heroku create sales-angel-prod
heroku addons:create heroku-postgresql:hobby-dev
heroku config:set ENVIRONMENT=production
git push heroku main
```

## Status

✅ Production ready
✅ All 42 modules organized
✅ API fully integrated
✅ Ready for customers

---
Created: 2025-11-13 00:40:02
