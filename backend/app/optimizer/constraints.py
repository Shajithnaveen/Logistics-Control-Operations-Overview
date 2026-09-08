from typing import Dict, List, Any, Tuple
from app.optimizer.distance import parse_time_to_minutes, estimate_travel_time_minutes

class ConstraintChecker:
    """Explicitly separates and evaluates HARD and SOFT constraints."""

    @staticmethod
    def evaluate_route(vehicle: Dict[str, Any], route_stops: List[Dict[str, Any]]) -> Tuple[List[str], List[str], Dict[str, Any]]:
        """
        Evaluates a sequence of stops for a single vehicle.
        Returns: (hard_violations, soft_violations, details)
        """
        hard_violations = []
        soft_violations = []
        
        veh_capacity = vehicle.get("capacity_kg", 5000)
        max_work_hours = vehicle.get("driver_work_limit_hours", 8.0)
        veh_status = vehicle.get("vehicle_status", "Available")
        
        # Hard Constraint 1: Vehicle Maintenance / Availability
        if veh_status == "Maintenance":
            hard_violations.append(f"Vehicle {vehicle['vehicle_id']} is under Maintenance and cannot be assigned.")

        current_load = 0
        peak_load = 0
        total_travel_distance = 0.0
        empty_return_distance = 0.0
        total_service_time = 0
        
        current_time = parse_time_to_minutes(vehicle.get("available_from", "07:00"))
        end_time_limit = parse_time_to_minutes(vehicle.get("available_until", "17:00"))
        
        prev_stop = {
            "latitude": vehicle.get("latitude", 40.7128),
            "longitude": vehicle.get("longitude", -74.0060),
            "type": "DEPOT"
        }
        
        deliveries_completed = 0
        pickups_completed = 0
        urgent_pickups_completed = 0
        has_delivered_all = False
        
        # Track load changes stop by stop
        for idx, stop in enumerate(route_stops):
            stop_type = stop.get("type", "DELIVERY") # DELIVERY, PICKUP, DEPOT
            lat = stop.get("latitude")
            lng = stop.get("longitude")
            
            from app.optimizer.distance import manhattan_road_distance
            dist = manhattan_road_distance(prev_stop["latitude"], prev_stop["longitude"], lat, lng)
            travel_time = estimate_travel_time_minutes(dist)
            
            total_travel_distance += dist
            current_time += travel_time
            
            # Check segment empty KM (if vehicle carries 0 load after deliveries before pickup)
            if stop_type == "DEPOT" and current_load == 0:
                empty_return_distance += dist
            elif current_load == 0 and idx > 0 and prev_stop["type"] == "DELIVERY":
                empty_return_distance += dist
                
            # Service Window Hard & Soft Checks
            window_start = parse_time_to_minutes(stop.get("service_start", "07:00"))
            window_end = parse_time_to_minutes(stop.get("service_end", "17:00"))
            
            if current_time < window_start:
                # Arrived early -> wait
                current_time = window_start
            elif current_time > window_end:
                stop_id = stop.get("delivery_id") or stop.get("pickup_id") or f"Stop-{idx}"
                arr_h = int(current_time) // 60
                arr_m = int(current_time) % 60
                win_h = int(window_end) // 60
                win_m = int(window_end) % 60
                hard_violations.append(f"Service Window Violation at {stop_id}: Arrived at {arr_h:02d}:{arr_m:02d}, window ends at {win_h:02d}:{win_m:02d}")
            
            service_mins = stop.get("estimated_service_minutes", 15)
            current_time += service_mins
            total_service_time += service_mins
            
            # Load adjustment
            if stop_type == "DELIVERY":
                load_weight = stop.get("load_kg", 0)
                current_load += load_weight
                peak_load = max(peak_load, current_load)
                deliveries_completed += 1
            elif stop_type == "PICKUP":
                waste_weight = stop.get("waste_weight_kg", 0)
                current_load += waste_weight
                peak_load = max(peak_load, current_load)
                pickups_completed += 1
                if stop.get("priority") in ["Urgent", "Critical"]:
                    urgent_pickups_completed += 1
            elif stop_type == "DEPOT":
                current_load = 0 # Unloaded at depot
                
            # Hard Constraint 2: Vehicle Capacity Exceeded
            if current_load > veh_capacity:
                hard_violations.append(f"Vehicle Capacity Exceeded on {vehicle['vehicle_id']}: Load {current_load} kg exceeds capacity {veh_capacity} kg at stop {stop.get('location', idx)}")
                
            prev_stop = stop
            
        # Hard Constraint 3: Driver Work Limit Exceeded
        total_time_hours = round((current_time - parse_time_to_minutes(vehicle.get("available_from", "07:00"))) / 60.0, 2)
        if total_time_hours > max_work_hours:
            hard_violations.append(f"Driver Workload Limit Exceeded: Assigned {total_time_hours} hrs exceeds driver limit {max_work_hours} hrs for {vehicle.get('driver_name', vehicle['driver_id'])}")

        if current_time > end_time_limit:
            ret_h = int(current_time) // 60
            ret_m = int(current_time) % 60
            end_h = int(end_time_limit) // 60
            end_m = int(end_time_limit) % 60
            hard_violations.append(f"Vehicle Operating Window Exceeded: Vehicle returned at {ret_h:02d}:{ret_m:02d}, past shift end {end_h:02d}:{end_m:02d}")
            
        # Soft Constraint Warnings
        if empty_return_distance > 15.0:
            soft_violations.append(f"High empty return distance ({empty_return_distance:.1f} km) on route {vehicle['vehicle_id']}")
            
        if (peak_load / veh_capacity) < 0.35:
            soft_violations.append(f"Low vehicle capacity utilization ({round(peak_load/veh_capacity*100,1)}%) for {vehicle['vehicle_id']}")

        details = {
            "total_distance_km": round(total_travel_distance, 2),
            "empty_distance_km": round(empty_return_distance, 2),
            "peak_load_kg": peak_load,
            "capacity_utilization": round((peak_load / veh_capacity) * 100, 1) if veh_capacity > 0 else 0,
            "workload_hours": total_time_hours,
            "workload_utilization": round((total_time_hours / max_work_hours) * 100, 1) if max_work_hours > 0 else 0,
            "deliveries_completed": deliveries_completed,
            "pickups_completed": pickups_completed,
            "urgent_pickups_completed": urgent_pickups_completed,
            "safe_assignment": len(hard_violations) == 0
        }
        
        return hard_violations, soft_violations, details
