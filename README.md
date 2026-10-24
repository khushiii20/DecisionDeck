# DecisionDeck

> **Make choices with clarity.**  
> A transparent full-stack decision-support application that helps people compare alternatives using weighted criteria, practical constraints, numerical scores, and interactive simulation.

---

## 1. Project Overview

**DecisionDeck** is an interactive web application designed to help individuals and teams navigate complex trade-offs without cognitive overload. Whether deciding between career paths, purchasing computing hardware, choosing job offers, or prioritizing project ideas, DecisionDeck brings transparency to decision-making.

### The Decision-Making Philosophy
- **Transparent Formula**: Option scores are calculated as $\sum \frac{\text{Weight}_i \times \text{Rating}_i}{100}$. Every input and mathematical contribution is visible.
- **Support, Not Certainty**: DecisionDeck helps users reason through trade-offs; it does **not** claim that a numerical score represents an objectively indisputable truth.
- **Hard Constraints vs. Soft Preferences**: Measurable requirements (e.g., maximum budget, minimum battery life) are checked *first* to determine eligibility before ranking alternatives.

---

## 2. Features Implemented

- **Weighted Criteria Evaluation**: Assign percentage weights totaling 100% and rate alternatives on a standardized 1–10 scale.
- **Hard Requirements & Eligibility Filtering**: Filter out alternatives that violate non-negotiable thresholds (`<=`, `>=`, `<`, `>`, `==`) with explicit human-readable disqualification notes.
- **Deterministic Tie Handling**: Alternatives with identical scores share the exact same rank and are flagged as tied.
- **Interactive What-if Simulator**: Dynamically adjust criteria weights using sliders to observe real-time rank shifts without overwriting saved data until explicitly chosen.
- **Predefined Decision Templates**: Jumpstart comparisons with 5 curated scenarios (Career Path, Laptop Hardware, Job Offer, Course Selection, Side Project Idea).
- **Relative Score Visualization**: Clean inline SVG score comparison charts with color-coded ranks and eligibility status.
- **RFC 4180-Compliant CSV Export**: Download complete decision matrices, ratings, calculated scores, and constraint notes for spreadsheet analysis.
- **Print-Friendly Report View**: Dedicated `@media print` styling removes navigation bars and buttons for clean PDF generation or physical printing.
- **Secure Authentication & User Data Isolation**: Salted password hashing with `bcrypt`, JWT access tokens, and strict database query filters preventing cross-user data leakage.
- **Responsive Dark-Mode Interface**: Built on a design system with accessible contrast, visible focus rings, and reduced-motion support.

---

## 3. Screenshots

> *To add screenshots to your repository, capture images of the running application, place them in a `docs/screenshots/` folder, and update the links below.*

| Landing Page | Decision Workspace |
|:---:|:---:|
| ![Landing Page Preview](docs/screenshots/landing_page.png) | ![Decision Workspace Preview](docs/screenshots/workspace.png) |
| *Hero, feature breakdown, and realistic example* | *Criteria editor, rating matrix, and What-if Simulator* |

---

## 4. Technology Stack

- **Frontend**:
  - Semantic HTML5 & Responsive CSS3 (CSS Flexbox, CSS Grid, Custom Design Tokens).
  - Vanilla JavaScript (ES6+) utilizing native `fetch()` API and DOM manipulation.
  - Zero heavy frontend frameworks or build steps required.
- **Backend**:
  - **Python 3.14** with **FastAPI** for high-performance asynchronous REST endpoints.
  - **Pydantic v2** for strict request/response data validation and serialization.
  - **SQLAlchemy 2.0** ORM for relational persistence and cascade deletes.
  - **Uvicorn** ASGI server.
  - **Bcrypt** and **PyJWT** for cryptographic password hashing and token generation.
- **Database**:
  - **SQLite** for zero-configuration local development.
  - **PostgreSQL (Supabase)** ready for cloud production via `DATABASE_URL`.
- **Testing**:
  - **Pytest** with 29 automated tests covering scoring calculations, validation rules, auth, and multi-user isolation.

---

## 5. Architecture Overview

DecisionDeck follows a clean 3-tier architectural pattern:

```
[ Frontend: HTML5 / CSS3 / Vanilla JS ]
                 ↕  JSON over HTTP (REST API)
[ Backend: FastAPI (Python 3.14) ]
   ├── Authentication & Security (bcrypt, JWT)
   ├── Scoring & Constraint Engine (Functional, Pure Math)
   └── SQLAlchemy 2.0 ORM
                 ↕  SQL Engine
[ Database: SQLite (Local) / Supabase PostgreSQL (Cloud) ]
```

### User Data Isolation
Every private decision, alternative, criterion, rating, and constraint is bound to the authenticated user ID (`user_id`). Route handlers explicitly filter by `Decision.user_id == current_user.id`, returning `404 Not Found` if an unauthorized user attempts to view, modify, calculate, export, or delete another user's decision.

---

## 6. Project Folder Structure

```
DecisionDeck/
├── app/
│   ├── __init__.py
│   ├── auth.py              # Bcrypt hashing, JWT creation & dependency injection
│   ├── database.py          # SQLAlchemy engine and session dependency
│   ├── main.py              # FastAPI application & static asset mounts
│   ├── models.py            # Relational database models (User, Decision, Option, etc.)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py          # /api/auth routes (register, login, logout, me)
│   │   └── decisions.py     # /api/decisions routes (CRUD, calculate, export)
│   ├── schemas.py           # Pydantic v2 request/response schemas
│   └── scoring.py           # Standalone weighted scoring & constraint engine
├── frontend/
│   ├── index.html           # Landing page with realistic career example
│   ├── login.html           # Login page
│   ├── register.html        # Registration page
│   ├── dashboard.html       # Decision list, search, templates modal, delete confirmation
│   ├── decision.html        # Decision workspace, rating matrix, simulator, results
│   ├── css/
│   │   └── style.css        # Shared design system, dark-mode tokens, print styles
│   └── js/
│       ├── app.js           # API client, session management, toast alerts
│       ├── auth.js          # Client-side validation & auth handlers
│       ├── dashboard.js     # Decision cards, search filtering, template creation
│       ├── decision.js      # Matrix grid, live calculation, What-if simulator, CSV export
│       └── templates.js     # Curated scenario templates
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures and isolated SQLite test database
│   ├── test_auth.py         # Authentication integration tests
│   ├── test_decisions.py    # CRUD, What-if simulation, cross-user isolation tests
│   ├── test_foundation.py   # Static assets and route checks
│   └── test_scoring.py      # Scoring engine mathematical & constraint unit tests
├── .env.example             # Template for environment configuration
├── .gitignore               # Ignores .venv, .env, *.db, cache files
├── requirements.txt         # Production dependencies
└── README.md                # Comprehensive documentation
```

---

## 7. Prerequisites for Windows

- **Windows 10 or 11**
- **Python 3.10+** (tested and verified on Python 3.14.6). Ensure *"Add Python to PATH"* was selected during installation.
- **Git** (version 2.40+).
- **PowerShell** or **Windows Command Prompt**.

---

## 8. Step-by-Step Local Setup

### Step 1: Clone the Repository
Open PowerShell and clone the repository:
```powershell
git clone https://github.com/your-username/DecisionDeck.git
cd DecisionDeck
```

### Step 2: Create and Activate Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(If PowerShell displays an ExecutionPolicy error, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and reactivate).*

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy the example environment file:
```powershell
Copy-Item .env.example .env
```
Open `.env` in your text editor and provide a secure random secret key:
```ini
APP_ENV=development
APP_SECRET_KEY=change-this-to-a-secure-random-string-at-least-32-characters
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DATABASE_URL=sqlite:///./decisiondeck.db
```

### Step 5: Start the Application
Run Uvicorn to start the local development server:
```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Open your browser and navigate to:
**`http://127.0.0.1:8000`**

---

## 9. Running Automated Tests

Run the full Pytest test suite:
```powershell
pytest -v
```

All 29 tests will execute, validating:
- The 8.1 career example calculation.
- Deterministic tie handling and floating-point tolerance.
- Weight summation (strictly 100%) and rating bounds (1.0–10.0).
- Ineligible option exclusion by hard constraints.
- User registration, login, and token generation.
- Decision CRUD operations and CSV streaming export.
- Cross-user data isolation (preventing User B from accessing User A's private decisions).

---

## 10. Interactive API Documentation

FastAPI automatically generates interactive OpenAPI documentation for all backend endpoints:
- **Swagger UI**: Visit `http://127.0.0.1:8000/docs`
- **ReDoc UI**: Visit `http://127.0.0.1:8000/redoc`

---

## 11. Deployment Guide

### Option A: Cloud Deployment (Render / Railway / Fly.io / Koyeb)

1. **Database Setup (Supabase PostgreSQL)**:
   - Create a free project at [Supabase](https://supabase.com).
   - In Supabase Project Settings &rarr; Database, copy your PostgreSQL connection URI:
     `postgresql://postgres:[YOUR-PASSWORD]@[HOST]:5432/postgres`
2. **Environment Variables**:
   In your hosting service's dashboard, configure the following environment variables:
   - `APP_ENV`: `production`
   - `APP_SECRET_KEY`: *Generate a strong 64-character random string*
   - `ACCESS_TOKEN_EXPIRE_MINUTES`: `1440`
   - `DATABASE_URL`: *Your Supabase PostgreSQL connection string*
3. **Build & Start Command**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. **Automatic Table Initialization**:
   On application startup, FastAPI's lifespan handler calls `Base.metadata.create_all(bind=engine)`, creating all required relational tables and indexes automatically.

---

## 12. Security Considerations

- **Password Storage**: Passwords are never stored in plaintext. They are salted and hashed using `bcrypt` (work factor 12).
- **No Token Leakage**: Password hashes and sensitive credentials are never returned in JSON response bodies or logged.
- **Session Tokens**: Authentication uses cryptographically signed JWT tokens with expiration (`exp`) and issuance (`iat`) timestamps.
- **Ownership Verification**: All state-changing endpoints verify ownership against the authenticated token subject before performing reads, updates, calculations, or deletions.
- **Preventing ID Enumeration**: Requesting an unauthorized decision ID returns `404 Not Found` rather than `403 Forbidden`.

---

## 13. Project Status

| Area | Status | Verification Details |
|:---|:---:|:---|
| **Weighted Scoring Engine** | Completed | 12 Pytest tests passed; 8.1 spec calculation verified |
| **Hard Requirements Evaluation** | Completed | Threshold evaluations tested (`<=`, `>=`, `<`, `>`, `==`) |
| **Relational Database & Models** | Completed | SQLAlchemy models, cascading deletes, foreign keys verified |
| **Authentication & User Isolation** | Completed | JWT + bcrypt implemented; multi-user isolation verified with tests |
| **Landing Page** | Completed | Responsive dark-mode interface, inline SVG logo, formula breakdown |
| **Dashboard** | Completed | Live search, templates modal, delete confirmation modal |
| **Decision Workspace** | Completed | Dynamic alternatives, criteria with auto-balance, rating matrix |
| **What-if Simulator** | Completed | Real-time weight sliders, non-mutating preview, reset & save |
| **Visual Charts** | Completed | Lightweight SVG score comparison bar chart |
| **CSV & Print Export** | Completed | RFC 4180 streaming CSV export & `@media print` layout |
| **Automated Test Suite** | Completed | 29/29 automated tests passing |

---

## 14. Known Limitations & Future Roadmap

- **Known Limitations**:
  - The What-if Simulator currently recalculates in real-time when sliders equal 100%. If a single slider is moved without adjusting others, the badge reminds the user to balance weights.
- **Future Roadmap**:
  - Proportional auto-normalization mode for sliders in the What-if Simulator.
  - Multi-user collaborative decision rooms with shared voting.
  - Integration with external data APIs for automatic product specification retrieval.

---

## License

This project is licensed under the MIT License.
