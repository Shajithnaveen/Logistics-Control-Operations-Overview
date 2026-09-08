# Requirements Specification

## Functional Requirements (FR)

- **FR1 – Vehicle Management**: Manage 20 fleet vehicles with parameters including capacity (kg), location, availability windows, assigned driver, and operational status (Available, Assigned, In Transit, Completed, Maintenance).
- **FR2 – Delivery Management**: Track 100 delivery loads with customer location, latitude/longitude, weight load (kg), service time windows, and priority rankings (Normal, High, Critical).
- **FR3 – Pickup Management**: Track 200 waste pickup requests with location, waste weight (kg), request time, service windows, and priority rankings (Normal, Urgent, Critical). Urgent requests receive optimization priority.
- **FR4 – Route Optimization Engine**: Formulate and solve Vehicle Routing Problem with Time Windows (VRPTW) combining delivery drop-offs and waste pickups before returning to depot.
- **FR5 – Constraint Validation Engine**: Explicitly enforce Hard Constraints (capacity limits, driver work hours limits, vehicle shift windows, service windows) and evaluate Soft Constraints (empty km minimization, distance penalties).
- **FR6 – Dual Objective Solver**:
  - **Objective A**: Minimize empty return distance and maximize vehicle load utilization.
  - **Objective B**: Prioritize urgent pickup completion rate and tight service window compliance.
- **FR7 – Authorised Manual Override**: Provide dispatcher interface to reassign routes, reorder stops, or adjust priorities. Hard constraint overrides require explicit confirmation and typed reason logged into an immutable audit trail.
- **FR8 – Metrics & Analytics Dashboard**: Present KPI cards, Chart.js distance visualizers, vehicle utilization gauges, and baseline vs optimized comparison tables.
- **FR9 – Baseline Comparison**: Calculate traditional **Delivery → Empty Return** baseline process to benchmark empty KM reduction.
- **FR10 – Immutable Audit Logging**: Maintain complete audit log of all dispatcher overrides including user ID, timestamp, vehicle ID, original assignment, new assignment, reason, and status.

## Non-Functional Requirements (NFR)

- **Reliability**: Deterministic solver guarantees feasible routes under all valid input conditions.
- **Safety**: Safe Assignment flag (`YES/NO`) enforces hard driver workload and safety limits.
- **Usability**: Responsive glassmorphic dark-theme UI with interactive GIS Leaflet route maps.
- **Performance**: Solves 20-vehicle, 300-stop VRP optimization in under 2 seconds.
- **Scalability**: REST API backend designed for extension to multi-depot and larger regional fleets.
