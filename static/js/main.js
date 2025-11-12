/**
 * RAKSHAK - Main Application
 * Main application controller that initializes and manages all components
 */

const SafeRouteApp = {
    // Application state
    state: {
        initialized: false,
        currentLocation: null,
        startLocation: null,
        endLocation: null,
        currentRoute: null,
        hotspots: [],
        weather: null
    },

    // UI elements
    elements: {},

    /**
     * Initialize the application
     */
    async init() {
        SafeRouteUtils.log.info('Initializing RAKSHAK...');
        SafeRouteUtils.performance.mark('app-init-start');

        try {
            // Show loading overlay
            SafeRouteUtils.showLoading('Initializing RAKSHAK...');

            // Initialize DOM elements
            this.initElements();

            // Initialize map
            SafeRouteUtils.showLoading('Loading map...');
            SafeRouteMap.init('map');

            // Initialize emergency response layers
            if (window.EmergencyLayers) {
                SafeRouteUtils.showLoading('Loading emergency resources...');
                EmergencyLayers.init(SafeRouteMap.map);
            }
            
            // Initialize incident reporter
            if (window.IncidentReporter) {
                IncidentReporter.init();
            }

            // Initialize event listeners
            this.initEventListeners();

            // Initialize location services
            SafeRouteUtils.showLoading('Getting your location...');
            await this.initLocation();

            // Load initial data
            SafeRouteUtils.showLoading('Loading safety data...');
            await this.loadInitialData();

            // Mark as initialized
            this.state.initialized = true;

            SafeRouteUtils.performance.mark('app-init-end');
            SafeRouteUtils.performance.measure('app-init', 'app-init-start', 'app-init-end');

            SafeRouteUtils.hideLoading();
            SafeRouteUtils.showNotification('RAKSHAK initialized successfully!', 'success');

            SafeRouteUtils.log.info('RAKSHAK initialized successfully');
        } catch (error) {
            SafeRouteUtils.hideLoading();
            SafeRouteUtils.showNotification('Failed to initialize application: ' + error.message, 'error');
            SafeRouteUtils.log.error('App initialization failed:', error);
        }
    },

    /**
     * Initialize DOM element references
     */
    initElements() {
        this.elements = {
            // Input elements
            fromLocation: document.getElementById('fromLocation'),
            toLocation: document.getElementById('toLocation'),
            routeType: document.getElementById('routeType'),
            vehicleType: document.getElementById('vehicleType'),
            avoidTolls: document.getElementById('avoidTolls'),
            avoidHighways: document.getElementById('avoidHighways'),

            // Button elements
            findRoute: document.getElementById('findRoute'),
            useCurrentLocation: document.getElementById('useCurrentLocation'),
            toggleSidebar: document.getElementById('toggleSidebar'),
            centerMap: document.getElementById('centerMap'),
            toggleFullscreen: document.getElementById('toggleFullscreen'),

            // Filter elements
            hotspotFilter: document.getElementById('hotspotFilter'),
            riskFilter: document.getElementById('riskFilter'),

            // Display elements
            weatherCurrent: document.getElementById('weatherCurrent'),
            hotspotsList: document.getElementById('hotspotsList'),
            routePanel: document.getElementById('routePanel'),
            routeSummary: document.getElementById('routeSummary'),
            weatherSummary: document.getElementById('weatherSummary')
        };

        SafeRouteUtils.log.debug('DOM elements initialized');
    },

    /**
     * Initialize event listeners
     */
    initEventListeners() {
        // Route planning events
        if (this.elements.findRoute) {
            this.elements.findRoute.addEventListener('click', () => this.handleFindRoute());
        }

        if (this.elements.useCurrentLocation) {
            this.elements.useCurrentLocation.addEventListener('click', () => this.handleUseCurrentLocation());
        }

        // Map control events
        if (this.elements.toggleSidebar) {
            this.elements.toggleSidebar.addEventListener('click', () => SafeRouteMap.toggleSidebar());
        }

        if (this.elements.centerMap) {
            this.elements.centerMap.addEventListener('click', () => this.handleCenterMap());
        }

        if (this.elements.toggleFullscreen) {
            this.elements.toggleFullscreen.addEventListener('click', () => SafeRouteMap.toggleFullscreen());
        }

        // Input events with debouncing
        if (this.elements.fromLocation) {
            this.elements.fromLocation.addEventListener('input', 
                SafeRouteUtils.debounce((e) => this.handleLocationInput(e, 'from'), SafeRouteConfig.performance.debounceTime)
            );
        }

        if (this.elements.toLocation) {
            this.elements.toLocation.addEventListener('input', 
                SafeRouteUtils.debounce((e) => this.handleLocationInput(e, 'to'), SafeRouteConfig.performance.debounceTime)
            );
        }

        // Filter events
        if (this.elements.hotspotFilter) {
            this.elements.hotspotFilter.addEventListener('change', () => this.handleHotspotFilter());
        }

        if (this.elements.riskFilter) {
            this.elements.riskFilter.addEventListener('change', () => this.handleRiskFilter());
        }

        // Panel toggle events
        document.querySelectorAll('.toggle-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handlePanelToggle(e));
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));

        SafeRouteUtils.log.debug('Event listeners initialized');
    },

    /**
     * Initialize location services
     */
    async initLocation() {
        try {
            const location = await SafeRouteUtils.getCurrentLocation();
            this.state.currentLocation = location;
            
            // Set current location on map
            SafeRouteMap.setCurrentLocation(location.latitude, location.longitude, location.accuracy);
            SafeRouteMap.centerOn(location.latitude, location.longitude, 12);

            SafeRouteUtils.log.info('Current location obtained:', location);
            return location;
        } catch (error) {
            SafeRouteUtils.log.warn('Failed to get current location:', error.message);
            SafeRouteUtils.showNotification('Unable to get your location. Using default location.', 'warning');
            
            // Fall back to default location (Delhi)
            const defaultLocation = { latitude: 28.6139, longitude: 77.2090 };
            this.state.currentLocation = defaultLocation;
            SafeRouteMap.centerOn(defaultLocation.latitude, defaultLocation.longitude, 10);
            
            return defaultLocation;
        }
    },

    /**
     * Load initial data (weather, hotspots)
     */
    async loadInitialData() {
        const location = this.state.currentLocation;
        if (!location) return;

        try {
            // Load weather data
            await this.loadWeather(location.latitude, location.longitude);

            // Load nearby hotspots
            await this.loadHotspots(location.latitude, location.longitude);

        } catch (error) {
            SafeRouteUtils.log.error('Failed to load initial data:', error);
            SafeRouteUtils.showNotification('Some data may not be available', 'warning');
        }
    },

    /**
     * Load weather data
     */
    async loadWeather(lat, lng) {
        try {
            const response = await SafeRouteAPI.weather.getCurrent(lat, lng);
            
            if (response.status === 'success') {
                this.state.weather = response.data;
                this.updateWeatherDisplay(response.data);
                SafeRouteUtils.log.info('Weather data loaded');
            }
        } catch (error) {
            SafeRouteUtils.log.error('Failed to load weather:', error);
        }
    },

    /**
     * Load hotspots data
     */
    async loadHotspots(lat, lng, radius = 25) {
        try {
            const response = await SafeRouteAPI.hotspots.getInRadius(lat, lng, radius);
            
            if (response.status === 'success' && response.data.hotspots) {
                this.state.hotspots = response.data.hotspots;
                SafeRouteMap.addHotspots(response.data.hotspots);
                this.updateHotspotsDisplay(response.data.hotspots);
                SafeRouteUtils.log.info(`Loaded ${response.data.hotspots.length} hotspots`);
            }
        } catch (error) {
            SafeRouteUtils.log.error('Failed to load hotspots:', error);
        }
    },

    /**
     * Handle route finding
     */
    async handleFindRoute() {
        const fromValue = this.elements.fromLocation?.value.trim();
        const toValue = this.elements.toLocation?.value.trim();

        if (!fromValue || !toValue) {
            SafeRouteUtils.showNotification('Please enter both start and destination locations', 'warning');
            return;
        }

        try {
            SafeRouteUtils.toggleMapLoading(true, 'Calculating safe route...');

            // Geocode locations
            const fromGeocode = await SafeRouteAPI.geocoding.forward(fromValue);
            const toGeocode = await SafeRouteAPI.geocoding.forward(toValue);

            if (fromGeocode.status !== 'success' || !fromGeocode.data.length) {
                throw new Error('Could not find starting location');
            }

            if (toGeocode.status !== 'success' || !toGeocode.data.length) {
                throw new Error('Could not find destination');
            }

            const fromLocation = fromGeocode.data[0];
            const toLocation = toGeocode.data[0];

            // Get route options
            const routeOptions = {
                routeType: this.elements.routeType?.value || 'balanced',
                vehicleType: this.elements.vehicleType?.value || 'car',
                avoidTolls: this.elements.avoidTolls?.checked || false,
                avoidHighways: this.elements.avoidHighways?.checked || false
            };

            // Calculate route
            const routeResponse = await SafeRouteAPI.routes.calculate(
                fromLocation.latitude, fromLocation.longitude,
                toLocation.latitude, toLocation.longitude,
                routeOptions
            );

            if (routeResponse.status === 'success') {
                this.handleRouteResult(routeResponse.data, fromLocation, toLocation);
                SafeRouteUtils.showNotification('Route calculated successfully!', 'success');
            } else {
                throw new Error(routeResponse.message || 'Failed to calculate route');
            }

        } catch (error) {
            SafeRouteUtils.log.error('Route calculation failed:', error);
            SafeRouteUtils.showNotification('Failed to calculate route: ' + error.message, 'error');
        } finally {
            SafeRouteUtils.toggleMapLoading(false);
        }
    },

    /**
     * Handle route calculation result
     */
    handleRouteResult(routeData, fromLocation, toLocation) {
        this.state.currentRoute = routeData;
        this.state.startLocation = fromLocation;
        this.state.endLocation = toLocation;

        // Add markers to map
        SafeRouteMap.addRouteMarker(fromLocation.latitude, fromLocation.longitude, 'start', fromLocation.display_name);
        SafeRouteMap.addRouteMarker(toLocation.latitude, toLocation.longitude, 'end', toLocation.display_name);

        // Add route to map
        if (routeData.geometry) {
            SafeRouteMap.addRoute(routeData);
        }

        // Update route panel
        this.updateRouteDisplay(routeData);
        this.showRoutePanel();

        SafeRouteUtils.log.info('Route result processed');
    },

    /**
     * Handle use current location
     */
    async handleUseCurrentLocation() {
        if (!this.state.currentLocation) {
            try {
                SafeRouteUtils.showLoading('Getting your location...');
                await this.initLocation();
            } catch (error) {
                SafeRouteUtils.showNotification('Unable to get your location', 'error');
                return;
            } finally {
                SafeRouteUtils.hideLoading();
            }
        }

        const location = this.state.currentLocation;
        if (this.elements.fromLocation) {
            this.elements.fromLocation.value = `${location.latitude.toFixed(6)}, ${location.longitude.toFixed(6)}`;
        }

        SafeRouteUtils.showNotification('Current location set as starting point', 'success');
    },

    /**
     * Handle center map
     */
    handleCenterMap() {
        // Attempt to actively fetch and center on user's live location
        SafeRouteMap.locateUser({ zoom: 14, showMarker: true, centerMap: true })
            .then(loc => {
                this.state.currentLocation = { latitude: loc.lat, longitude: loc.lng, accuracy: loc.accuracy };
            })
            .catch(() => {
                // Fallback to last known or default center
                if (this.state.currentLocation) {
                    SafeRouteMap.centerOn(
                        this.state.currentLocation.latitude,
                        this.state.currentLocation.longitude,
                        12
                    );
                } else {
                    SafeRouteMap.centerOn(...SafeRouteConfig.map.defaultCenter, SafeRouteConfig.map.defaultZoom);
                }
            });
    },

    /**
     * Handle location input with geocoding suggestions
     */
    async handleLocationInput(event, type) {
        const query = event.target.value.trim();
        if (query.length < 3) return;

        try {
            const response = await SafeRouteAPI.geocoding.search(query, 
                this.state.currentLocation?.latitude, 
                this.state.currentLocation?.longitude
            );

            if (response.status === 'success' && response.data.length > 0) {
                // For now, just log the results
                // In a full implementation, we'd show a dropdown with suggestions
                SafeRouteUtils.log.debug(`Geocoding suggestions for "${query}":`, response.data);
            }
        } catch (error) {
            SafeRouteUtils.log.error('Geocoding failed:', error);
        }
    },

    /**
     * Handle panel toggle
     */
    handlePanelToggle(event) {
        const button = event.currentTarget;
        const targetId = button.dataset.target;
        const content = document.getElementById(targetId);
        const icon = button.querySelector('i');

        if (content && icon) {
            content.style.display = content.style.display === 'none' ? 'block' : 'none';
            icon.classList.toggle('fa-chevron-down');
            icon.classList.toggle('fa-chevron-up');
        }
    },

    /**
     * Handle hotspot filter changes
     */
    handleHotspotFilter() {
        const typeFilter = this.elements.hotspotFilter?.value || 'all';
        const riskFilter = this.elements.riskFilter?.value || 'all';
        this.filterHotspots({ type: typeFilter, riskLevel: riskFilter });
    },

    /**
     * Handle risk filter changes
     */
    handleRiskFilter() {
        const typeFilter = this.elements.hotspotFilter?.value || 'all';
        const riskFilter = this.elements.riskFilter?.value || 'all';
        this.filterHotspots({ type: typeFilter, riskLevel: riskFilter });
    },

    /**
     * Filter hotspots
     */
    filterHotspots(filters = {}) {
        let filteredHotspots = [...this.state.hotspots];

        if (filters.type && filters.type !== 'all') {
            filteredHotspots = filteredHotspots.filter(h => h.type === filters.type);
        }

        if (filters.riskLevel && filters.riskLevel !== 'all') {
            filteredHotspots = filteredHotspots.filter(h => h.risk_level === filters.riskLevel);
        }

        // Clear and update map hotspots
        SafeRouteMap.clearHotspots();
        SafeRouteMap.addHotspots(filteredHotspots);
        
        // Update sidebar display
        this.updateHotspotsDisplay(filteredHotspots);

        SafeRouteUtils.log.info(`Filtered to ${filteredHotspots.length} hotspots`);
        SafeRouteUtils.showNotification(`Showing ${filteredHotspots.length} hotspots`, 'info');
    },

    /**
     * Handle keyboard shortcuts
     */
    handleKeyboardShortcuts(event) {
        // Ctrl/Cmd + Enter: Find route
        if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
            this.handleFindRoute();
            event.preventDefault();
        }
        
        // Escape: Clear route
        if (event.key === 'Escape') {
            this.clearRoute();
            event.preventDefault();
        }
    },

    /**
     * Update weather display
     */
    updateWeatherDisplay(weatherData) {
        if (!weatherData || !this.elements.weatherCurrent) return;

        const current = weatherData.current;
        const conditions = weatherData.driving_conditions;

        // Update main weather display
        const weatherIcon = this.elements.weatherCurrent.querySelector('.weather-icon i');
        const temperature = this.elements.weatherCurrent.querySelector('.temperature');
        const description = this.elements.weatherCurrent.querySelector('.description');
        const feelsLike = this.elements.weatherCurrent.querySelector('.feels-like');

        if (weatherIcon) {
            const iconClass = SafeRouteConfig.weather.icons[current.icon] || 'fa-cloud';
            weatherIcon.className = `fas ${iconClass}`;
        }

        if (temperature) temperature.textContent = `${current.temperature_c}°C`;
        if (description) description.textContent = current.description;
        if (feelsLike) feelsLike.textContent = `Feels like ${current.feels_like_c}°C`;

        // Update weather details
        const humidity = document.getElementById('humidity');
        const windSpeed = document.getElementById('windSpeed');
        const visibility = document.getElementById('visibility');

        if (humidity) humidity.textContent = `${current.humidity_percent}%`;
        if (windSpeed) windSpeed.textContent = `${current.wind_speed_kmh} km/h`;
        if (visibility) visibility.textContent = `${current.visibility_km} km`;

        // Update driving conditions
        const drivingRisk = document.getElementById('drivingRisk');
        const recommendations = document.getElementById('weatherRecommendations');

        if (drivingRisk) {
            const riskLevel = conditions.risk_factor < 0.3 ? 'low' : 
                           conditions.risk_factor < 0.6 ? 'medium' : 'high';
            drivingRisk.textContent = SafeRouteUtils.formatRiskLevel(riskLevel);
            drivingRisk.className = `risk-value ${riskLevel}`;
        }

        if (recommendations && conditions.recommendations) {
            recommendations.textContent = conditions.recommendations[0] || 'Drive safely';
        }

        // Update header weather summary
        if (this.elements.weatherSummary) {
            this.elements.weatherSummary.querySelector('span').textContent = 
                `${current.temperature_c}°C, ${current.description}`;
        }
    },

    /**
     * Update hotspots display
     */
    updateHotspotsDisplay(hotspots) {
        if (!this.elements.hotspotsList) return;

        if (!hotspots || hotspots.length === 0) {
            this.elements.hotspotsList.innerHTML = '<div class="loading">No hotspots found in this area</div>';
            return;
        }

        const hotspotsHtml = hotspots.slice(0, 10).map(hotspot => {
            const riskClass = SafeRouteUtils.getRiskClass(hotspot.risk_level);
            const distance = this.state.currentLocation ? 
                SafeRouteUtils.calculateDistance(
                    this.state.currentLocation.latitude,
                    this.state.currentLocation.longitude,
                    hotspot.latitude,
                    hotspot.longitude
                ) : 0;

            return `
                <div class="hotspot-item" data-hotspot-id="${hotspot.id}">
                    <div class="hotspot-header">
                        <div class="hotspot-name">${SafeRouteUtils.sanitizeHtml(hotspot.name)}</div>
                        <div class="hotspot-risk ${riskClass}">${SafeRouteUtils.formatRiskLevel(hotspot.risk_level)}</div>
                    </div>
                    <div class="hotspot-info">
                        <span class="hotspot-type">${hotspot.type.replace('_', ' ')}</span>
                        <span class="hotspot-distance">${SafeRouteUtils.formatDistance(distance)}</span>
                    </div>
                </div>
            `;
        }).join('');

        this.elements.hotspotsList.innerHTML = hotspotsHtml;

        // Add click listeners for hotspot items
        this.elements.hotspotsList.querySelectorAll('.hotspot-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const hotspotId = item.dataset.hotspotId;
                const hotspot = hotspots.find(h => h.id === hotspotId);
                if (hotspot) {
                    SafeRouteMap.centerOn(hotspot.latitude, hotspot.longitude, 15);
                    const marker = SafeRouteMap.markers.hotspots.get(hotspotId);
                    if (marker) marker.openPopup();
                }
            });
        });
    },

    /**
     * Update route display
     */
    updateRouteDisplay(routeData) {
        if (!this.elements.routeSummary || !routeData) return;

        const summaryHtml = `
            <div class="route-info-card">
                <h4>Route Summary</h4>
                <div class="route-stats">
                    <div class="stat-item">
                        <span class="stat-label">Distance</span>
                        <span class="stat-value">${SafeRouteUtils.formatDistance(routeData.distance_km)}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Duration</span>
                        <span class="stat-value">${SafeRouteUtils.formatDuration(routeData.duration_minutes)}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Safety Score</span>
                        <span class="stat-value">${(routeData.safety_score * 100).toFixed(0)}%</span>
                    </div>
                </div>
                ${routeData.warnings && routeData.warnings.length > 0 ? `
                <div class="route-warnings">
                    <h5>Safety Warnings</h5>
                    <ul>
                        ${routeData.warnings.map(warning => 
                            `<li>${SafeRouteUtils.sanitizeHtml(warning)}</li>`
                        ).join('')}
                    </ul>
                </div>
                ` : ''}
            </div>
        `;

        this.elements.routeSummary.innerHTML = summaryHtml;
    },

    /**
     * Show route panel
     */
    showRoutePanel() {
        if (this.elements.routePanel) {
            this.elements.routePanel.style.display = 'block';
        }
    },

    /**
     * Clear current route
     */
    clearRoute() {
        this.state.currentRoute = null;
        this.state.startLocation = null;
        this.state.endLocation = null;

        SafeRouteMap.clearRoutes();
        SafeRouteMap.clearAllMarkers();

        if (this.elements.routePanel) {
            this.elements.routePanel.style.display = 'none';
        }

        if (this.elements.fromLocation) this.elements.fromLocation.value = '';
        if (this.elements.toLocation) this.elements.toLocation.value = '';

        // Restore current location marker
        if (this.state.currentLocation) {
            SafeRouteMap.setCurrentLocation(
                this.state.currentLocation.latitude, 
                this.state.currentLocation.longitude
            );
        }

        // Restore hotspots
        if (this.state.hotspots.length > 0) {
            SafeRouteMap.addHotspots(this.state.hotspots);
        }

        SafeRouteUtils.showNotification('Route cleared', 'info');
    }
};

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    SafeRouteApp.init();
});

// Export for use in other modules
window.SafeRouteApp = SafeRouteApp;