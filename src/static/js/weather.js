/**
 * SafeRoute Navigator v2.0 - Weather Module
 * Frontend weather management and display
 */

const SafeRouteWeather = {
    // Current weather data
    currentWeather: null,
    
    // Weather update interval
    updateInterval: null,

    /**
     * Initialize weather module
     */
    init() {
        SafeRouteUtils.log.info('Weather module initialized');
        this.startPeriodicUpdates();
    },

    /**
     * Start periodic weather updates
     */
    startPeriodicUpdates() {
        // Update weather every 10 minutes
        this.updateInterval = setInterval(() => {
            if (SafeRouteApp.state.currentLocation) {
                this.updateWeather(
                    SafeRouteApp.state.currentLocation.latitude,
                    SafeRouteApp.state.currentLocation.longitude
                );
            }
        }, SafeRouteConfig.weather.updateInterval);
    },

    /**
     * Update weather data
     */
    async updateWeather(lat, lng) {
        try {
            const response = await SafeRouteAPI.weather.getCurrent(lat, lng);
            if (response.status === 'success') {
                this.currentWeather = response.data;
                SafeRouteApp.updateWeatherDisplay(response.data);
            }
        } catch (error) {
            SafeRouteUtils.log.error('Weather update failed:', error);
        }
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
window.SafeRouteWeather = SafeRouteWeather;