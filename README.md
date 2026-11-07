# RouteWise — Disruption-Aware Journey Planner

A beginner-friendly full-stack demo that replans a journey when a transport connection is delayed or cancelled.

**Important:** This version uses fictional, simulated transport data inspired by a city network. It does not use live train/bus/metro feeds.

## Features
- Origin, destination, departure time, arrival deadline, budget, and maximum walking inputs
- Fastest, cheapest, and balanced route options
- Simulated delays and cancellations
- Replanning after disruption
- Explanation of route trade-offs
- React + Vite frontend and FastAPI backend

## Requirements
- Python 3.10+
- Node.js 20+ (LTS recommended)
- VS Code

## Run locally

### 1. Start the backend
Open Terminal in VS Code, then:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Windows PowerShell activation:
```powershell
.venv\Scripts\Activate.ps1
```

Backend API: http://127.0.0.1:8000  
Interactive API docs: http://127.0.0.1:8000/docs

### 2. Start the frontend
Open a **second terminal** in VS Code:

```bash
cd frontend
npm install
npm run dev
```

Open the URL Vite prints, usually http://localhost:5173.

## Deploy live (free-tier availability/pricing can change)

### Backend: Render
1. Push this folder to a GitHub repository.
2. In Render, create a **New Web Service** and connect the repository.
3. Set **Root Directory** to `backend`.
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Deploy and copy the public backend URL, e.g. `https://your-service.onrender.com`.

### Frontend: Vercel
1. In Vercel, import the same GitHub repository.
2. Set **Root Directory** to `frontend`.
3. Add environment variable:
   `VITE_API_URL=https://your-service.onrender.com`
   (replace with your actual backend URL; do not include a trailing slash)
4. Build command: `npm run build`
5. Output directory: `dist`
6. Deploy.

### CORS after deployment
The backend permits all origins for this student demo. For a public production app, restrict `allow_origins` in `backend/app/main.py` to your deployed frontend URL.

## Demo scenarios
1. Fastest route: choose Central Station → Tech Park.
2. Click **Simulate disruption** to cancel a connection or add a delay.
3. Click **Find routes** to compare available alternatives.
4. Try a tight budget or arrival deadline to see constraints affect results.

## Limitations and future improvements
- Simulated timetable, fares, walking links, and disruptions
- No authentication, persistence, live transit feeds, GTFS ingestion, or real map matching
- Schedule model is intentionally simplified for a student prototype
- Before using real-world data, verify licensing, reliability, and service terms
