/**
 * RAKSHAK - Emergency Response Layers
 * Manages hospitals, police stations, and ambulance layers on the map
 */

const EmergencyLayers = {
    // Layer groups
    layers: {
        hospitals: null,
        policeStations: null,
        ambulances: null
    },
    
    // Data storage
    data: {
        hospitals: [],
        policeStations: [],
        ambulances: []
    },
    
    // Layer visibility
    visibility: {
        hospitals: true,
        policeStations: true,
        ambulances: true,
        hotspots: true
    },
    
    // Layer control
    layerControl: null,
    
    /**
     * Initialize emergency layers
     */
    init(map) {
        console.log('Initializing Emergency Response Layers...');
        
        if (!map) {
            console.error('Map instance required for emergency layers');
            return;
        }
        
        this.map = map;
        
        // Create layer groups
        this.layers.hospitals = L.layerGroup().addTo(map);
        this.layers.policeStations = L.layerGroup().addTo(map);
        this.layers.ambulances = L.layerGroup().addTo(map);
        
        // Add layer control
        this.addLayerControl();
        
        // Load initial data
        this.loadAllEmergencyData();
        
        console.log('Emergency Response Layers initialized');
    },
    
    /**
     * Add layer control menu to map
     */
    addLayerControl() {
        // Create layer control HTML
        const controlHtml = `
            <div class="emergency-layer-control" id="emergencyLayerControl">
                <div class="control-header">
                    <i class="fas fa-layer-group"></i>
                    <span>Map Layers</span>
                    <button class="toggle-control" id="toggleLayerControl">
                        <i class="fas fa-chevron-up"></i>
                    </button>
                </div>
                <div class="control-body">
                    <div class="layer-item">
                        <label>
                            <input type="checkbox" id="layer-hotspots" checked>
                            <i class="fas fa-exclamation-triangle" style="color: #ff6b6b;"></i>
                            <span>Accident Hotspots</span>
                        </label>
                    </div>
                    <div class="layer-item">
                        <label>
                            <input type="checkbox" id="layer-hospitals" checked>
                            <i class="fas fa-plus-square" style="color: #e74c3c;"></i>
                            <span>Hospitals</span>
                        </label>
                    </div>
                    <div class="layer-item">
                        <label>
                            <input type="checkbox" id="layer-police" checked>
                            <i class="fas fa-shield-alt" style="color: #3498db;"></i>
                            <span>Police Stations</span>
                        </label>
                    </div>
                    <div class="layer-item">
                        <label>
                            <input type="checkbox" id="layer-ambulances" checked>
                            <i class="fas fa-ambulance" style="color: #f39c12;"></i>
                            <span>Pre-positioned Ambulances</span>
                        </label>
                    </div>
                </div>
            </div>
        `;
        
        // Create control element
        const controlDiv = document.createElement('div');
        controlDiv.className = 'leaflet-control-layers leaflet-control';
        controlDiv.innerHTML = controlHtml;
        
        // Add to map
        const mapContainer = this.map.getContainer();
        mapContainer.appendChild(controlDiv);
        
        // Add event listeners
        this.setupLayerControlEvents();
        
        // Add CSS if not already present
        this.addLayerControlStyles();
    },
    
    /**
     * Setup layer control event listeners
     */
    setupLayerControlEvents() {
        // Toggle control visibility
        const toggleBtn = document.getElementById('toggleLayerControl');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                const control = document.getElementById('emergencyLayerControl');
                const body = control.querySelector('.control-body');
                const icon = toggleBtn.querySelector('i');
                
                body.classList.toggle('collapsed');
                icon.classList.toggle('fa-chevron-up');
                icon.classList.toggle('fa-chevron-down');
            });
        }
        
        // Layer toggles
        const toggles = {
            'layer-hotspots': () => this.toggleHotspotsLayer(),
            'layer-hospitals': () => this.toggleLayer('hospitals'),
            'layer-police': () => this.toggleLayer('policeStations'),
            'layer-ambulances': () => this.toggleLayer('ambulances')
        };
        
        Object.entries(toggles).forEach(([id, handler]) => {
            const checkbox = document.getElementById(id);
            if (checkbox) {
                checkbox.addEventListener('change', handler);
            }
        });
    },
    
    /**
     * Toggle layer visibility
     */
    toggleLayer(layerName) {
        if (!this.layers[layerName]) return;
        
        const checkbox = document.getElementById(`layer-${layerName === 'policeStations' ? 'police' : layerName}`);
        const isVisible = checkbox.checked;
        
        if (isVisible) {
            this.map.addLayer(this.layers[layerName]);
        } else {
            this.map.removeLayer(this.layers[layerName]);
        }
        
        this.visibility[layerName] = isVisible;
        console.log(`${layerName} layer: ${isVisible ? 'shown' : 'hidden'}`);
    },
    
    /**
     * Toggle hotspots layer
     */
    toggleHotspotsLayer() {
        const checkbox = document.getElementById('layer-hotspots');
        const isVisible = checkbox.checked;
        
        // Access the hotspots layer from SafeRouteMap
        if (window.SafeRouteMap && SafeRouteMap.layers && SafeRouteMap.layers.hotspots) {
            if (isVisible) {
                this.map.addLayer(SafeRouteMap.layers.hotspots);
            } else {
                this.map.removeLayer(SafeRouteMap.layers.hotspots);
            }
        }
        
        this.visibility.hotspots = isVisible;
        console.log(`Hotspots layer: ${isVisible ? 'shown' : 'hidden'}`);
    },
    
    /**
     * Load all emergency data
     */
    async loadAllEmergencyData() {
        try {
            // Get map center
            const center = this.map.getCenter();
            
            // Initialize emergency system
            await this.initializeEmergencySystem(center.lat, center.lng);
            
            // Load all layers
            await Promise.all([
                this.loadHospitals(),
                this.loadPoliceStations(),
                this.loadAmbulances()
            ]);
            
            console.log('All emergency data loaded successfully');
        } catch (error) {
            console.error('Error loading emergency data:', error);
        }
    },
    
    /**
     * Initialize emergency system
     */
    async initializeEmergencySystem(lat, lon) {
        try {
            const response = await fetch('/api/emergency/initialize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    lat: lat,
                    lon: lon,
                    radius: 50
                })
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                console.log('Emergency system initialized:', result.data);
            }
        } catch (error) {
            console.error('Error initializing emergency system:', error);
        }
    },
    
    /**
     * Load hospitals
     */
    async loadHospitals() {
        try {
            const response = await fetch('/api/emergency/hospitals?limit=500');
            const result = await response.json();
            
            if (result.status === 'success') {
                this.data.hospitals = result.data.hospitals;
                this.displayHospitals(this.data.hospitals);
                console.log(`Loaded ${this.data.hospitals.length} hospitals`);
            }
        } catch (error) {
            console.error('Error loading hospitals:', error);
        }
    },
    
    /**
     * Load police stations (nationwide cached dataset)
     */
    async loadPoliceStations() {
        try {
            const response = await fetch(`/api/emergency/police-stations?limit=1000`);
            const result = await response.json();
            
            if (result.status === 'success') {
                this.data.policeStations = result.data.police_stations;
                this.displayPoliceStations(this.data.policeStations);
                console.log(`Loaded ${this.data.policeStations.length} police stations`);
            }
        } catch (error) {
            console.error('Error loading police stations:', error);
        }
    },
    
    /**
     * Load ambulances
     */
    async loadAmbulances() {
        try {
            // Only recalculate on first load if not cached
            const response = await fetch('/api/emergency/ambulances?max_placements=30');
            const result = await response.json();
            
            if (result.status === 'success') {
                this.data.ambulances = result.data.ambulances;
                this.displayAmbulances(this.data.ambulances);
                console.log(`Loaded ${this.data.ambulances.length} ambulance placements`);
            }
        } catch (error) {
            console.error('Error loading ambulances:', error);
        }
    },
    
    /**
     * Display hospitals on map
     */
    displayHospitals(hospitals) {
        // Clear existing markers
        this.layers.hospitals.clearLayers();
        
        hospitals.forEach(hospital => {
            const icon = this.createHospitalIcon();
            const marker = L.marker([hospital.latitude, hospital.longitude], { icon })
                .bindPopup(this.createHospitalPopup(hospital))
                .addTo(this.layers.hospitals);
        });
    },
    
    /**
     * Display police stations on map
     */
    displayPoliceStations(stations) {
        // Clear existing markers
        this.layers.policeStations.clearLayers();
        
        stations.forEach(station => {
            const icon = this.createPoliceIcon();
            const marker = L.marker([station.latitude, station.longitude], { icon })
                .bindPopup(this.createPolicePopup(station))
                .addTo(this.layers.policeStations);
        });
    },
    
    /**
     * Display ambulances on map
     */
    displayAmbulances(ambulances) {
        // Clear existing markers
        this.layers.ambulances.clearLayers();
        
        ambulances.forEach(ambulance => {
            const icon = this.createAmbulanceIcon();
            const marker = L.marker([ambulance.latitude, ambulance.longitude], { icon })
                .bindPopup(this.createAmbulancePopup(ambulance))
                .addTo(this.layers.ambulances);
        });
    },
    
    /**
     * Create hospital icon
     */
    createHospitalIcon() {
        const iconHtml = `
            <div class="emergency-marker hospital-marker">
                <i class="fas fa-plus-square"></i>
            </div>
        `;
        
        return L.divIcon({
            html: iconHtml,
            className: 'custom-emergency-marker',
            iconSize: [30, 30],
            iconAnchor: [15, 15],
            popupAnchor: [0, -15]
        });
    },
    
    /**
     * Create police icon
     */
    createPoliceIcon() {
        const iconHtml = `
            <div class="emergency-marker police-marker">
                <i class="fas fa-shield-alt"></i>
            </div>
        `;
        
        return L.divIcon({
            html: iconHtml,
            className: 'custom-emergency-marker',
            iconSize: [30, 30],
            iconAnchor: [15, 15],
            popupAnchor: [0, -15]
        });
    },
    
    /**
     * Create ambulance icon
     */
    createAmbulanceIcon() {
        const iconHtml = `
            <div class="emergency-marker ambulance-marker">
                <i class="fas fa-ambulance"></i>
            </div>
        `;
        
        return L.divIcon({
            html: iconHtml,
            className: 'custom-emergency-marker',
            iconSize: [32, 32],
            iconAnchor: [16, 16],
            popupAnchor: [0, -16]
        });
    },
    
    /**
     * Create hospital popup
     */
    createHospitalPopup(hospital) {
        return `
            <div class="emergency-popup hospital-popup">
                <div class="popup-header" style="background: #e74c3c; color: white;">
                    <i class="fas fa-plus-square"></i>
                    <h4>Hospital</h4>
                </div>
                <div class="popup-body">
                    <p class="hospital-name"><strong>${hospital.name}</strong></p>
                    <p class="hospital-type">Type: ${hospital.type.toUpperCase()}</p>
                    <p class="hospital-location">
                        <i class="fas fa-map-marker-alt"></i>
                        ${hospital.district}, ${hospital.state}
                    </p>
                    ${hospital.address !== 'N/A' ? `<p class="hospital-address">${hospital.address}</p>` : ''}
                </div>
            </div>
        `;
    },
    
    /**
     * Create police popup
     */
    createPolicePopup(station) {
        return `
            <div class="emergency-popup police-popup">
                <div class="popup-header" style="background: #3498db; color: white;">
                    <i class="fas fa-shield-alt"></i>
                    <h4>Police Station</h4>
                </div>
                <div class="popup-body">
                    <p class="station-name"><strong>${station.name}</strong></p>
                    <p class="station-type">Type: ${station.type}</p>
                    ${station.operator !== 'Unknown' ? `<p class="station-operator">Operator: ${station.operator}</p>` : ''}
                    <p class="station-coords">
                        <i class="fas fa-map-marker-alt"></i>
                        ${station.latitude.toFixed(4)}, ${station.longitude.toFixed(4)}
                    </p>
                </div>
            </div>
        `;
    },
    
    /**
     * Create ambulance popup
     */
    createAmbulancePopup(ambulance) {
        const statusColors = {
            'available': '#51cf66',
            'on-duty': '#ffa500',
            'emergency': '#ff6b6b'
        };
        
        const riskColors = {
            'critical': '#8B0000',
            'very_high': '#8B0000',
            'high': '#ff6b6b',
            'medium': '#ffa500',
            'low': '#51cf66'
        };
        
        // Check if this is a demo ambulance (has id field) or calculated placement (has hotspot_name)
        const isDemoAmbulance = ambulance.id && ambulance.id.startsWith('AMB-');
        const statusColor = statusColors[ambulance.status] || statusColors[ambulance.ambulance_status] || '#51cf66';
        const riskColor = riskColors[ambulance.risk_level?.toLowerCase()] || '#ffa500';
        
        if (isDemoAmbulance && !ambulance.hotspot_name) {
            // Demo ambulance not assigned to hotspot
            return `
                <div class="emergency-popup ambulance-popup">
                    <div class="popup-header" style="background: #f39c12; color: white;">
                        <i class="fas fa-ambulance"></i>
                        <h4>Demo Ambulance (Development)</h4>
                    </div>
                    <div class="popup-body">
                        <p class="ambulance-id"><strong>ID:</strong> ${ambulance.id}</p>
                        <p class="status-badge" style="background: ${statusColor}; color: white; padding: 4px 8px; border-radius: 4px; display: inline-block; margin: 8px 0;">
                            <strong>Status: ${ambulance.status.toUpperCase()}</strong>
                        </p>
                        <div class="ambulance-details">
                            <p><strong>Base Hospital:</strong></p>
                            <p style="margin-left: 12px;">${ambulance.hospital}</p>
                            <p style="margin-left: 12px; font-size: 0.9em; color: #666;">
                                ${ambulance.city}
                            </p>
                            ${ambulance.distance_km ? `<p><strong>Distance from you:</strong> ${ambulance.distance_km} km</p>` : ''}
                            ${ambulance.eta_minutes ? `<p><strong>Estimated ETA:</strong> ${ambulance.eta_minutes} minutes</p>` : ''}
                        </div>
                        <p style="margin-top: 10px; padding: 8px; background: #e3f2fd; border-radius: 4px; font-size: 0.85em;">
                            <i class="fas fa-info-circle"></i> This is a demo ambulance for development. Will be replaced with real GPS data in production.
                        </p>
                    </div>
                </div>
            `;
        } else {
            // Ambulance assigned to hotspot
            return `
                <div class="emergency-popup ambulance-popup">
                    <div class="popup-header" style="background: #f39c12; color: white;">
                        <i class="fas fa-ambulance"></i>
                        <h4>Pre-positioned Ambulance</h4>
                    </div>
                    <div class="popup-body">
                        ${ambulance.id ? `<p class="ambulance-id"><strong>ID:</strong> ${ambulance.id}</p>` : ''}
                        ${ambulance.current_hospital ? `<p><strong>Current Base:</strong> ${ambulance.current_hospital}</p>` : ''}
                        <p class="ambulance-location"><strong>${ambulance.hotspot_name}</strong></p>
                        ${ambulance.risk_level ? `
                        <p class="risk-badge" style="background: ${riskColor}; color: white; padding: 4px 8px; border-radius: 4px; display: inline-block; margin: 8px 0;">
                            <strong>Risk: ${ambulance.risk_level}</strong>
                        </p>
                        ` : ''}
                        ${ambulance.ambulance_status ? `
                        <p class="status-badge" style="background: ${statusColor}; color: white; padding: 4px 8px; border-radius: 4px; display: inline-block; margin: 8px 0 8px 8px;">
                            <strong>${ambulance.ambulance_status.toUpperCase()}</strong>
                        </p>
                        ` : ''}
                        ${ambulance.assigned_hospital ? `
                        <div class="ambulance-details">
                            <p><strong>Nearest Hospital:</strong></p>
                            <p style="margin-left: 12px;">${ambulance.assigned_hospital.name}</p>
                            <p style="margin-left: 12px; font-size: 0.9em; color: #666;">
                                ${ambulance.assigned_hospital.district}
                            </p>
                            <p><strong>Distance:</strong> ${ambulance.distance_to_hospital} km</p>
                            <p><strong>Est. Response Time:</strong> ${ambulance.response_time_estimate} min</p>
                        </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }
    },
    
    /**
     * Add layer control styles
     */
    addLayerControlStyles() {
        if (document.getElementById('emergency-layer-styles')) return;
        
        const styleElement = document.createElement('style');
        styleElement.id = 'emergency-layer-styles';
        styleElement.textContent = `
            .emergency-layer-control {
                position: absolute;
                top: 80px;
                right: 10px;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                padding: 0;
                min-width: 220px;
                z-index: 1000;
            }
            
            .emergency-layer-control .control-header {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 12px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 8px 8px 0 0;
                font-weight: 600;
            }
            
            .emergency-layer-control .control-header i {
                font-size: 18px;
            }
            
            .emergency-layer-control .toggle-control {
                margin-left: auto;
                background: none;
                border: none;
                color: white;
                cursor: pointer;
                font-size: 16px;
                padding: 4px;
            }
            
            .emergency-layer-control .control-body {
                padding: 12px;
                max-height: 300px;
                overflow-y: auto;
            }
            
            .emergency-layer-control .control-body.collapsed {
                display: none;
            }
            
            .emergency-layer-control .layer-item {
                margin-bottom: 10px;
            }
            
            .emergency-layer-control .layer-item:last-child {
                margin-bottom: 0;
            }
            
            .emergency-layer-control .layer-item label {
                display: flex;
                align-items: center;
                gap: 8px;
                cursor: pointer;
                padding: 6px;
                border-radius: 4px;
                transition: background 0.2s;
            }
            
            .emergency-layer-control .layer-item label:hover {
                background: #f5f5f5;
            }
            
            .emergency-layer-control .layer-item input[type="checkbox"] {
                cursor: pointer;
            }
            
            .emergency-layer-control .layer-item i {
                font-size: 16px;
            }
            
            .emergency-marker {
                width: 30px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                font-size: 16px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3);
                border: 2px solid white;
            }
            
            .hospital-marker {
                background: #e74c3c;
                color: white;
            }
            
            .police-marker {
                background: #3498db;
                color: white;
            }
            
            .ambulance-marker {
                background: #f39c12;
                color: white;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; transform: scale(1); }
                50% { opacity: 0.7; transform: scale(1.1); }
            }
            
            .emergency-popup {
                min-width: 250px;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
            
            .emergency-popup .popup-header {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 10px;
                margin: -12px -12px 12px -12px;
                border-radius: 4px 4px 0 0;
            }
            
            .emergency-popup .popup-header h4 {
                margin: 0;
                font-size: 16px;
            }
            
            .emergency-popup .popup-body {
                font-size: 14px;
            }
            
            .emergency-popup .popup-body p {
                margin: 8px 0;
            }
            
            .emergency-popup .popup-body p:first-child {
                margin-top: 0;
            }
            
            .emergency-popup .popup-body p:last-child {
                margin-bottom: 0;
            }
        `;
        
        document.head.appendChild(styleElement);
    }
};

// Initialize when map is ready
if (typeof window !== 'undefined') {
    window.EmergencyLayers = EmergencyLayers;
}
