import json
import os
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from app.seed_data import generate_seed_data
from app.optimizer.baseline import calculate_baseline
from app.optimizer.vrp_solver import VRPOptimizer
from app.services.overrides import override_service
from app.services.edge_cases import simulate_edge_cases

app = FastAPI(
    title="Combined Delivery-Pickup Optimizer API",
    description="Waste Collection Logistics & VRP Routing Engine",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_FILE = os.path.join(BASE_DIR, "data", "seed_dataset.json")

def load_data() -> Dict[str, Any]:
    if not os.path.exists(DATA_FILE):
        return generate_seed_data()
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data: Dict[str, Any]):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Models for API requests
class OverrideRequest(BaseModel):
    user: str
    role: str = "Dispatcher"
    action_type: str = "REASSIGN_VEHICLE"
    vehicle_id: str
    original_assignment: str
    new_assignment: str
    reason: str
    constraint_affected: str = "Soft Constraint"
    confirm_hard_override: bool = False
    route_stops: Optional[List[Dict[str, Any]]] = None

class DeliveryCreateRequest(BaseModel):
    location: str
    latitude: float
    longitude: float
    load_kg: float
    service_start: str = "08:00"
    service_end: str = "16:00"
    priority: str = "Normal"

class PickupCreateRequest(BaseModel):
    location: str
    latitude: float
    longitude: float
    waste_weight_kg: float
    request_time: str = "08:30"
    service_start: str = "09:00"
    service_end: str = "15:00"
    priority: str = "Normal"
    estimated_service_minutes: int = 15

class VehicleCreateRequest(BaseModel):
    vehicle_number: str
    capacity_kg: float
    driver_name: str
    driver_work_limit_hours: float = 8.0
    vehicle_status: str = "Available"

# API Endpoints

@app.get("/api/health")
def health_check():
    return {
        "status": "HEALTHY",
        "service": "Waste Collection Route Optimization API",
        "engine": "Google OR-Tools / VRPTW Engine Active",
        "version": "1.0.0"
    }

@app.get("/api/dataset")
def get_dataset():
    data = load_data()
    return {
        "depot": data["depot"],
        "vehicle_count": len(data["vehicles"]),
        "driver_count": len(data["drivers"]),
        "delivery_count": len(data["deliveries"]),
        "pickup_count": len(data["pickups"]),
        "vehicles": data["vehicles"],
        "deliveries": data["deliveries"],
        "pickups": data["pickups"],
        "drivers": data["drivers"]
    }

@app.get("/api/baseline")
def get_baseline():
    data = load_data()
    return calculate_baseline(data)

@app.post("/api/optimize")
def run_optimization(objective_mode: str = Query("OBJECTIVE_A", description="OBJECTIVE_A or OBJECTIVE_B")):
    data = load_data()
    optimizer = VRPOptimizer(data)
    result = optimizer.solve(objective_mode)
    return result

@app.get("/api/optimization-comparison")
def get_optimization_comparison():
    """Returns side-by-side comparison matrix for Baseline vs Objective A vs Objective B."""
    data = load_data()
    baseline = calculate_baseline(data)
    
    optimizer = VRPOptimizer(data)
    obj_a = optimizer.solve("OBJECTIVE_A")
    obj_b = optimizer.solve("OBJECTIVE_B")
    
    return {
        "baseline": baseline["metrics"],
        "objective_a": obj_a["metrics"],
        "objective_b": obj_b["metrics"],
        "targets": {
            "empty_km_reduction_target_pct": 20.0,
            "pending_urgent_reduction_target_pct": 50.0,
            "max_hard_violations": 0,
            "max_unsafe_assignments": 0,
            "capacity_compliance_target_pct": 100.0
        },
        "routes": {
            "baseline": baseline["routes"],
            "objective_a": obj_a["routes"],
            "objective_b": obj_b["routes"]
        }
    }

@app.get("/api/routes")
def get_routes(objective_mode: str = Query("OBJECTIVE_A")):
    data = load_data()
    optimizer = VRPOptimizer(data)
    result = optimizer.solve(objective_mode)
    return {
        "scenario": result["scenario"],
        "objective_mode": objective_mode,
        "routes": result["routes"]
    }

@app.get("/api/metrics")
def get_metrics(objective_mode: str = Query("OBJECTIVE_A")):
    data = load_data()
    optimizer = VRPOptimizer(data)
    result = optimizer.solve(objective_mode)
    return result["metrics"]

@app.post("/api/deliveries")
def add_delivery(payload: DeliveryCreateRequest):
    data = load_data()
    new_id = f"DEL-{len(data['deliveries']) + 1:03d}"
    new_delivery = {
        "delivery_id": new_id,
        "location": payload.location,
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "load_kg": payload.load_kg,
        "service_start": payload.service_start,
        "service_end": payload.service_end,
        "priority": payload.priority,
        "status": "Pending"
    }
    data["deliveries"].append(new_delivery)
    save_data(data)
    return {"status": "SUCCESS", "delivery": new_delivery}

@app.post("/api/pickups")
def add_pickup(payload: PickupCreateRequest):
    data = load_data()
    new_id = f"PU-{len(data['pickups']) + 1:03d}"
    new_pickup = {
        "pickup_id": new_id,
        "location": payload.location,
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "waste_weight_kg": payload.waste_weight_kg,
        "request_time": payload.request_time,
        "service_start": payload.service_start,
        "service_end": payload.service_end,
        "priority": payload.priority,
        "estimated_service_minutes": payload.estimated_service_minutes,
        "status": "Pending"
    }
    data["pickups"].append(new_pickup)
    save_data(data)
    return {"status": "SUCCESS", "pickup": new_pickup}

@app.post("/api/vehicles")
def add_vehicle(payload: VehicleCreateRequest):
    data = load_data()
    new_id = f"V{len(data['vehicles']) + 1:02d}"
    new_driver_id = f"DRV-{len(data['drivers']) + 1:03d}"
    
    new_driver = {
        "driver_id": new_driver_id,
        "driver_name": payload.driver_name,
        "max_work_hours": payload.driver_work_limit_hours,
        "shift_start": "07:00",
        "shift_end": "17:00"
    }
    data["drivers"].append(new_driver)
    
    new_veh = {
        "vehicle_id": new_id,
        "vehicle_number": payload.vehicle_number,
        "capacity_kg": payload.capacity_kg,
        "current_location": data["depot"]["name"],
        "latitude": data["depot"]["latitude"],
        "longitude": data["depot"]["longitude"],
        "available_from": "07:00",
        "available_until": "17:00",
        "driver_id": new_driver_id,
        "driver_name": payload.driver_name,
        "driver_work_limit_hours": payload.driver_work_limit_hours,
        "vehicle_status": payload.vehicle_status
    }
    data["vehicles"].append(new_veh)
    save_data(data)
    return {"status": "SUCCESS", "vehicle": new_veh}

@app.post("/api/override")
def perform_override(req: OverrideRequest):
    data = load_data()
    vehicle = next((v for v in data["vehicles"] if v["vehicle_id"] == req.vehicle_id), data["vehicles"][0])
    
    # If custom route stops not passed, load default optimized stops for that vehicle
    if not req.route_stops:
        optimizer = VRPOptimizer(data)
        sol = optimizer.solve("OBJECTIVE_A")
        matched_r = next((r for r in sol["routes"] if r["vehicle_id"] == req.vehicle_id), None)
        route_stops = matched_r["stops"] if matched_r else []
    else:
        route_stops = req.route_stops
        
    result = override_service.process_override(
        user=req.user,
        role=req.role,
        action_type=req.action_type,
        vehicle_id=req.vehicle_id,
        vehicle=vehicle,
        route_stops=route_stops,
        original_assignment=req.original_assignment,
        new_assignment=req.new_assignment,
        reason=req.reason,
        constraint_affected=req.constraint_affected,
        confirm_hard_override=req.confirm_hard_override
    )
    
    if not result.get("success"):
        return JSONResponse(status_code=400, content=result)
        
    return result

@app.get("/api/overrides")
def get_overrides():
    return {
        "overrides_count": len(override_service.get_logs()),
        "overrides": override_service.get_logs()
    }

@app.get("/api/edge-cases")
def get_edge_cases():
    data = load_data()
    return simulate_edge_cases(data)

# Mount Web Application Frontend Static Assets
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def serve_index():
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Combined Delivery-Pickup Optimizer API Running"}
