import math

# Earth radius in kilometers
EARTH_RADIUS_KM = 6371.0
AVERAGE_SPEED_KMH = 30.0 # 30 km/h urban traffic average speed

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the Great-Circle distance between two points in KM."""
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(EARTH_RADIUS_KM * c, 2)

def manhattan_road_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Manhattan-like road network distance approximation (approx 1.3x Haversine)."""
    h_dist = haversine_distance(lat1, lon1, lat2, lon2)
    return round(h_dist * 1.25, 2)

def estimate_travel_time_minutes(distance_km: float) -> float:
    """Estimate travel time in minutes based on distance."""
    return round((distance_km / AVERAGE_SPEED_KMH) * 60.0, 1)

def parse_time_to_minutes(time_str: str) -> int:
    """Convert HH:MM string to minutes from midnight."""
    try:
        parts = time_str.split(":")
        return int(parts[0]) * 60 + int(parts[1])
    except Exception:
        return 7 * 60 # Default 07:00 AM

def format_minutes_to_time(minutes: float) -> str:
    """Convert minutes from midnight to HH:MM format."""
    total_mins = int(round(minutes))
    hours = (total_mins // 60) % 24
    mins = total_mins % 60
    return f"{hours:02d}:{mins:02d}"
