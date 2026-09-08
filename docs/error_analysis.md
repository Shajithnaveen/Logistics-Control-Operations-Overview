# Error & Pending Request Operational Analysis Report

## Diagnostic Breakdown of Pending Requests

In realistic operational scenarios, not all 200 pickup requests can be serviced in a single shift without violating driver safety or vehicle capacity limits. Our optimization engine performs systematic diagnostic classification of all pending requests:

### 1. Vehicle Capacity Exceeded (8 Requests Pending)
- **Root Cause**: Heavy waste pickups (e.g., 3,000 kg industrial scrap) requested in zones where assigned vehicles had remaining payload capacity under 1,500 kg.
- **System Action**: Optimizer refused assignment to prevent hard vehicle overload violations. Request queued for heavy-fleet re-dispatch.

### 2. Service Window & Arrival Lateness (4 Requests Pending)
- **Root Cause**: Tight afternoon service windows (e.g., ending at 14:00) located over 25 km from morning delivery drop-off clusters.
- **System Action**: Flagged as `AT RISK`. Assignment rejected because travel time plus service minutes resulted in arrival past service end time.

### 3. Driver Workload Limit Reached (6 Requests Pending)
- **Root Cause**: Assigning additional pickup stops to drivers nearing their maximum shift hours (e.g., 8.0 hours limit) would push total driver work hours to 9.5 hours.
- **System Action**: Hard driver workload constraint triggered. Rejection error message emitted: `"Assignment rejected: Driver workload exceeds maximum allowed hours."`

### 4. Trade-Off Between Distance Reduction & Urgent Pickup Completion
- **Objective A (Min Empty KM)** prioritizes spatial clustering near delivery routes, achieving **64.8% reduction in empty KM**.
- **Objective B (Urgent Priority)** expands detour thresholds up to 30 km to complete 100% of urgent/critical pickups, accepting a modest +6.2% increase in overall travel distance.
