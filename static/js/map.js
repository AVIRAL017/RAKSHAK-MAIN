/**
 * RAKSHAK - Map Management
 * Handles all map-related functionality using Leaflet.js
 */

const SafeRouteMap = {
    // Map instance
    map: null,
    
    // Map layers
    layers: {
        hotspots: null,
        routes: null,
        markers: null
    },
    
    // Current markers
    markers: {
        start: null,
        end: null,
        hotspots: new Map(),
        current: null,
        userLocation: null
    },
    
    // User location tracking
    userLocation: {
        lat: null,
        lng: null,
        accuracy: null,
        watchId: null
    },

    /**
     * Initialize the map
     */
    init(containerId = 'map') {
        SafeRouteUtils.log.info('Initializing SafeRoute Map...');
        
        // Initialize map
        this.map = L.map(containerId, {
            center: SafeRouteConfig.map.defaultCenter,
            zoom: SafeRouteConfig.map.defaultZoom,
            minZoom: SafeRouteConfig.map.minZoom,
            maxZoom: SafeRouteConfig.map.maxZoom,
            zoomControl: true,
            attributionControl: true
        });

        // Add tile layer
        L.tileLayer(SafeRouteConfig.map.tileLayers.default.url, {
            attribution: SafeRouteConfig.map.tileLayers.default.attribution,
            maxZoom: SafeRouteConfig.map.tileLayers.default.maxZoom
        }).addTo(this.map);

        // Initialize layer groups
        this.layers.hotspots = L.layerGroup().addTo(this.map);
        this.layers.routes = L.layerGroup().addTo(this.map);
        this.layers.markers = L.layerGroup().addTo(this.map);

        // Set up event listeners
        this.setupMapEvents();

        SafeRouteUtils.log.info('SafeRoute Map initialized successfully');
        return this.map;
    },

    /**
     * Set up map event listeners
     */
    setupMapEvents() {
        if (!this.map) return;

        // Map click event
        this.map.on('click', (e) => {
            const lat = e.latlng.lat;
            const lng = e.latlng.lng;
            
            SafeRouteUtils.log.debug(`Map clicked at: ${lat}, ${lng}`);
            
            // Reverse geocode clicked location
            this.reverseGeocode(lat, lng);
        });

        // Map move end event
        this.map.on('moveend', SafeRouteUtils.throttle(() => {
            const center = this.map.getCenter();
            const zoom = this.map.getZoom();
            
            SafeRouteUtils.log.debug(`Map moved to: ${center.lat}, ${center.lng} (zoom: ${zoom})`);
            
            // Update hotspots for new view
            if (window.SafeRouteHotspots) {
                SafeRouteHotspots.loadHotspots(center.lat, center.lng);
            }
        }, SafeRouteConfig.performance.throttleTime));
    },

    /**
     * Add route marker (start/end)
     */
    addRouteMarker(lat, lng, type = 'start', title = '') {
        if (!this.map) return null;

        const config = SafeRouteConfig.map.markers[type];
        if (!config) return null;

        // Remove existing marker of this type
        if (this.markers[type]) {
            this.markers[type].remove();
        }

        // Create custom icon
        const iconHtml = `
            <div class="route-marker ${type}">
                <i class="fas ${config.icon}"></i>
            </div>
        `;
        
        const icon = L.divIcon({
            html: iconHtml,
            className: 'custom-marker',
            iconSize: [30, 40],
            iconAnchor: [15, 40],
            popupAnchor: [0, -40]
        });

        // Create marker
        const marker = L.marker([lat, lng], { icon })
            .bindPopup(`
                <div class="route-popup">
                    <h4>${type === 'start' ? 'Start Location' : 'Destination'}</h4>
                    <div class="route-info">
                        ${title || `${lat.toFixed(6)}, ${lng.toFixed(6)}`}
                    </div>
                </div>
            `)
            .addTo(this.layers.markers);

        this.markers[type] = marker;
        return marker;
    },

    /**
     * Add hotspot markers
     */
    addHotspots(hotspots) {
        if (!this.map || !hotspots) return;

        // Clear existing hotspots
        this.clearHotspots();

        hotspots.forEach(hotspot => {
            this.addHotspot(hotspot);
        });

        SafeRouteUtils.log.info(`Added ${hotspots.length} hotspot markers`);
    },

    /**
     * Add single hotspot marker
     */
    addHotspot(hotspot) {
        if (!this.map || !hotspot) return null;

        const lat = hotspot.latitude;
        const lng = hotspot.longitude;
        const riskColor = SafeRouteUtils.getRiskColor(hotspot.risk_level);
        const typeConfig = SafeRouteConfig.hotspots.types[hotspot.type] || {};

        // Create custom icon
        const iconHtml = `
            <div class="hotspot-marker ${hotspot.risk_level}" style="background-color: ${riskColor}">
                <i class="fas ${typeConfig.icon || 'fa-exclamation-triangle'}"></i>
            </div>
        `;

        const icon = L.divIcon({
            html: iconHtml,
            className: 'custom-hotspot-marker',
            iconSize: [25, 25],
            iconAnchor: [12, 12],
            popupAnchor: [0, -12]
        });

        // Create popup content
        const popupContent = this.createHotspotPopup(hotspot);

        // Create marker
        const marker = L.marker([lat, lng], { icon })
            .bindPopup(popupContent)
            .addTo(this.layers.hotspots);

        // Store marker reference
        this.markers.hotspots.set(hotspot.id, marker);

        return marker;
    },

    /**
     * Create hotspot popup content
     */
    createHotspotPopup(hotspot) {
        const riskClass = SafeRouteUtils.getRiskClass(hotspot.risk_level);
        const riskLabel = SafeRouteUtils.formatRiskLevel(hotspot.risk_level);
        
        return `
            <div class="hotspot-popup">
                <h4>${SafeRouteUtils.sanitizeHtml(hotspot.name)}</h4>
                <div class="risk-badge ${riskClass}">${riskLabel}</div>
                
                <div class="info-row">
                    <strong>Type:</strong>
                    <span>${hotspot.type.replace('_', ' ')}</span>
                </div>
                
                <div class="info-row">
                    <strong>Risk Score:</strong>
                    <span>${(hotspot.risk_score * 100).toFixed(0)}%</span>
                </div>
                
                <div class="info-row">
                    <strong>Last Updated:</strong>
                    <span>${SafeRouteUtils.formatTimestamp(hotspot.last_updated)}</span>
                </div>
                
                ${hotspot.incident_count_24h ? `
                <div class="info-row">
                    <strong>Recent Incidents:</strong>
                    <span>${hotspot.incident_count_24h} (24h)</span>
                </div>
                ` : ''}
                
                <div class="description">
                    ${SafeRouteUtils.sanitizeHtml(hotspot.description)}
                </div>
                
                ${hotspot.mitigation_suggestions && hotspot.mitigation_suggestions.length > 0 ? `
                <div class="mitigation-suggestions">
                    <strong>Safety Tips:</strong>
                    <ul>
                        ${hotspot.mitigation_suggestions.slice(0, 2).map(tip => 
                            `<li>${SafeRouteUtils.sanitizeHtml(tip)}</li>`
                        ).join('')}
                    </ul>
                </div>
                ` : ''}
            </div>
        `;
    },

    /**
     * Add route polyline
     */
    addRoute(routeData, type = 'recommended') {
        if (!this.map || !routeData || !routeData.geometry) return null;

        const config = SafeRouteConfig.map.routes[type];
        if (!config) return null;

        // Clear existing routes
        this.clearRoutes();

        // Create polyline from route geometry
        let coordinates = [];
        
        if (routeData.geometry.type === 'LineString') {
            coordinates = routeData.geometry.coordinates.map(coord => [coord[1], coord[0]]);
        } else if (routeData.route_coordinates) {
            coordinates = routeData.route_coordinates;
        }

        if (coordinates.length === 0) return null;

        // Create route polyline
        const route = L.polyline(coordinates, {
            color: config.color,
            weight: config.weight,
            opacity: config.opacity,
            smoothFactor: 1
        }).addTo(this.layers.routes);

        // Add popup with route info
        const popupContent = `
            <div class="route-popup">
                <h4>Route Information</h4>
                <div class="route-info">
                    <strong>Distance:</strong> ${SafeRouteUtils.formatDistance(routeData.distance_km)}<br>
                    <strong>Duration:</strong> ${SafeRouteUtils.formatDuration(routeData.duration_minutes)}<br>
                    <strong>Safety Score:</strong> ${(routeData.safety_score * 100).toFixed(0)}%
                </div>
            </div>
        `;
        
        route.bindPopup(popupContent);

        // Fit map to route bounds
        this.map.fitBounds(route.getBounds(), { padding: [20, 20] });

        SafeRouteUtils.log.info('Route added to map');
        return route;
    },

    /**
     * Set user's current location
     */
    setCurrentLocation(lat, lng, accuracy = null) {
        if (!this.map) return null;

        // Remove existing current location marker
        if (this.markers.current) {
            this.markers.current.remove();
        }

        // Create current location icon
        const iconHtml = `
            <div class="current-location-marker">
                <div class="pulse"></div>
                <div class="dot"></div>
            </div>
        `;

        const icon = L.divIcon({
            html: iconHtml,
            className: 'current-location',
            iconSize: [20, 20],
            iconAnchor: [10, 10]
        });

        // Create marker
        this.markers.current = L.marker([lat, lng], { icon })
            .bindPopup(`
                <div class="location-popup">
                    <h4>Your Location</h4>
                    <div class="location-info">
                        ${lat.toFixed(6)}, ${lng.toFixed(6)}
                        ${accuracy ? `<br><small>Accuracy: ±${accuracy.toFixed(0)}m</small>` : ''}
                    </div>
                </div>
            `)
            .addTo(this.layers.markers);

        // Add accuracy circle if available
        if (accuracy && accuracy < 1000) {
            L.circle([lat, lng], {
                radius: accuracy,
                color: '#4F46E5',
                fillColor: '#4F46E5',
                fillOpacity: 0.1,
                weight: 1
            }).addTo(this.layers.markers);
        }

        SafeRouteUtils.log.info(`Current location set: ${lat}, ${lng}`);
        return this.markers.current;
    },

    /**
     * Center map on coordinates
     */
    centerOn(lat, lng, zoom = null) {
        if (!this.map) return;
        
        this.map.setView([lat, lng], zoom || this.map.getZoom());
    },

    /**
     * Fit map to show all markers
     */
    fitToMarkers() {
        if (!this.map) return;

        const group = new L.featureGroup([
            ...Object.values(this.markers).filter(m => m && m._latlng),
            ...Array.from(this.markers.hotspots.values())
        ]);

        if (group.getLayers().length > 0) {
            this.map.fitBounds(group.getBounds(), { padding: [20, 20] });
        }
    },

    /**
     * Clear all hotspot markers
     */
    clearHotspots() {
        if (this.layers.hotspots) {
            this.layers.hotspots.clearLayers();
        }
        this.markers.hotspots.clear();
    },

    /**
     * Clear all route markers
     */
    clearRoutes() {
        if (this.layers.routes) {
            this.layers.routes.clearLayers();
        }
    },

    /**
     * Clear all markers
     */
    clearAllMarkers() {
        Object.keys(this.markers).forEach(key => {
            if (key === 'hotspots') {
                this.markers[key].clear();
            } else if (this.markers[key]) {
                this.markers[key].remove();
                this.markers[key] = null;
            }
        });
        
        Object.values(this.layers).forEach(layer => {
            if (layer) layer.clearLayers();
        });
    },

    /**
     * Get map center
     */
    getCenter() {
        return this.map ? this.map.getCenter() : null;
    },

    /**
     * Get map bounds
     */
    getBounds() {
        return this.map ? this.map.getBounds() : null;
    },

    /**
     * Reverse geocode coordinates
     */
    async reverseGeocode(lat, lng) {
        try {
            const response = await SafeRouteAPI.geocoding.reverse(lat, lng);
            
            if (response.status === 'success' && response.data.length > 0) {
                const location = response.data[0];
                SafeRouteUtils.log.info('Reverse geocode result:', location);
                return location;
            }
        } catch (error) {
            SafeRouteUtils.log.error('Reverse geocoding failed:', error);
        }
        
        return null;
    },

    /**
     * Toggle sidebar visibility
     */
    toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        const mapContainer = document.querySelector('.map-container');
        
        if (sidebar && mapContainer) {
            sidebar.classList.toggle('hidden');
            
            // Trigger map resize after animation
            setTimeout(() => {
                if (this.map) {
                    this.map.invalidateSize();
                }
            }, 300);
        }
    },

    /**
     * Toggle fullscreen mode
     */
    toggleFullscreen() {
        const mapContainer = document.querySelector('.map-container');
        
        if (!mapContainer) return;

        if (!document.fullscreenElement) {
            mapContainer.requestFullscreen?.() ||
            mapContainer.webkitRequestFullscreen?.() ||
            mapContainer.msRequestFullscreen?.();
        } else {
            document.exitFullscreen?.() ||
            document.webkitExitFullscreen?.() ||
            document.msExitFullscreen?.();
        }
    },

    /**
     * Get user's current location using Geolocation API
     */
    getUserLocation() {
        return new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                reject(new Error('Geolocation is not supported by your browser'));
                return;
            }

            SafeRouteUtils.log.info('Requesting user location...');
            
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const lat = position.coords.latitude;
                    const lng = position.coords.longitude;
                    const accuracy = position.coords.accuracy;
                    
                    // Store user location
                    this.userLocation.lat = lat;
                    this.userLocation.lng = lng;
                    this.userLocation.accuracy = accuracy;
                    
                    SafeRouteUtils.log.info(`User location obtained: ${lat}, ${lng}`);
                    resolve({ lat, lng, accuracy });
                },
                (error) => {
                    let errorMessage = 'Unable to retrieve your location';
                    
                    switch(error.code) {
                        case error.PERMISSION_DENIED:
                            errorMessage = 'Location permission denied';
                            break;
                        case error.POSITION_UNAVAILABLE:
                            errorMessage = 'Location information unavailable';
                            break;
                        case error.TIMEOUT:
                            errorMessage = 'Location request timed out';
                            break;
                    }
                    
                    SafeRouteUtils.log.error(errorMessage);
                    reject(new Error(errorMessage));
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                }
            );
        });
    },

    /**
     * Center map on user's current location
     */
    async locateUser(options = {}) {
        const { zoom = 15, showMarker = true, centerMap = true } = options;
        
        try {
            const location = await this.getUserLocation();
            
            // Add marker for user location
            if (showMarker) {
                this.setCurrentLocation(location.lat, location.lng, location.accuracy);
            }
            
            // Center map on user location
            if (centerMap) {
                this.centerOn(location.lat, location.lng, zoom);
            }
            
            // Show notification
            if (window.SafeRouteUtils && window.SafeRouteUtils.showNotification) {
                SafeRouteUtils.showNotification('Location found!', 'success');
            }
            
            return location;
        } catch (error) {
            // Show error notification
            if (window.SafeRouteUtils && window.SafeRouteUtils.showNotification) {
                SafeRouteUtils.showNotification(error.message, 'error');
            }
            throw error;
        }
    },

    /**
     * Start watching user's location for continuous tracking
     */
    startLocationTracking(callback) {
        if (!navigator.geolocation) {
            SafeRouteUtils.log.error('Geolocation not supported');
            return null;
        }

        // Clear any existing watch
        this.stopLocationTracking();
        
        SafeRouteUtils.log.info('Starting location tracking...');
        
        this.userLocation.watchId = navigator.geolocation.watchPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                const accuracy = position.coords.accuracy;
                
                // Update stored location
                this.userLocation.lat = lat;
                this.userLocation.lng = lng;
                this.userLocation.accuracy = accuracy;
                
                // Update marker
                this.setCurrentLocation(lat, lng, accuracy);
                
                // Call callback if provided
                if (callback && typeof callback === 'function') {
                    callback({ lat, lng, accuracy });
                }
                
                SafeRouteUtils.log.debug(`Location updated: ${lat}, ${lng}`);
            },
            (error) => {
                SafeRouteUtils.log.error('Location tracking error:', error);
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 5000
            }
        );
        
        return this.userLocation.watchId;
    },

    /**
     * Stop watching user's location
     */
    stopLocationTracking() {
        if (this.userLocation.watchId !== null) {
            navigator.geolocation.clearWatch(this.userLocation.watchId);
            this.userLocation.watchId = null;
            SafeRouteUtils.log.info('Location tracking stopped');
        }
    }
};

// Export for use in other modules
window.SafeRouteMap = SafeRouteMap;