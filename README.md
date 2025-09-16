
# OppWinProb CRUD (FastAPI + Streamlit, SQLite, no JWT)

This package contains a ready-to-run **CRUD application** connected to a **win probability calculator**.
- **DB:** SQLite (file: `backend/app.db`)
- **Auth:** Simple session (no JWT). Streamlit calls a FastAPI `/auth/login` check.
- **Integration:** The Streamlit app reads/writes directly to the same DB through the API.
- **Seeded user:** `admin` / `admin123`

## 1) Prerequisites
- Python 3.10+ installed
- A terminal (PowerShell or Command Prompt on Windows)

## 2) Create & Activate a Virtual Environment
```bash
cd OppWinProbCRUD
python -m venv .venv
# Windows PowerShell
. .venv\Scripts\Activate.ps1
# Windows CMD
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

## 3) Install Dependencies
```bash
pip install -r requirements.txt
```

## 4) Start the Backend (FastAPI)
```bash
cd backend
uvicorn main:app --reload
```
FastAPI runs at **http://127.0.0.1:8000**  
Interactive API docs: **http://127.0.0.1:8000/docs**

> The first run will create `app.db` and seed the default user (`admin` / `admin123`) and example data.

## 5) Start the Frontend (Streamlit)
Open a second terminal (keep the backend running), then:
```bash
cd OppWinProbCRUD/frontend
streamlit run app.py
```
Streamlit runs at the URL it prints (usually **http://localhost:8501**).

## 6) Tester Walkthrough

### A) Log in
- Username: `admin`
- Password: `admin123`

### B) Divisions CRUD
- Go to the **Divisions** tab.
- **Create**: enter a division name and optional weight modifier.
- **Read**: existing rows appear in a table.
- **Update**: select a row, edit values, save.
- **Delete**: pick a row and delete.

### C) Decision Makers CRUD
- Go to **Decision Makers** tab.
- **Create**: add name, role, and your assessment score (0–100).
- **Update/Delete** similarly.

### D) Win Probability Calculator
- Select a **Division** and a **Decision Maker**.
- Optionally enter extra context weights (budget fit, timeline fit).
- Click **Calculate** to see the final OppWinProb value.
- Click **Save Result** to store the calculation record.

### E) Verify Persistence
- Refresh the Streamlit app—your entries remain.
- Use FastAPI docs to **GET** `/divisions`, `/decision_makers`, `/calculations` to verify a JSON view.

## 7) Resetting
To reset the app to a clean slate, stop the backend, delete `backend/app.db`, and restart the backend to re-seed demo data.

## 8) File Map
```
OppWinProbCRUD/
├─ backend/
│  ├─ main.py
│  ├─ database.py
│  ├─ models.py
│  ├─ schemas.py
│  ├─ seed.py
│  └─ app.db        # created on first run
├─ frontend/
│  └─ app.py
├─ data/
│  ├─ decision_makers.csv  # sample data
│  └─ divisions.csv        # sample data
└─ requirements.txt
```

## 9) Notes
- This is a starter template you can adapt to your production needs (swap out SQLite for Postgres by changing the DB URL in `database.py`).
- No JWT: Streamlit keeps a simple session flag from the `/auth/login` check.
- CORS is open for localhost use.
