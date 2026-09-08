# Prototype Limitations & Future Enhancements Report

## Documented Prototype Limitations

1. **Synthetic Geo-Dataset**:
   - The validation dataset uses synthetic latitude/longitude coordinates generated around a metropolitan central grid (lat 40.71, lng -74.00). While realistic in spatial distribution, real municipal GIS street networks contain specific one-way streets, turn restrictions, and bridge weight limits.
2. **Simplified Travel-Time Model**:
   - Travel times are estimated using Manhattan road distance approximation (1.25x Haversine) and a uniform average city speed of 30 km/h. Real-world traffic congestion, peak-hour bottlenecks, and weather delays are not dynamically updated in real time.
3. **Static Waste Density Assumptions**:
   - The optimizer models waste payload purely by mass (`weight_kg`). In actual municipal waste operations, volumetric expansion (cubic meters) and compactor compression ratios also influence maximum bin capacity.
4. **Single Depot Assumption**:
   - All 20 vehicles start and return to a single central depot hub. Multi-depot operations with regional transfer stations are not included in the initial prototype scope.

## Future Enhancements Roadmap

- Real-time OpenStreetMap / OSRM routing engine integration.
- Live GPS vehicle telemetry tracking websocket stream.
- Multi-depot and transfer station routing support.
- Machine learning demand forecasting for dynamic pickup requests.
