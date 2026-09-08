import pytest
import os
import sys

# Add project root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.seed_data import generate_seed_data
from app.optimizer.baseline import calculate_baseline
from app.optimizer.vrp_solver import VRPOptimizer
from app.optimizer.constraints import ConstraintChecker
from app.services.overrides import OverrideAuditLogService
from app.services.edge_cases import simulate_edge_cases

@pytest.fixture
def sample_dataset():
    return generate_seed_data(seed=123)

def test_dataset_generation(sample_dataset):
    assert len(sample_dataset["vehicles"]) == 20
    assert len(sample_dataset["drivers"]) == 20
    assert len(sample_dataset["deliveries"]) == 100
    assert len(sample_dataset["pickups"]) == 200
    assert sample_dataset["depot"]["id"] == "DEPOT"

def test_baseline_calculation(sample_dataset):
    baseline = calculate_baseline(sample_dataset)
    metrics = baseline["metrics"]
    
    assert metrics["empty_kilometres"] > 0
    assert metrics["total_pickups_completed"] == 0 # 0 pickups completed in delivery-only baseline
    assert metrics["pending_urgent_pickups"] > 0
    assert len(baseline["routes"]) == 20

def test_objective_a_empty_km_reduction(sample_dataset):
    optimizer = VRPOptimizer(sample_dataset)
    sol_a = optimizer.solve("OBJECTIVE_A")
    metrics_a = sol_a["metrics"]
    
    baseline = calculate_baseline(sample_dataset)
    baseline_empty = baseline["metrics"]["empty_kilometres"]
    
    # Objective A must achieve reduced empty return distance
    assert metrics_a["empty_kilometres"] <= baseline_empty
    assert metrics_a["empty_km_reduction_pct"] > 0.0
    assert metrics_a["total_pickups_completed"] > 0

def test_objective_b_urgent_pickups(sample_dataset):
    optimizer = VRPOptimizer(sample_dataset)
    sol_b = optimizer.solve("OBJECTIVE_B")
    metrics_b = sol_b["metrics"]
    
    # Objective B must complete urgent pickups
    assert metrics_b["urgent_pickups_completed"] > 0
    assert metrics_b["urgent_pickup_completion_rate"] > 50.0

def test_hard_capacity_constraint(sample_dataset):
    veh = sample_dataset["vehicles"][0] # capacity e.g. 4000 kg
    # Overload stops
    overload_stops = [
        {"type": "DEPOT", "latitude": 40.7128, "longitude": -74.0060},
        {"type": "DELIVERY", "load_kg": 9000, "latitude": 40.7200, "longitude": -74.0100},
        {"type": "DEPOT", "latitude": 40.7128, "longitude": -74.0060}
    ]
    hard_v, soft_v, details = ConstraintChecker.evaluate_route(veh, overload_stops)
    assert len(hard_v) > 0
    assert "Capacity Exceeded" in hard_v[0]
    assert details["safe_assignment"] is False

def test_hard_workload_constraint(sample_dataset):
    veh = dict(sample_dataset["vehicles"][0])
    veh["driver_work_limit_hours"] = 2.0 # tight 2 hour limit
    
    long_stops = [
        {"type": "DEPOT", "latitude": 40.7128, "longitude": -74.0060},
        {"type": "DELIVERY", "load_kg": 100, "latitude": 40.8500, "longitude": -74.2000, "estimated_service_minutes": 120},
        {"type": "DEPOT", "latitude": 40.7128, "longitude": -74.0060}
    ]
    hard_v, soft_v, details = ConstraintChecker.evaluate_route(veh, long_stops)
    assert len(hard_v) > 0
    assert "Driver Workload Limit Exceeded" in hard_v[0]
    assert details["safe_assignment"] is False

def test_manual_override_audit_logging(sample_dataset):
    service = OverrideAuditLogService()
    veh = sample_dataset["vehicles"][0]
    stops = [
        {"type": "DEPOT", "latitude": 40.7128, "longitude": -74.0060},
        {"type": "DELIVERY", "load_kg": 500, "latitude": 40.7200, "longitude": -74.0100},
        {"type": "DEPOT", "latitude": 40.7128, "longitude": -74.0060}
    ]
    
    # 1. Anonymous override should fail
    anon_res = service.process_override(
        user="",
        role="Dispatcher",
        action_type="REASSIGN",
        vehicle_id=veh["vehicle_id"],
        vehicle=veh,
        route_stops=stops,
        original_assignment="V01",
        new_assignment="V02",
        reason="Manual change",
        constraint_affected="Soft"
    )
    assert anon_res["success"] is False
    
    # 2. Authorized valid override should succeed and log
    auth_res = service.process_override(
        user="Dispatcher_John",
        role="Operations Manager",
        action_type="REASSIGN_VEHICLE",
        vehicle_id=veh["vehicle_id"],
        vehicle=veh,
        route_stops=stops,
        original_assignment="V01",
        new_assignment="V02",
        reason="Customer escalation priority shift",
        constraint_affected="Soft Distance Penalty"
    )
    assert auth_res["success"] is True
    assert len(service.get_logs()) == 1
    assert service.get_logs()[0]["user"] == "Dispatcher_John"

def test_edge_cases_simulation(sample_dataset):
    cases = simulate_edge_cases(sample_dataset)
    assert len(cases) == 5
    for c in cases:
        assert c["status"] == "PASS"
