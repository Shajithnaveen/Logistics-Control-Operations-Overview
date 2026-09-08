# System Architecture Documentation

```
                        ┌──────────────────────────────────────────────┐
                        │        Synthetic Validation Dataset          │
                        │ (20 Vehicles, 20 Drivers, 100 Del, 200 Pk)  │
                        └──────────────────────┬───────────────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                     FastAPI Backend API                                      │
├──────────────────────────────┬──────────────────────────────┬───────────────────────────────┤
│    Distance Matrix Engine    │  Hard/Soft Constraint Model  │   Override Audit Log Service  │
│ (Haversine / Manhattan KM)   │ (Capacity, Workload, Window) │  (Immutable Action Log)       │
└──────────────────────────────┴──────────────┬───────────────┴───────────────────────────────┘
                                               │
                      ┌────────────────────────┴────────────────────────┐
                      │                                                 │
                      ▼                                                 ▼
        ┌───────────────────────────┐                     ┌───────────────────────────┐
        │     Baseline Solver       │                     │    VRPTW Optimizer        │
        │ (Delivery → Empty Return) │                     │ (Delivery → Pickup → Depot)│
        └─────────────┬─────────────┘                     └─────────────┬─────────────┘
                      │                                                 │
                      │         ┌───────────────────────────────┐       │
                      └────────►│  Side-by-Side Comparison      │◄──────┘
                                │  Matrix Engine & Metrics      │
                                └───────────────┬───────────────┘
                                                │
                                                ▼
                                ┌───────────────────────────────┐
                                │ Single-Page Web App Frontend  │
                                │ (Tailwind, Leaflet, Chart.js) │
                                └───────────────────────────────┘
```

## Core Algorithmic Workflow

1. **Input Data Validation**: Validates vehicle capacity, driver shift limits, delivery loads, and pickup weights.
2. **Geographic Distance Matrix**: Computes pairwise Manhattan road approximation distance (1.25x Haversine) and travel times assuming 30 km/h urban average speed.
3. **Route Construction Phase**:
   - **Step 1**: Assigns delivery drop-offs to fleet vehicles starting at 07:00 AM.
   - **Step 2**: Identifies pickup requests near delivery drop-off trajectories.
   - **Step 3**: Inserts pickup stops prior to returning to depot once delivery loads are emptied.
4. **Constraint Verification**: Evaluates all candidate stop insertions against vehicle capacity (kg) and driver shift limits (hours).
5. **Metric Synthesis**: Computes total distance, empty return distance, capacity utilization, workload hours, and percentage reductions.
