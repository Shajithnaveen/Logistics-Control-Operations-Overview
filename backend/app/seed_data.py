import json
import math
import os
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Depot Location: Metro Central Waste Hub
DEPOT = {
    "id": "DEPOT",
    "name": "Central Depot & Waste Recycling Hub",
    "latitude": 40.7128,
    "longitude": -74.0060,
    "address": "100 Logistics Way, Central Industrial Park"
}

def generate_seed_data(seed=42):
    random.seed(seed)
    
    # 1. Generate 20 Drivers
    drivers = []
    first_names = ["John", "Sarah", "Michael", "Elena", "David", "Jessica", "Robert", "Amanda", "James", "Lisa", 
                   "William", "Karen", "Richard", "Nancy", "Joseph", "Betty", "Thomas", "Sandra", "Charles", "Ashley"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
                  "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]
    
    for i in range(1, 21):
        driver_id = f"DRV-{i:03d}"
        driver_name = f"{first_names[i-1]} {last_names[i-1]}"
        # Work limit between 7.0 and 9.5 hours
        limit_hours = round(random.choice([7.0, 8.0, 8.5, 9.0, 9.5]), 1)
        drivers.append({
            "driver_id": driver_id,
            "driver_name": driver_name,
            "max_work_hours": limit_hours,
            "shift_start": "07:00",
            "shift_end": "17:00",
            "phone": f"+1-555-01{i:02d}"
        })

    # 2. Generate 20 Vehicles
    vehicles = []
    statuses = ["Available", "Available", "Available", "Available", "Assigned", "In Transit", "Available"]
    for i in range(1, 21):
        veh_id = f"V{i:02d}"
        capacity = random.choice([4000, 5000, 6500, 8000, 10000, 12000]) # kg
        status = statuses[(i - 1) % len(statuses)]
        vehicles.append({
            "vehicle_id": veh_id,
            "vehicle_number": f"WCV-{1000 + i}",
            "capacity_kg": capacity,
            "current_location": DEPOT["name"],
            "latitude": DEPOT["latitude"],
            "longitude": DEPOT["longitude"],
            "available_from": "07:00",
            "available_until": "17:00",
            "driver_id": drivers[i-1]["driver_id"],
            "driver_name": drivers[i-1]["driver_name"],
            "driver_work_limit_hours": drivers[i-1]["max_work_hours"],
            "vehicle_status": status
        })

    # 3. Generate 100 Delivery Loads
    # Deliveries are spread across urban zone (lat 40.65 to 40.78, lng -74.12 to -73.92)
    deliveries = []
    streets = ["Main St", "Broadway", "Market St", "Oak Ave", "Pine St", "Maple Ave", "Cedar St", "Elm St", "Washington St", "Park Ave",
               "River Rd", "Industrial Pkwy", "Commercial Blvd", "Highland Ave", "Sunset Dr", "Ocean Ave", "Franklin St", "Center St"]
    
    for i in range(1, 101):
        del_id = f"DEL-{i:03d}"
        lat = round(40.7128 + random.uniform(-0.08, 0.08), 4)
        lng = round(-74.0060 + random.uniform(-0.10, 0.10), 4)
        load = random.choice([250, 400, 500, 750, 1000, 1200, 1500, 1800, 2200]) # kg
        
        # Service windows: morning or afternoon
        if random.random() < 0.6:
            start_hour = random.randint(7, 10)
            end_hour = start_hour + random.randint(2, 4)
        else:
            start_hour = random.randint(11, 14)
            end_hour = min(17, start_hour + random.randint(2, 4))
            
        priority = random.choices(["Normal", "High", "Critical"], weights=[0.7, 0.2, 0.1])[0]
        street = random.choice(streets)
        num = random.randint(100, 999)
        
        deliveries.append({
            "delivery_id": del_id,
            "location": f"{num} {street}",
            "latitude": lat,
            "longitude": lng,
            "load_kg": load,
            "service_start": f"{start_hour:02d}:00",
            "service_end": f"{end_hour:02d}:00",
            "priority": priority,
            "estimated_service_minutes": random.choice([10, 15, 20]),
            "status": "Pending"
        })

    # 4. Generate 200 Pickup Requests
    # Pickups are located near delivery locations or scattered in municipal waste collection zones
    pickups = []
    pickup_types = ["Commercial Recycling", "Organic Waste", "Hazardous E-Waste", "Industrial Scrap", "Municipal Solid Waste", "Bulk Dumpster"]
    
    for i in range(1, 201):
        pik_id = f"PU-{i:03d}"
        
        # 60% of pickups are purposely placed near delivery locations to test spatial clustering optimization
        if random.random() < 0.6 and deliveries:
            ref_del = random.choice(deliveries)
            lat = round(ref_del["latitude"] + random.uniform(-0.015, 0.015), 4)
            lng = round(ref_del["longitude"] + random.uniform(-0.015, 0.015), 4)
        else:
            lat = round(40.7128 + random.uniform(-0.09, 0.09), 4)
            lng = round(-74.0060 + random.uniform(-0.11, 0.11), 4)
            
        weight = random.choice([150, 300, 500, 800, 1200, 1500, 2000, 2500, 3000]) # kg
        
        # Priority distribution: Normal (50%), Urgent (35%), Critical (15%)
        priority = random.choices(["Normal", "Urgent", "Critical"], weights=[0.50, 0.35, 0.15])[0]
        
        # Service windows: urgent ones have tighter windows
        if priority in ["Urgent", "Critical"]:
            start_h = random.randint(8, 13)
            end_h = start_h + random.choice([1, 2]) # tight 1-2 hour window
        else:
            start_h = random.randint(8, 12)
            end_h = min(17, start_h + random.randint(3, 5))
            
        street = random.choice(streets)
        num = random.randint(100, 999)
        ptype = random.choice(pickup_types)
        
        pickups.append({
            "pickup_id": pik_id,
            "location": f"{num} {street} ({ptype})",
            "latitude": lat,
            "longitude": lng,
            "waste_weight_kg": weight,
            "request_time": f"{max(7, start_h - 1):02d}:30",
            "service_start": f"{start_h:02d}:00",
            "service_end": f"{end_h:02d}:00",
            "priority": priority,
            "estimated_service_minutes": random.choice([12, 15, 20, 25]),
            "status": "Pending"
        })

    dataset = {
        "depot": DEPOT,
        "drivers": drivers,
        "vehicles": vehicles,
        "deliveries": deliveries,
        "pickups": pickups
    }
    
    with open(os.path.join(DATA_DIR, "seed_dataset.json"), "w") as f:
        json.dump(dataset, f, indent=2)
        
    print(f"Generated realistic validation dataset: {len(vehicles)} vehicles, {len(drivers)} drivers, {len(deliveries)} deliveries, {len(pickups)} pickups.")
    return dataset

if __name__ == "__main__":
    generate_seed_data()
