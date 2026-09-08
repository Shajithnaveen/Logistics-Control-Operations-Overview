import math
from typing import Dict, List, Any, Tuple
from app.optimizer.distance import manhattan_road_distance, estimate_travel_time_minutes, parse_time_to_minutes
from app.optimizer.constraints import ConstraintChecker

class VRPOptimizer:
    def __init__(self, dataset: Dict[str, Any]):
        self.depot = dataset["depot"]
        self.vehicles = dataset["vehicles"]
        self.deliveries = dataset["deliveries"]
        self.pickups = dataset["pickups"]

    def solve(self, objective_mode: str = "OBJECTIVE_A") -> Dict[str, Any]:
        """
        Solves the combined Delivery -> Pickup -> Return VRP.
        objective_mode:
            - 'OBJECTIVE_A': Minimize Empty Kilometres
            - 'OBJECTIVE_B': Prioritize Urgent Pickups
        """
        try:
            return self._solve_ortools(objective_mode)
        except Exception as e:
            return self._solve_heuristic(objective_mode)

    def _solve_heuristic(self, objective_mode: str) -> Dict[str, Any]:
        depot = self.depot
        vehicles = [v for v in self.vehicles if v.get("vehicle_status") != "Maintenance"]
        deliveries = list(self.deliveries)
        pickups = list(self.pickups)
        
        priority_weights = {"Critical": 3, "Urgent": 2, "Normal": 1}
        
        # Sort pickups: Urgent & Critical pickups FIRST
        if objective_mode == "OBJECTIVE_B":
            pickups.sort(key=lambda p: (-priority_weights.get(p.get("priority"), 1), p.get("service_end", "17:00")))
        else:
            pickups.sort(key=lambda p: (0 if p.get("priority") in ["Urgent", "Critical"] else 1, p.get("waste_weight_kg", 0)))
            
        routes = []
        assigned_delivery_ids = set()
        assigned_pickup_ids = set()
        
        total_km = 0.0
        empty_km = 0.0
        
        del_pool = list(deliveries)
        
        for veh in self.vehicles:
            if veh.get("vehicle_status") == "Maintenance":
                routes.append({
                    "vehicle_id": veh["vehicle_id"],
                    "driver_name": veh["driver_name"],
                    "stops": [{"type": "DEPOT", "name": depot["name"], "latitude": depot["latitude"], "longitude": depot["longitude"]}],
                    "total_distance_km": 0.0,
                    "empty_distance_km": 0.0,
                    "deliveries_completed": 0,
                    "pickups_completed": 0,
                    "urgent_pickups_completed": 0,
                    "capacity_utilization": 0.0,
                    "workload_hours": 0.0,
                    "hard_violations": [f"Vehicle {veh['vehicle_id']} is under Maintenance."],
                    "soft_violations": []
                })
                continue
                
            veh_capacity = veh["capacity_kg"]
            max_work_hours = veh["driver_work_limit_hours"]
            
            # Start route with Depot
            veh_stops = [{
                "type": "DEPOT",
                "name": depot["name"],
                "latitude": depot["latitude"],
                "longitude": depot["longitude"],
                "service_start": "07:00",
                "service_end": "17:00"
            }]
            
            curr_delivery_load = 0
            
            # Add deliveries
            del_limit = 3 if objective_mode == "OBJECTIVE_B" else 6
            del_added = 0
            
            unassigned_del_pool = []
            for d in del_pool:
                if d["delivery_id"] in assigned_delivery_ids:
                    continue
                if del_added < del_limit and curr_delivery_load + d["load_kg"] <= veh_capacity * 0.60:
                    curr_delivery_load += d["load_kg"]
                    assigned_delivery_ids.add(d["delivery_id"])
                    del_added += 1
                    veh_stops.append({
                        "type": "DELIVERY",
                        "delivery_id": d["delivery_id"],
                        "location": d["location"],
                        "latitude": d["latitude"],
                        "longitude": d["longitude"],
                        "load_kg": d["load_kg"],
                        "service_start": d["service_start"],
                        "service_end": d["service_end"],
                        "estimated_service_minutes": d.get("estimated_service_minutes", 15),
                        "priority": d["priority"]
                    })
                else:
                    unassigned_del_pool.append(d)
                    
            del_pool = unassigned_del_pool
            
            # Step 2: Add Pickups
            current_pickup_load = 0
            
            for p in pickups:
                if p["pickup_id"] in assigned_pickup_ids:
                    continue
                    
                p_weight = p["waste_weight_kg"]
                p_priority = p.get("priority", "Normal")
                
                # In Objective B, pick up as many urgent & critical requests as fit vehicle capacity
                if current_pickup_load + p_weight <= veh_capacity:
                    # Test inserting pickup before depot return
                    test_stops = list(veh_stops) + [{
                        "type": "PICKUP",
                        "pickup_id": p["pickup_id"],
                        "location": p["location"],
                        "latitude": p["latitude"],
                        "longitude": p["longitude"],
                        "waste_weight_kg": p["waste_weight_kg"],
                        "service_start": p["service_start"],
                        "service_end": p["service_end"],
                        "estimated_service_minutes": p.get("estimated_service_minutes", 15),
                        "priority": p["priority"]
                    }, {
                        "type": "DEPOT",
                        "name": depot["name"],
                        "latitude": depot["latitude"],
                        "longitude": depot["longitude"]
                    }]
                    
                    # Evaluate driver work hours limit
                    hard_v, _, details = ConstraintChecker.evaluate_route(veh, test_stops)
                    
                    if details["workload_hours"] <= max_work_hours:
                        current_pickup_load += p_weight
                        assigned_pickup_ids.add(p["pickup_id"])
                        veh_stops.append({
                            "type": "PICKUP",
                            "pickup_id": p["pickup_id"],
                            "location": p["location"],
                            "latitude": p["latitude"],
                            "longitude": p["longitude"],
                            "waste_weight_kg": p["waste_weight_kg"],
                            "service_start": p["service_start"],
                            "service_end": p["service_end"],
                            "estimated_service_minutes": p.get("estimated_service_minutes", 15),
                            "priority": p["priority"]
                        })
                        
            # End route with Depot Return
            veh_stops.append({
                "type": "DEPOT",
                "name": depot["name"],
                "latitude": depot["latitude"],
                "longitude": depot["longitude"],
                "service_start": "07:00",
                "service_end": "17:00"
            })
            
            # Final route evaluation
            hard_v, soft_v, details = ConstraintChecker.evaluate_route(veh, veh_stops)
            route_empty = details["empty_distance_km"]
            
            total_km += details["total_distance_km"]
            empty_km += route_empty
            
            routes.append({
                "vehicle_id": veh["vehicle_id"],
                "driver_name": veh["driver_name"],
                "stops": veh_stops,
                "total_distance_km": details["total_distance_km"],
                "empty_distance_km": route_empty,
                "deliveries_completed": details["deliveries_completed"],
                "pickups_completed": details["pickups_completed"],
                "urgent_pickups_completed": details["urgent_pickups_completed"],
                "capacity_utilization": details["capacity_utilization"],
                "workload_hours": details["workload_hours"],
                "hard_violations": hard_v,
                "soft_violations": soft_v
            })

        completed_del_count = len(assigned_delivery_ids)
        completed_pik_count = len(assigned_pickup_ids)
        
        urgent_pickups = [p for p in pickups if p.get("priority") in ["Urgent", "Critical"]]
        completed_urgent_count = sum(1 for p in urgent_pickups if p["pickup_id"] in assigned_pickup_ids)
        pending_urgent_count = len(urgent_pickups) - completed_urgent_count
        
        from app.optimizer.baseline import calculate_baseline
        baseline_res = calculate_baseline({"depot": self.depot, "vehicles": self.vehicles, "deliveries": self.deliveries, "pickups": self.pickups})
        baseline_empty = baseline_res["metrics"]["empty_kilometres"]
        
        empty_reduction_pct = round(((baseline_empty - empty_km) / max(1.0, baseline_empty)) * 100.0, 1)
        
        active_routes = [r for r in routes if len(r["stops"]) > 2]
        avg_veh_util = round(sum(r["capacity_utilization"] for r in active_routes) / max(1, len(active_routes)), 1)
        avg_workload = round(sum(r["workload_hours"] for r in routes) / len(routes), 1)
        
        total_violations = sum(len(r["hard_violations"]) for r in routes)
        scenario_name = "Objective A (Minimize Empty KM)" if objective_mode == "OBJECTIVE_A" else "Objective B (Prioritize Urgent Pickups)"
        
        return {
            "scenario": scenario_name,
            "objective_mode": objective_mode,
            "routes": routes,
            "metrics": {
                "total_kilometres": round(total_km, 1),
                "empty_kilometres": round(empty_km, 1),
                "empty_km_reduction_pct": max(0.0, empty_reduction_pct),
                "total_deliveries_completed": completed_del_count,
                "pending_deliveries": len(deliveries) - completed_del_count,
                "total_pickups_completed": completed_pik_count,
                "total_pickups": len(pickups),
                "pickup_completion_rate": round((completed_pik_count / max(1, len(pickups))) * 100, 1),
                "urgent_pickups_completed": completed_urgent_count,
                "total_urgent_pickups": len(urgent_pickups),
                "pending_urgent_pickups": pending_urgent_count,
                "urgent_pickup_completion_rate": round((completed_urgent_count / max(1, len(urgent_pickups))) * 100, 1),
                "vehicle_utilization_pct": avg_veh_util,
                "average_workload_hours": avg_workload,
                "constraint_violations": total_violations,
                "manual_overrides_count": 0,
                "safe_assignment": total_violations == 0
            }
        }

    def _solve_ortools(self, objective_mode: str) -> Dict[str, Any]:
        return self._solve_heuristic(objective_mode)
