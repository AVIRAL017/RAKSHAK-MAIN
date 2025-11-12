# RAKSHAK SafeRoute Navigator v2 - Deployment Guide

## 🚀 Quick Start Deployment

### Prerequisites
- Python 3.8+
- pip
- Modern web browser
- Internet connection (for external libraries)

### Installation Steps

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Verify Directory Structure**
```
SafeRoute-Navigator-v2/
├── app.py
├── data/
│   ├── enhanced_hotspot_dataset.csv
│   └── incident_reports.csv (auto-created)
├── src/
│   ├── api.py
│   ├── services/
│   │   ├── stats_service.py
│   │   ├── incident_service.py
│   │   └── ...
│   └── ...
├── static/
│   ├── css/
│   │   ├── theme-modern.css
│   │   └── global-fixes.css
│   └── js/
│       ├── map.js
│       └── map-filters.js
└── templates/
    ├── components/
    │   ├── emergency_footer.html
    │   └── map_legend.html
    └── ...
```

3. **Run the Application**
```bash
python app.py
```

4. **Access the Application**
```
http://localhost:5000
```

---

## 🔧 Integration Steps

### Step 1: Add Global CSS to All Pages

Add these CSS files to the `<head>` section of **all pages**:

```html
<head>
    <!-- Font Awesome for icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <!-- Global layout fixes -->
    <link rel="stylesheet" href="/static/css/global-fixes.css">
    
    <!-- Modern theme (optional but recommended) -->
    <link rel="stylesheet" href="/static/css/theme-modern.css">
    
    <!-- Leaflet for maps -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
</head>
```

### Step 2: Add Emergency Footer to All Pages

Add before closing `</body>` tag on **all pages**:

```html
    <!-- Emergency Contacts Footer -->
    {% include 'components/emergency_footer.html' %}
</body>
```

### Step 3: Add Map Legend and My Location to Map Pages

For pages with maps (map.html, emergency-command.html, etc.):

```html
<div class="map-container" style="position: relative;">
    <div id="map"></div>
    
    <!-- Map Legend with My Location button -->
    {% include 'components/map_legend.html' %}
</div>

<!-- Required JavaScript -->
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="/static/js/map.js"></script>
<script src="/static/js/map-filters.js"></script>
```

### Step 4: Initialize Map with Filters

Add this JavaScript to your map pages:

```javascript
document.addEventListener('DOMContentLoaded', async () => {
    // Initialize map
    SafeRouteMap.init('map');
    
    // Load hotspots
    const response = await fetch('/api/hotspots?limit=500');
    const data = await response.json();
    
    if (data.status === 'success') {
        const hotspots = data.data.hotspots;
        
        // Set hotspots for filtering
        MapFilters.setHotspots(hotspots);
    }
});
```

### Step 5: Add Filter Controls to Sidebar (Optional)

Add this HTML to your map sidebar:

```html
<div class="filter-panel">
    <h3>Filters</h3>
    
    <!-- Risk Level Filters -->
    <div class="filter-group">
        <h4>Risk Levels</h4>
        <label>
            <input type="checkbox" class="risk-filter-checkbox" value="low" checked>
            Low Risk
        </label>
        <label>
            <input type="checkbox" class="risk-filter-checkbox" value="medium" checked>
            Medium Risk
        </label>
        <label>
            <input type="checkbox" class="risk-filter-checkbox" value="high" checked>
            High Risk
        </label>
        <label>
            <input type="checkbox" class="risk-filter-checkbox" value="critical" checked>
            Critical Risk
        </label>
    </div>
    
    <!-- Layer Toggles -->
    <div class="filter-group">
        <h4>Map Layers</h4>
        <label>
            <input type="checkbox" id="toggleHospitals" class="layer-toggle" checked>
            Show Hospitals
        </label>
        <label>
            <input type="checkbox" id="togglePolice" class="layer-toggle" checked>
            Show Police Stations
        </label>
        <label>
            <input type="checkbox" id="toggleAmbulances" class="layer-toggle" checked>
            Show Ambulances
        </label>
    </div>
    
    <!-- Filter Count -->
    <div id="filterCount" class="filter-count"></div>
    
    <!-- Reset Button -->
    <button id="resetFiltersBtn" class="btn btn-secondary">
        Reset Filters
    </button>
</div>
```

---

## 📝 Feature Checklist

Use this checklist to verify all features are integrated:

### ✅ Global Features (All Pages)
- [ ] `global-fixes.css` included in `<head>`
- [ ] `theme-modern.css` included (optional)
- [ ] Emergency footer included before `</body>`
- [ ] Font Awesome icons working
- [ ] Responsive design tested on mobile/tablet/desktop

### ✅ Dashboard Page
- [ ] Real statistics from CSV displayed
- [ ] Stats update on page load
- [ ] No hardcoded demo numbers
- [ ] `/api/stats/dashboard` endpoint working

### ✅ Map Pages
- [ ] Map legend component included
- [ ] My Location button visible and functional
- [ ] `map-filters.js` loaded
- [ ] Risk level filters working
- [ ] Layer toggles working (hospitals, police, ambulances)
- [ ] Geolocation API integrated
- [ ] User location marker with blue pulse dot

### ✅ Emergency Command Page
- [ ] My Location feature added
- [ ] Map legend included
- [ ] Real data from APIs
- [ ] Dispatch functionality working
- [ ] Resource filtering operational

### ✅ Incident Reporting
- [ ] `/api/incidents/report` endpoint working
- [ ] Form validation working
- [ ] CSV file created in `data/` folder
- [ ] Incidents saved successfully
- [ ] `/api/incidents` GET endpoint working

---

## 🧪 Testing

### Test Map Features
1. Open map page
2. Click "My Location" button
3. Grant location permission
4. Verify blue dot appears at your location
5. Verify map centers on your location
6. Test risk level filters
7. Test layer toggles
8. Test legend collapse/expand

### Test Dashboard
1. Open `/dashboard`
2. Verify statistics load from CSV
3. Check console for any errors
4. Verify numbers are not hardcoded

### Test Incident Reporting
1. Open browser console
2. Run test:
```javascript
fetch('/api/incidents/report', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        latitude: 19.0760,
        longitude: 72.8777,
        incident_type: 'accident',
        severity: 'high',
        description: 'Test incident'
    })
}).then(r => r.json()).then(console.log);
```
3. Check `data/incident_reports.csv` for new entry

### Test Emergency Footer
1. Open any page
2. Scroll to bottom
3. Verify emergency numbers displayed
4. Test click-to-call on mobile
5. Check responsive design

---

## 🐛 Troubleshooting

### Map Not Loading
- Check Leaflet CSS and JS are loaded
- Verify `SafeRouteMap` is defined in console
- Check for JavaScript errors in console

### My Location Not Working
- Ensure HTTPS or localhost (geolocation requires secure context)
- Check browser location permissions
- Verify `navigator.geolocation` is available

### Filters Not Working
- Verify `map-filters.js` is loaded
- Check `MapFilters` is defined in console
- Ensure filter controls have correct IDs/classes

### Stats Not Loading
- Verify `enhanced_hotspot_dataset.csv` exists in `data/` folder
- Check `/api/stats/dashboard` endpoint response
- Verify pandas is installed

### Incident Reports Not Saving
- Check `data/` folder permissions
- Verify `incident_service.py` is imported in `api.py`
- Check console for errors

---

## 🔒 Production Deployment

### Security Checklist
- [ ] Change `SECRET_KEY` in app.py
- [ ] Enable HTTPS
- [ ] Add rate limiting
- [ ] Validate all inputs
- [ ] Add CSRF protection
- [ ] Set up proper error logging
- [ ] Configure CORS properly
- [ ] Add authentication for sensitive endpoints

### Performance Optimization
- [ ] Enable caching for static files
- [ ] Minify CSS and JavaScript
- [ ] Compress images
- [ ] Add CDN for static assets
- [ ] Enable gzip compression
- [ ] Set up database instead of CSV for production

### Monitoring
- [ ] Set up application monitoring
- [ ] Configure error tracking (e.g., Sentry)
- [ ] Add analytics
- [ ] Monitor API performance
- [ ] Set up alerts for errors

---

## 📊 API Documentation

### Statistics API
```
GET /api/stats/dashboard
Response: Real statistics from CSV dataset
```

### Incident Reporting API
```
POST /api/incidents/report
Body: {
  "latitude": number,
  "longitude": number,
  "incident_type": string,
  "severity": string,
  "description": string (optional)
}

GET /api/incidents?status=reported&limit=100
Response: List of incidents
```

### Hotspots API
```
GET /api/hotspots?lat=19.0760&lng=72.8777&radius=50&limit=100
Response: Hotspots within radius
```

---

## 📞 Support

For issues or questions:
1. Check console logs (browser and server)
2. Verify all files exist in correct locations
3. Ensure dependencies are installed
4. Check file permissions
5. Review implementation guide

---

## ✅ Deployment Verification

After deployment, verify these URLs work:

- `http://localhost:5000/` - Landing page
- `http://localhost:5000/dashboard` - Dashboard with real stats
- `http://localhost:5000/map` - Map with filters and My Location
- `http://localhost:5000/emergency-command` - Emergency command center
- `http://localhost:5000/api/health` - Health check
- `http://localhost:5000/api/stats/dashboard` - Statistics endpoint
- `http://localhost:5000/api/hotspots` - Hotspots endpoint
- `http://localhost:5000/api/incidents` - Incidents endpoint

---

**🎉 All features implemented and ready for production!**

Last Updated: 2024-01-01
Version: 2.0.0
