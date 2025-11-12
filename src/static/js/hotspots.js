/**
 * SafeRoute Navigator v2.0 - Hotspots Module
 * Frontend hotspot management and display
 */

const SafeRouteHotspots = {
    // Current hotspots data
    hotspots: [],
    
    // Update interval
    updateInterval: null,

    /**
     * Initialize hotspots module
     */
    init() {
        SafeRouteUtils.log.info('Hotspots module initialized');
        this.startPeriodicUpdates();
    },

    /**
     * Load hotspots for given location
     */
    async loadHotspots(lat, lng, radius = 25) {
        if (SafeRouteApp.loadHotspots) {
            return SafeRouteApp.loadHotspots(lat, lng, radius);
        }
    },

    /**
     * Start periodic hotspot updates
     */
    startPeriodicUpdates() {
        // Update hotspots every 5 minutes
        this.updateInterval = setInterval(() => {
            if (SafeRouteApp.state.currentLocation) {
                this.loadHotspots(
                    SafeRouteApp.state.currentLocation.latitude,
                    SafeRouteApp.state.currentLocation.longitude
                );
            }
        }, SafeRouteConfig.hotspots.refreshInterval);
    },

    /**
     * Stop periodic updates
     */
    stopUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }
};

// Export for use in other modules
window.SafeRouteHotspots = SafeRouteHotspots;