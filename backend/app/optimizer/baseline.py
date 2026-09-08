from typing import Dict, List, Any
from app.optimizer.distance import manhattan_road_distance, estimate_travel_time_minutes, parse_time_to_minutes
from app.optimizer.constraints import ConstraintChecker

def calculate_baseline(dataset: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates the Baseline operational state:
    Traditional Delivery -> Depot Return process.
    Pickups are NOT combined onto delivery routes and remain unserviced/pending.
    """
    depot = dataset["depot"]
    vehicles = dataset["vehicles"]
    deliveries = dataset["deliveries"]
    pickups = dataset["pickups"]
    
    routes = []
    total_km = 0.0
    empty_km = 0.0
    completed_deliveries = 0
    completed_pickups = 0
    completed_urgent_pickups = 0
    
    # Assign deliveries sequentially across available vehicles up to capacity limits
    del_index = 0
    num_deliveries = len(deliveries)
    
    for veh in vehicles:
        if del_index >= num_deliveries or veh.get("vehicle_status") == "Maintenance":
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
                "hard_violations": [],
                "soft_violations": []
            })
            continue
            
        veh_capacity = veh["capacity_kg"]
        veh_routes_stops = []
        current_load = 0
        
        # Add Depot Start
        veh_routes_stops.append({
            "type": "DEPOT",
            "name": depot["name"],
            "latitude": depot["latitude"],
            "longitude": depot["longitude"],
            "service_start": "07:00",
            "service_end": "17:00"
        })
        
        # Add Deliveries until capacity or count limit
        while del_index < num_deliveries:
            d = deliveries[del_index]
            if current_load + d["load_kg"] <= veh_capacity:
                current_load += d["load_kg"]
                veh_routes_stops.append({
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
                del_index += 1
            else:
                break
                
        # Add Depot Return (Empty Return!)
        veh_routes_stops.append({
            "type": "DEPOT",
            "name": depot["name"],
            "latitude": depot["latitude"],
            "longitude": depot["longitude"],
            "service_start": "07:00",
            "service_end": "17:00"
        })
        
        # Evaluate route metrics
        hard_v, soft_v, details = ConstraintChecker.evaluate_route(veh, veh_routes_stops)
        
        # In baseline, the leg from last delivery back to depot is 100% empty return
        # plus any transit between deliveries with 0 useful pickup load
        route_empty = 0.0
        if len(veh_routes_stops) >= 3:
            last_del = veh_routes_stops[-2]
            depot_return_dist = manhattan_road_distance(last_del["latitude"], last_del["longitude"], depot["latitude"], depot["longitude"])
            route_empty = depot_return_dist
            
        details["empty_distance_km"] = round(route_empty, 2)
        total_km += details["total_distance_km"]
        empty_km += route_empty
        completed_deliveries += details["deliveries_completed"]
        
        routes.append({
            "vehicle_id": veh["vehicle_id"],
            "driver_name": veh["driver_name"],
            "stops": veh_routes_stops,
            "total_distance_km": details["total_distance_km"],
            "empty_distance_km": route_empty,
            "deliveries_completed": details["deliveries_completed"],
            "pickups_completed": 0,
            "urgent_pickups_completed": 0,
            "capacity_utilization": details["capacity_utilization"],
            "workload_hours": details["workload_hours"],
            "hard_violations": hard_v,
            "soft_violations": soft_v
        })

    total_urgent = sum(1 for p in pickups if p.get("priority") in ["Urgent", "Critical"])
    pending_urgent = total_urgent # 0 completed in baseline
    
    avg_veh_utilization = round(sum(r["capacity_utilization"] for r in routes if r["deliveries_completed"] > 0) / max(1, sum(1 for r in routes if r["deliveries_completed"] > 0)), 1)
    
    return {
        "scenario": "Baseline (Delivery -> Empty Return)",
        "routes": routes,
        "metrics": {
            "total_kilometres": round(total_km, 1),
            "empty_kilometres": round(empty_km, 1),
            "empty_km_reduction_pct": 0.0,
            "total_deliveries_completed": completed_deliveries,
            "pending_deliveries": len(deliveries) - completed_deliveries,
            "total_pickups_completed": 0,
            "total_pickups": len(pickups),
            "pickup_completion_rate": 0.0,
            "urgent_pickups_completed": 0,
            "total_urgent_pickups": total_urgent,
            "pending_urgent_pickups": pending_urgent,
            "urgent_pickup_completion_rate": 0.0,
            "vehicle_utilization_pct": avg_veh_utilization,
            "average_workload_hours": round(sum(r["workload_hours"] for r in routes) / len(routes), 1),
            "constraint_violations": sum(len(r["hard_violations"]) for r in routes),
            "manual_overrides_count": 0,
            "safe_assignment": True
        }
    }
