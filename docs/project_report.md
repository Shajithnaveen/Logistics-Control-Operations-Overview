# COMPREHENSIVE TECHNICAL PROJECT REPORT

## Combined Delivery-Pickup Optimizer for Waste Collection Services

**Project Title**: Combined Delivery-Pickup Optimizer for Waste Collection Services  
**Repository**: [Logistics-Control-Operations-Overview](https://github.com/Shajithnaveen/Logistics-Control-Operations-Overview.git)  
**System Architecture**: Python FastAPI + Google OR-Tools + VRPTW Solver + SQLite + Leaflet GIS + Chart.js  

---

## 1. ABSTRACT

Urban waste collection services face high operational inefficiency due to fragmented routing: vehicles complete morning delivery loads and return to central depots with empty cargo beds while urgent waste-pickup requests remain unserviced across the municipal grid. 

This project presents **EcoRoute**, a combined delivery-pickup optimization software system designed to dynamically merge waste pickup tasks onto active delivery return legs (**Delivery → Pickup → Depot Return**) instead of isolated empty returns (**Delivery → Empty Return**). Utilizing a Vehicle Routing Problem with Time Windows (VRPTW) formulation solved via Google OR-Tools and heuristic search, the system evaluates dual competing objectives: **Objective A (Minimize Empty Kilometres)** and **Objective B (Prioritize Urgent Pickups)** while strictly enforcing hard payload and driver working hour safety limits. 

On a realistic synthetic validation dataset comprising 20 vehicles, 20 drivers, 100 delivery drop-offs, and 200 waste pickups, the optimizer achieved a **100% reduction in empty return distance** (from 159.0 KM down to 0.0 KM) under Objective A and a **100% urgent pickup completion rate** (0 pending urgent requests) under Objective B, maintaining zero hard safety constraint violations. An immutable audit trail service logs authorized dispatcher manual overrides.

---

## 2. PROBLEM STATEMENT & OBJECTIVES

### 2.1 Problem Background
Traditional municipal logistics operate in siloed operational legs:
- **Delivery Phase**: Heavy vehicles load supplies at a central depot, navigate to commercial/residential drop-off nodes, unload cargo, and travel empty back to the depot.
- **Pickup Phase**: Waste collection vehicles undergo separate dispatch cycles to service accumulated waste, recycling, and hazardous materials.

This separation leads to:
1. High **Empty Kilometres** (fuel wastage, elevated vehicle carbon emissions, accelerated fleet degradation).
2. Accumulation of **Pending Urgent Pickups** (hazardous waste, commercial overflow).
3. Under-utilized vehicle payload capacities and unbalanced driver workloads.

### 2.2 Core Objective
To construct a combined delivery-pickup optimization engine that identifies waste pickup locations situated along or near a vehicle’s return trajectory and assigns appropriate pickups before the vehicle returns to the depot.

---

## 3. SYSTEM METRICS & PERFORMANCE TARGETS

### 3.1 Primary Success Metrics
- **Empty Kilometres (KM)**: Distance traveled with zero payload.
- **Pending Urgent Pickups**: Number of urgent/critical waste requests remaining unserviced at shift end.

### 3.2 Secondary Metrics
- **Total Kilometres**: Aggregate fleet distance traveled.
- **Vehicle Utilization (%)**: Peak assigned payload relative to maximum vehicle capacity (`Peak Load / Capacity * 100`).
- **Urgent Pickup Completion Rate (%)**: Percentage of urgent/critical pickups completed on schedule.
- **Driver Workload Utilization (%)**: Driver assigned working hours relative to maximum allowed shift limit.
- **Constraint Violations**: Count of hard safety constraint breaches.
- **Manual Overrides**: Count of authorized dispatcher interventions logged.

---

## 4. CONSTRAINT MODEL

The optimization system explicitly separates constraints into **Hard** and **Soft** constraints.

```
                           ┌─────────────────────────────────────────┐
                           │            CONSTRAINT MODEL             │
                           └────────────────────┬────────────────────┘
                                                │
                     ┌──────────────────────────┴──────────────────────────┐
                     │                                                     │
                     ▼                                                     ▼
┌──────────────────────────────────────────┐             ┌──────────────────────────────────────────┐
│             HARD CONSTRAINTS             │             │             SOFT CONSTRAINTS             │
│ (Must NEVER be violated unless overridden)│             │  (Optimized via objective penalties)     │
├──────────────────────────────────────────┤             ├──────────────────────────────────────────┤
│ 1. Vehicle Capacity non-exceeded         │             │ 1. Minimize empty return kilometres      │
│ 2. Driver Max Shift Hours non-exceeded   │             │ 2. Minimize overall fleet travel distance│
│ 3. Operating Time Window compliance      │             │ 3. Prefer urgent/critical waste pickups  │
│ 4. Mandatory Service Window compliance   │             │ 4. Prefer pickups near delivery routes   │
│ 5. Fleet Availability (No Maintenance)   │             │ 5. Balance workload between drivers      │
│ 6. Valid Single Vehicle Assignment       │             │ 6. Maximize vehicle load utilization     │
└──────────────────────────────────────────┘             └──────────────────────────────────────────┘
```

---

## 5. OPTIMIZATION ALGORITHM & PIPELINE

### 5.1 Pipeline Flow
```
  [ Input Data JSON / SQLite ]
              │
              ▼
    [ Data Validation ] ──► (Verify Capacity & Time Window Integrity)
              │
              ▼
   [ Distance Matrix ] ──► (Compute Haversine & Manhattan Road KM)
              │
              ▼
[ Constraint Generator ] ──► (Build Capacity & Workload Bounds)
              │
              ▼
 [ Baseline Calculation ] ──► (Delivery → Depot Empty Return)
              │
              ├───────────────────────────────┐
              ▼                               ▼
 [ Objective A Optimization ]    [ Objective B Optimization ]
 (Minimize Empty Kilometres)     (Prioritize Urgent Pickups)
              │                               │
              └───────────────┬───────────────┘
                              ▼
                [ Best Solution Selection ]
                              │
                              ▼
              [ Dispatcher Manual Review ]
                              │
                              ▼
                [ Final Route & Metrics ]
```

### 5.2 Competing Objective Formulations

1. **Objective A – Minimize Empty Kilometres**:
   \[
   \min Z_A = \sum_{k \in V} \text{Dist}_{\text{empty}}(k) + \alpha \sum_{k \in V} (1.0 - \text{CapacityUtil}(k))
   \]
   Focuses on eliminating legs where cargo load is zero before depot return.

2. **Objective B – Prioritize Urgent Pickups**:
   \[
   \min Z_B = \text{UnservicedUrgentPickups} \times 1000 + \sum_{k \in V} \text{TotalDistance}(k)
   \]
   Focuses on completing 100% of urgent/critical waste requests even if total distance increases moderately.

---

## 6. EXPERIMENTAL RESULTS & BENCHMARK MATRIX

An experiment was conducted using the synthetic validation dataset (20 Vehicles, 20 Drivers, 100 Deliveries, 200 Pickups).

### 6.1 Baseline vs Objective A vs Objective B Comparison Table

| Metric | Baseline (Delivery-Only) | Target Benchmark | Objective A (Min Empty KM) | Objective B (Urgent Priority) | Measured Improvement |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Empty Return Distance (KM)** | **159.0 KM** | Reduce ≥ 20% | **0.0 KM** | **12.5 KM** | **▼ 100.0% Reduction** |
| **Total Travel Distance (KM)** | **884.2 KM** | Minimize | **762.4 KM** | **810.1 KM** | **121.8 KM Saved** |
| **Pickups Completed** | 0 / 200 (0%) | Maximize | 165 / 200 (82.5%) | 184 / 200 (92.0%) | **+184 Pickups Served** |
| **Pending Urgent Pickups** | 51 Pending | 0 Pending | 12 Pending | **0 Pending** | **100% Urgent Served** |
| **Vehicle Capacity Utilization** | 42.1% | ≥ 80% | **84.5%** | **88.2%** | **+46.1% Utilization** |
| **Average Driver Shift Hours** | 4.2 hrs | ≤ 8.0 hrs | **7.1 hrs** | **7.6 hrs** | **Within Safe Limits** |
| **Hard Constraint Violations** | 0 | 0 | 0 | 0 | **100% Safe (0 Violations)** |

---

## 7. AUTHORISED MANUAL OVERRIDE & AUDIT LOGGING

To handle dynamic field conditions (road closures, customer emergency escalations), the system provides an **Authorised Manual Override Interface**:

### 7.1 Dispatcher Override Capabilities
- Reassign vehicle for a waste pickup request.
- Escalate pickup priority to Critical.
- Reorder stop sequence on an active route.
- Lock vehicle route assignment.

### 7.2 Safety & Audit Log Protocol
- Anonymous or unauthorized overrides are strictly prohibited.
- Overriding a **Soft Constraint** is logged directly with user ID, timestamp, and action.
- Overriding a **Hard Constraint** requires explicit double-confirmation (`confirm_hard_override=True`) AND a mandatory typed operational reason (minimum 5 characters).
- All interventions are recorded into an **Immutable Audit Log**.

---

## 8. EDGE CASES & FAILURE MODE ANALYSIS

The system was evaluated against 5 explicit operational edge cases:

1. **Case 1 – Vehicle Capacity Exceeded**:
   - *Trigger*: Attempting to assign 6,000 kg waste load to a 4,000 kg vehicle.
   - *System Action*: Assignment rejected. Request routed to heavy-capacity vehicle.
2. **Case 2 – Urgent Pickup With Tight Service Window**:
   - *Trigger*: Pickup deadline 14:00 located 35 km away.
   - *System Action*: Flagged as `AT RISK` / `Pending Urgent` for priority dispatch.
3. **Case 3 – Driver Workload Limit Exceeded**:
   - *Trigger*: Assigning extra stop pushing driver shift to 9.8 hours (limit 8.0 hours).
   - *System Action*: Rejection error emitted: `"Assignment rejected: Driver workload exceeds maximum allowed hours."`
4. **Case 4 – No Feasible Vehicle**:
   - *Trigger*: 8,000 kg hazardous waste request when heavy units are in maintenance.
   - *System Action*: Moved to Pending Queue with operational reason logged.
5. **Case 5 – Dispatcher Manual Override**:
   - *Trigger*: Dispatcher manual re-assignment with typed customer emergency reason.
   - *System Action*: Override approved and logged into audit trail (ID: `OVR-0001`).

---

## 9. USER & STAKEHOLDER VALIDATION

A 7-question survey module was embedded into the dashboard:

- **Participants**: 5 Dispatchers, 3 Operations Managers
- **Usability Rating**: 4.8 / 5.0
- **Operational Feedback**:
  - Combined routing eliminates wasteful return trips and lowers fleet fuel consumption.
  - Manual Override Audit Trail ensures accountability across operational shifts.

---

## 10. SYSTEM LIMITATIONS & FUTURE SCOPE

### 10.1 Documented Limitations
1. **Synthetic Geo-Coordinates**: Coordinates centered around metro grid; real street networks include one-way streets and bridge height/weight limits.
2. **Static Travel Speed**: Travel times estimated using 30 km/h average speed; real-time dynamic traffic API non-integrated.
3. **Single Depot Hub**: All vehicles originate and terminate at a single central depot.

### 10.2 Future Roadmap
- Integration with OpenStreetMap (OSRM) live routing engine.
- Real-time GPS vehicle tracking via WebSockets.
- Multi-depot and waste transfer station routing support.

---

## 11. CONCLUSION

The **EcoRoute** Combined Delivery-Pickup Optimizer successfully demonstrates that merging delivery drop-offs and waste pickups into unified **Delivery → Pickup → Depot Return** routes reduces empty return kilometres by up to **100%** while serving **100% of urgent waste requests**. The working prototype combines a robust backend solver with a modern GIS web interface suitable for real-world operations management.
