# Combined Delivery-Pickup Optimizer for Waste Collection Services

A complete, end-to-end working software prototype that intelligently optimizes waste collection logistics by transforming standard **Delivery → Empty Return** routes into efficient **Delivery → Pickup → Depot Return** routes.

---

## Key Features

1. **Dual Optimization Objectives**:
   - **Objective A (Minimize Empty KM)**: Reduces empty return kilometres and optimizes vehicle load utilization before returning to the depot.
   - **Objective B (Prioritize Urgent Pickups)**: Maximizes completed urgent/critical pickups and time-window compliance.
2. **Hard & Soft Constraint Engine**:
   - Explicit separation of Hard constraints (vehicle capacity, driver working hours limit, service windows, fleet availability) and Soft constraints (distance penalties, urgent pickup weighting, workload balance).
3. **Authorised Manual Dispatcher Overrides**:
   - Allows dispatchers to manually reassign vehicles, reorder stops, or adjust priorities.
   - Hard constraint overrides require explicit confirmation and a mandatory typed operational reason logged into an immutable audit trail.
4. **Realistic Synthetic Validation Dataset**:
   - Includes 20 vehicles, 20 drivers, 100 delivery loads, and 200 pickup requests centered on realistic geographic coordinates.
5. **Interactive Web Dashboard**:
   - Built with modern HTML5/JS, Tailwind CSS, Leaflet GIS route mapping, Chart.js operational analytics, and 9 dedicated prototype screens.

---

## Setup & Running Instructions

### 1. Prerequisites
- Python 3.9+ (Anaconda Python recommended)
- `pip` package manager

### 2. Install Dependencies
```bash
pip install fastapi uvicorn ortools pandas scipy pytest requests sqlalchemy pydantic
```

### 3. Generate Seed Dataset
```bash
python backend/app/seed_data.py
```

### 4. Run Automated Test Suite
```bash
python -m pytest tests/test_optimizer.py
```

### 5. Launch FastAPI Backend Server & Web Application
```bash
python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
```

Open your browser and navigate to:
[http://localhost:8000](http://localhost:8000)

---

## Project Structure

```
waste_collection_optimizer/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI server & static file server
│   │   ├── seed_data.py         # Synthetic dataset generator
│   │   ├── optimizer/
│   │   │   ├── distance.py      # Haversine & Manhattan distance matrix
│   │   │   ├── constraints.py   # Hard & Soft constraint checkers
│   │   │   ├── baseline.py      # Baseline Delivery -> Depot Return solver
│   │   │   └── vrp_solver.py    # VRP solver (Objective A & B)
│   │   └── services/
│   │       ├── overrides.py     # Manual override handler & audit log
│   │       └── edge_cases.py    # Edge cases simulation validator
├── frontend/
│   └── index.html               # Single-page web app (Tailwind, Leaflet, Chart.js)
├── data/
│   └── seed_dataset.json        # 20 Vehicles, 20 Drivers, 100 Deliveries, 200 Pickups
├── tests/
│   └── test_optimizer.py        # Automated test suite (8 tests)
└── docs/
    ├── requirements_specification.md
    ├── architecture.md
    ├── error_analysis.md
    ├── limitations_report.md
    └── stakeholder_validation.md
```

---

## API Endpoints Overview

- `GET /api/dataset`: Fetch current fleet, drivers, deliveries, and pickups dataset.
- `GET /api/baseline`: Calculate Baseline (Delivery-only empty return) metrics & routes.
- `POST /api/optimize?objective_mode=OBJECTIVE_A`: Run Empty KM minimization optimization.
- `POST /api/optimize?objective_mode=OBJECTIVE_B`: Run Urgent Pickup prioritization optimization.
- `GET /api/optimization-comparison`: Get side-by-side metric comparison matrix (Baseline vs Obj A vs Obj B).
- `POST /api/override`: Submit dispatcher manual override with mandatory audit log.
- `GET /api/overrides`: Fetch full override history audit trail.
- `GET /api/edge-cases`: Retrieve 5 operational edge case simulation results.
- `GET /api/health`: System health status check.
