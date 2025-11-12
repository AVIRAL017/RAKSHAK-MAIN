# Emergency Response System - RAKSHAK

## Overview

The Emergency Response System is a comprehensive enhancement to RAKSHAK that integrates critical emergency assets (hospitals and police stations) onto the map and dynamically pre-positions ambulances at high-risk accident hotspots.

## Features

### 1. Hospital Integration
- **Data Source**: Local CSV file (`geocode_health_centre.csv`) containing 10,000+ health facilities
- **Facility Types**: District Hospitals (dis_h), Community Health Centers (chc), Primary Health Centers (phc)
- **Coverage**: Pan-India coverage with precise latitude/longitude coordinates
- **Map Display**: Red "plus sign" markers with detailed popup information

### 2. Police Station Integration
- **Data Source**: OpenStreetMap (OSM) Overpass API for real-time data
- **Coverage**: Dynamic fetching based on map center with configurable radius
- **Map Display**: Blue "shield" markers with station details
- **Data**: Real police station locations from genuine public mapping data

### 3. Ambulance Pre-positioning System
- **Algorithm**: Intelligent placement based on accident hotspot risk levels
- **Criteria**: Filters for High and Medium risk hotspots only
- **Assignment**: Each ambulance is assigned to the nearest hospital
- **Metrics**: 
  - Distance to assigned hospital (km)
  - Estimated response time (minutes)
  - Risk level of the hotspot
- **Map Display**: Orange pulsing ambulance markers with comprehensive information

### 4. Interactive Layer Control
- **Toggle Layers**: Independent show/hide controls for:
  - Accident Hotspots (original feature)
  - Hospitals
  - Police Stations
  - Pre-positioned Ambulances
- **User-Friendly UI**: Collapsible layer control menu in top-right corner
- **Icons**: Clear visual indicators for each layer type

## Technical Architecture

### Backend Components

#### 1. Emergency Service (`src/services/emergency_service.py`)
```python
class EmergencyService:
    - _load_hospitals()              # Parse CSV data
    - fetch_police_stations()        # Query OSM Overpass API
    - calculate_distance()           # Haversine formula implementation
    - find_nearest_hospital()        # Spatial search algorithm
    - calculate_ambulance_placements() # Pre-positioning logic
```

**Key Functions:**
- **Distance Calculation**: Uses Haversine formula for accurate geographic distance
- **Nearest Hospital Search**: Efficiently finds closest hospital to any coordinate
- **Ambulance Algorithm**: 
  1. Filters hotspots for High/Medium risk
  2. For each hotspot, calculates distance to all hospitals
  3. Assigns nearest hospital
  4. Estimates response time (assumes 40 km/h average speed)

#### 2. API Endpoints (`src/api.py`)

**GET /api/emergency/hospitals**
- Returns: List of hospitals with coordinates and metadata
- Query params: `limit` (optional)

**GET /api/emergency/police-stations**
- Returns: List of police stations
- Query params: `lat`, `lon`, `radius` (for fetching new data)

**GET /api/emergency/ambulances**
- Returns: List of pre-positioned ambulances
- Query params: `recalculate` (boolean)

**POST /api/emergency/initialize**
- Initializes entire emergency system
- Body: `{ "lat": float, "lon": float, "radius": float }`

### Frontend Components

#### 1. Emergency Layers Module (`static/js/emergency-layers.js`)

**Key Features:**
- Layer management (create, display, toggle)
- Custom icon creation for each asset type
- Popup content generation with rich information
- Async data loading from API endpoints
- Integration with main map instance

**Icon Design:**
- **Hospital**: Red circle with plus sign (fa-plus-square)
- **Police**: Blue circle with shield (fa-shield-alt)
- **Ambulance**: Orange circle with ambulance icon (fa-ambulance), with pulse animation

#### 2. Layer Control UI
- Positioned in top-right corner of map
- Collapsible header with toggle button
- Checkbox controls for each layer
- Color-coded icons matching map markers

## Data Flow

```
1. Application Start
   └─> Initialize Map
       └─> Initialize Emergency Layers
           ├─> Load Hospitals (from CSV via API)
           ├─> Fetch Police Stations (from OSM via API)
           └─> Calculate Ambulance Placements (from hotspots via API)

2. Display on Map
   ├─> Hospital Layer: Red plus markers
   ├─> Police Layer: Blue shield markers
   └─> Ambulance Layer: Orange ambulance markers (pulsing)

3. User Interaction
   ├─> Click marker → Show detailed popup
   └─> Toggle layer → Show/hide markers
```

## Installation & Setup

### Prerequisites
- Python 3.8+
- Flask
- Required Python packages in `requirements.txt`
- Internet connection (for police station data)

### Setup Steps

1. **Ensure Data File Exists**
   ```bash
   # Verify geocode_health_centre.csv is present in project root
   ls geocode_health_centre.csv
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Test the System**
   ```bash
   python test_emergency_system.py
   ```

4. **Run the Application**
   ```bash
   python run.py
   ```

5. **Access the Application**
   - Open browser to `http://127.0.0.1:5000`
   - Map should load with emergency layers visible
   - Layer control visible in top-right corner

## API Usage Examples

### Get Hospitals
```javascript
fetch('/api/emergency/hospitals?limit=100')
  .then(response => response.json())
  .then(data => {
    console.log(`Loaded ${data.data.hospitals.length} hospitals`);
  });
```

### Get Police Stations
```javascript
// Fetch around Delhi with 50km radius
fetch('/api/emergency/police-stations?lat=28.6139&lon=77.2090&radius=50')
  .then(response => response.json())
  .then(data => {
    console.log(`Fetched ${data.data.police_stations.length} stations`);
  });
```

### Get Ambulance Placements
```javascript
fetch('/api/emergency/ambulances?recalculate=true')
  .then(response => response.json())
  .then(data => {
    console.log(`Calculated ${data.data.ambulances.length} placements`);
  });
```

### Initialize Emergency System
```javascript
fetch('/api/emergency/initialize', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    lat: 28.6139,
    lon: 77.2090,
    radius: 50
  })
})
.then(response => response.json())
.then(data => console.log('System initialized:', data));
```

## Ambulance Pre-positioning Algorithm

### Logic Flow
```
1. Get all accident hotspots
2. Filter for High and Medium risk levels
3. For each high/medium risk hotspot:
   a. Calculate distance to every hospital
   b. Find hospital with minimum distance
   c. Create ambulance placement record:
      - Location: Hotspot coordinates
      - Assigned Hospital: Nearest hospital details
      - Distance: km from hotspot to hospital
      - Response Time: Estimated minutes (distance / 40 km/h * 60)
4. Return list of ambulance placements
```

### Example Output
```json
{
  "id": "ambulance_delhi_connaught_place",
  "hotspot_name": "Connaught Place",
  "latitude": 28.6315,
  "longitude": 77.2167,
  "risk_level": "High",
  "assigned_hospital": {
    "name": "Ram Manohar Lohia Hospital",
    "latitude": 28.6394,
    "longitude": 77.2144,
    "district": "New Delhi"
  },
  "distance_to_hospital": 1.2,
  "response_time_estimate": 1.8
}
```

## Layer Control Features

### Toggle Operations
- **Check/Uncheck**: Show or hide entire layer
- **Independent**: Each layer can be toggled separately
- **State Persistence**: Layer visibility maintained during session

### Visual Feedback
- Checked checkbox = Layer visible
- Unchecked checkbox = Layer hidden
- Icon color matches marker color on map

## Performance Considerations

### Optimization Strategies
1. **Hospital Data**: Loaded once at startup, cached in memory
2. **Police Stations**: Fetched on-demand, cached per region
3. **Ambulance Placements**: Calculated once, recalculated on request
4. **Map Markers**: Efficient clustering for dense areas
5. **API Calls**: Batched and debounced to minimize requests

### Scalability
- Hospital data: 10,000+ records handled efficiently
- Police stations: Configurable radius limits API load
- Ambulance placements: O(n*m) complexity where n=hotspots, m=hospitals
- Acceptable performance for typical use cases (<1000 hotspots)

## Future Enhancements

### Potential Improvements
1. **Real-time Updates**: WebSocket integration for live data
2. **Route Optimization**: Best path for ambulance to hospital
3. **Load Balancing**: Distribute ambulances across multiple hospitals
4. **Predictive Analytics**: ML-based placement optimization
5. **Traffic Integration**: Real-time traffic for response times
6. **Mobile Notifications**: Alert nearby ambulances to incidents
7. **Resource Management**: Track ambulance availability status

## Troubleshooting

### Common Issues

**Hospital data not loading**
- Check if `geocode_health_centre.csv` exists in project root
- Verify CSV file format and encoding (UTF-8)

**Police stations not appearing**
- Requires internet connection
- OpenStreetMap API may have rate limits
- Try increasing timeout or reducing radius

**Ambulances not showing**
- Requires hotspots to be loaded first
- Check browser console for API errors
- Verify hotspot data has risk_level or severity field

**Layer control not visible**
- Check if emergency-layers.js is loaded
- Verify EmergencyLayers.init() is called
- Check browser console for JavaScript errors

## Testing

Run the test script to verify all components:
```bash
python test_emergency_system.py
```

Expected output:
```
Testing Emergency Response System
1. Testing Hospital Data Loading...
   ✓ Loaded 10000+ hospitals
2. Testing Distance Calculation...
   ✓ Distance Delhi to Mumbai: 1140.52 km
3. Testing Nearest Hospital Search...
   ✓ Nearest hospital found
4. Testing Ambulance Pre-positioning...
   ✓ Calculated ambulance placements
5. Testing Police Station Fetching...
   ✓ Fetched police stations from OpenStreetMap
```

## Credits

- **Hospital Data**: Government of India Health Infrastructure Database
- **Police Station Data**: OpenStreetMap Community
- **Distance Calculations**: Haversine Formula
- **Map Icons**: Font Awesome Icon Library
- **Base Map**: Leaflet.js with OpenStreetMap tiles

## License

This emergency response system is part of RAKSHAK - SafeRoute Navigator v2.0

---

**Last Updated**: November 2025
**Version**: 1.0.0
**Status**: Production Ready ✓
