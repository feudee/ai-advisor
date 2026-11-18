# AI-Enabled Student Advising Assistant

Review 3 MVP for CSS7102. It demonstrates a student profile, sample course catalog, NetworkX prerequisite DAG, deterministic eligibility and ranking, multi-semester pathway planning, optional Claude explanations, and advisor approval.

## Problem and objectives

Students and advisors must combine course history, interests, career goals, prerequisites, and credit limits when planning future terms. This pilot stores those inputs in SQLite, blocks unsafe course choices using deterministic graph rules, ranks the eligible courses transparently, generates a short credit-capped pathway, explains the result, and records an advisor decision. The sample curriculum is illustrative and is not an official degree audit.

## Tech stack

React.js, Vite, Tailwind CSS, Python, FastAPI, NetworkX, SQLite, SQLAlchemy, Claude API (optional), pytest.

## Project structure

```text
backend/app/{main.py,database.py,models.py,schemas.py,routers/,services/}
backend/tests/{conftest.py,test_algorithms.py,test_api.py}
backend/seed.py
frontend/src/{App.jsx,main.jsx,services.js,style.css}
docs/{algorithms.md,architecture.md}
README.md
.env.example
```

## Windows 11 setup

Open the `review3-mvp` folder in VS Code. Open two PowerShell terminals with that folder as the working directory. If you extracted the supplied project into the Codex workspace, the folder is:

```text
C:\Users\91819\Documents\Codex\2026-09-25\files-mentioned-by-the-user-css7102\review3-mvp
```

### Backend and database

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python seed.py
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`; interactive API docs are at `http://localhost:8000/docs`. SQLite database is `backend/advising.db`. The seed script is safe to rerun and inserts/updates the demo catalog and student. Python 3.11 or newer is supported; use `python --version` to check the installed version. The plain `python -m venv` command uses the installed Python, so it also works when the Python 3.11 launcher alias is unavailable.

The SQLite schema includes `students`, `student_completed_courses`, `student_interests`, `courses`, `prerequisites`, and `pathway_plans`.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Node.js 18+ and Python 3.11+ are recommended.

### Environment / Claude

Copy `.env.example` to `backend/.env`, set `ANTHROPIC_API_KEY`, and optionally adjust `CLAUDE_MODEL` or `ADVISOR_WEIGHTS`. The backend loads this file automatically when started from the `backend` folder. You can also set values directly in PowerShell before starting it:

```powershell
$env:ANTHROPIC_API_KEY="your-key"
uvicorn app.main:app --reload
```

The key is never stored in source code. If absent or the API fails, the advisor uses its deterministic fallback.

Recommendation weights can be customized with `ADVISOR_WEIGHTS`, a JSON object containing all five factors. Values are normalized to sum to 1. For example:

```powershell
$env:ADVISOR_WEIGHTS='{"interest":0.4,"career":0.25,"academic":0.15,"progression":0.1,"semester":0.1}'
```

## API overview

- `GET /api/students`, `GET /api/students/{id}`, `PUT /api/students/{id}`
- `GET /api/courses`, `GET /api/courses/{course_code}`, `GET /api/graph`, `GET /api/graph/{course_code}`
- `GET /api/eligibility/{student_id}`, `GET /api/recommendations/{student_id}`
- `POST /api/pathway/{student_id}`
- `POST /api/chat`
- `GET /api/advisor`, `POST /api/advisor/{plan_id}/review`

## Tests

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest -q
```

The tests cover satisfied/missing prerequisites, completed-course and credit filtering, deterministic ranking, configurable weights, pathway ordering/credits, cycle detection, course/prerequisite lookup, and the live advising-to-approval API flow.

## Review 3 demo

Use the 5–10 minute script in [docs/architecture.md](docs/architecture.md#review-3-demo-procedure-5-10-minutes). The seeded profile is Prabuddha P (`20231CAI0155`), semester 5, GPA 3.6, with Python, Linear Algebra, Data Structures, Probability, Database Systems, and Algorithms completed.

## Algorithms and architecture

See [docs/algorithms.md](docs/algorithms.md) for objectives, inputs/outputs, pseudocode, complexity, examples, and the end-to-end flowchart. See [docs/architecture.md](docs/architecture.md) for the draft report content and viva Q&A.

See [docs/runtime-architecture.md](docs/runtime-architecture.md) for the high-level runtime diagram and request flow.

## Main demo flow

Open the dashboard, review the seeded profile, inspect eligible and blocked courses, compare their ranking scores, trace a prerequisite chain in the graph, generate a pathway, ask the AI Advisor “Why is Machine Learning recommended?”, then approve the saved plan in Advisor Review. With no Claude key configured, the explanation uses the local fallback.

## Free online deployment

Suggested student-demo hosting: Render Static Site for the React frontend, Render Free Web Service for FastAPI, and Neon Free Postgres for data. The app uses SQLite locally and switches to PostgreSQL when `DATABASE_URL` is set. Do not use SQLite for the deployed backend: free Render services have temporary local filesystems. Render's free PostgreSQL service expires after 30 days; Neon Free is a better fit for a continuing class demo, within its free usage limits. Free Render backends sleep when inactive and can take about a minute to wake. This configuration is suitable for a school demo, not real student records or production advising.

1. Put the contents of `review3-mvp` in a GitHub repository. Keep `.env`, API keys, and database files out of the repository.
2. Create a Neon project and copy its PostgreSQL connection string. In Neon, keep the connection string private.
3. In Render, create a **Web Service** from the repository with root directory `backend`, build command `pip install -r requirements.txt`, and start command `python seed.py && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Choose the Free instance.
4. Add `DATABASE_URL` in the Render API service settings using the Neon connection string. Add `CORS_ORIGINS` with your eventual frontend URL, for example `https://your-site.onrender.com`. Add `ANTHROPIC_API_KEY` only if you want Claude; the deterministic explanation works without it.
5. Create a Render **Static Site** from the same repository with root directory `frontend`, build command `npm install && npm run build`, and publish directory `dist`. Add the build environment variable `VITE_API_URL` with the API URL ending in `/api`, for example `https://your-api.onrender.com/api`.
6. After the frontend gets its Render URL, update the API service's `CORS_ORIGINS` to that exact URL and redeploy the API. Open the frontend URL and try profile, recommendations, pathway, advisor review, and chat.

The app has no login yet, so use only its sample data on the public URL. The `python seed.py` start step makes sure the demo profile and catalog exist when the API service starts.

## Limitations and future work

This is a pilot demo curriculum, not an official degree audit. Course availability is a boolean rather than section/seat data; the greedy planner creates at most four terms; there is no transcript import, authentication, full advisor change log, or guaranteed graduation optimization. Future work: validate the catalog with the department, add degree requirements and term-specific section constraints, persist review history, evaluate student feedback, and improve planning optimization.
