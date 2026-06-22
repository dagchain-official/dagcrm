# DAGOS CRM

Full-stack CRM platform.

- **Frontend** — React (Vite) + TailwindCSS, modern dashboard UI
- **Main API** — Django + Django REST Framework (CRM, HR, Finance, etc.) + JWT auth
- **AI Service** — FastAPI (lead scoring, insights, assistant)
- **Database** — PostgreSQL

```
dagos/
├── backend/      # Django + DRF  -> http://localhost:8000
├── ai-service/   # FastAPI       -> http://localhost:8100
├── frontend/     # React + Vite  -> http://localhost:5173
└── docker-compose.yml
```

## Quick start (Docker)

```bash
docker compose up --build
```

- Frontend:  http://localhost:5173
- DRF API:   http://localhost:8000/api/
- DRF docs:  http://localhost:8000/api/docs/
- AI API:    http://localhost:8100/docs

Default login (after seed): **admin@dagos.com / admin123**

## Manual dev setup

### Backend (Django/DRF)
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # win: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed          # demo data + admin user
python manage.py runserver
```

### AI service (FastAPI)
```bash
cd ai-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8100
```

### Frontend (React)
```bash
cd frontend
npm install
npm run dev
```

## Modules
Auth & Permissions · Users · Business/Products · Leads · Lead Activities ·
Opportunities · Customer 360 · Revenue/Sales · Targets · Support Desk ·
Communications · HR · Attendance · Employee Activity · Leaves · Payroll ·
Incentives · Finance · Reports · AI Layer
