/**
 * RAKSHAK - Routes Module  
 * Frontend route planning and management
 */

const SafeRouteRoutes = {
    // Current route data
    currentRoute: null,
    alternativeRoutes: [],

    /**
     * Initialize routes module
     */
    init() {
        SafeRouteUtils.log.info('Routes module initialized');
    },

    /**
     * Calculate route between two locations
     */
    async calculateRoute(fromLat, fromLng, toLat, toLng, options = {}) {
        try {
            return await SafeRouteAPI.routes.calculate(fromLat, fromLng, toLat, toLng, options);
        } catch (error) {
            SafeRouteUtils.log.error('Route calculation failed:', error);
            throw error;
        }
    },

    /**
     * Get alternative routes
     */
    async getAlternatives(fromLat, fromLng, toLat, toLng, options = {}) {
        try {
            const response = await SafeRouteAPI.routes.getAlternatives(fromLat, fromLng, toLat, toLng, options);
            if (response.status === 'success') {
                this.alternativeRoutes = response.data.routes || [];
            }
            return response;
        } catch (error) {
            SafeRouteUtils.log.error('Alternative routes failed:', error);
            throw error;
        }
    },

    /**
     * Clear current route
     */
    clearRoute() {
        this.currentRoute = null;
        this.alternativeRoutes = [];
        SafeRouteMap.clearRoutes();
    }
};

// Export for use in other modules
window.SafeRouteRoutes = SafeRouteRoutes;