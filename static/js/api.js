/**
 * RAKSHAK - API Client
 * Handles all communication with the backend API
 */

const SafeRouteAPI = {
    // Base configuration
    baseUrl: SafeRouteConfig.api.baseUrl,
    endpoints: SafeRouteConfig.api.endpoints,
    timeout: SafeRouteConfig.api.timeout,

    /**
     * Generic HTTP request handler
     */
    async request(url, options = {}) {
        const config = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin',
            ...options
        };

        // Add timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);
        config.signal = controller.signal;

        try {
            SafeRouteUtils.performance.mark('api-request-start');
            
            const response = await fetch(url, config);
            clearTimeout(timeoutId);

            SafeRouteUtils.performance.mark('api-request-end');
            SafeRouteUtils.performance.measure('api-request', 'api-request-start', 'api-request-end');

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            SafeRouteUtils.log.debug('API Response:', data);
            
            return data;
        } catch (error) {
            clearTimeout(timeoutId);
            
            if (error.name === 'AbortError') {
                throw new Error('Request timeout');
            }
            
            SafeRouteUtils.log.error('API Request failed:', error);
            throw error;
        }
    },

    /**
     * GET request helper
     */
    async get(endpoint, params = {}) {
        const url = new URL(`${this.baseUrl}${endpoint}`);
        Object.entries(params).forEach(([key, value]) => {
            if (value !== null && value !== undefined) {
                url.searchParams.set(key, value);
            }
        });
        
        return this.request(url.toString());
    },

    /**
     * POST request helper
     */
    async post(endpoint, data = {}) {
        return this.request(`${this.baseUrl}${endpoint}`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    /**
     * Routes API
     */
    routes: {
        /**
         * Calculate route between two points
         */
        async calculate(fromLat, fromLng, toLat, toLng, options = {}) {
            const params = {
                from_lat: fromLat,
                from_lng: fromLng,
                to_lat: toLat,
                to_lng: toLng,
                route_type: options.routeType || 'balanced',
                vehicle_type: options.vehicleType || 'car',
                avoid_tolls: options.avoidTolls || false,
                avoid_highways: options.avoidHighways || false
            };
            
            return SafeRouteAPI.get(SafeRouteAPI.endpoints.routes + '/calculate', params);
        },

        /**
         * Get route alternatives
         */
        async getAlternatives(fromLat, fromLng, toLat, toLng, options = {}) {
            const params = {
                from_lat: fromLat,
                from_lng: fromLng,
                to_lat: toLat,
                to_lng: toLng,
                alternatives: true,
                ...options
            };
            
            return SafeRouteAPI.get(SafeRouteAPI.endpoints.routes + '/alternatives', params);
        },

        /**
         * Optimize route with waypoints
         */
        async optimize(waypoints, options = {}) {
            const data = {
                waypoints: waypoints,
                ...options
            };
            
            return SafeRouteAPI.post(SafeRouteAPI.endpoints.routes + '/optimize', data);
        }
    },

    /**
     * Hotspots API
     */
    hotspots: {
        /**
         * Get hotspots in radius
         */
        async getInRadius(lat, lng, radius = 25, options = {}) {
            const params = {
                lat: lat,
                lng: lng,
                radius: radius,
                risk_filter: options.riskFilter,
                hotspot_type: options.hotspotType,
                limit: options.limit || 50
            };
            
            return SafeRouteAPI.get(SafeRouteAPI.endpoints.hotspots, params);
        },

        /**
         * Get personalized hotspots
         */
        async getPersonalized(lat, lng, radius = 25, preferences = {}) {
            const params = {
                lat: lat,
                lng: lng,
                radius: radius,
                ...preferences
            };
            
            return SafeRouteAPI.get(SafeRouteAPI.endpoints.hotspots + '/personalized', params);
        },

        /**
         * Get hotspot details
         */
        async getDetails(hotspotId) {
            return SafeRouteAPI.get(`${SafeRouteAPI.endpoints.hotspots}/${hotspotId}`);
        },

        /**
         * Report new hotspot
         */
        async report(lat, lng, type, description, options = {}) {
            const data = {
                latitude: lat,
                longitude: lng,
                type: type,
                description: description,
                ...options
            };
            
            return SafeRouteAPI.post(SafeRouteAPI.endpoints.hotspots + '/report', data);
        }
    },

    /**
     * Weather API
     */
    weather: {
        /**
         * Get current weather
         */
        async getCurrent(lat, lng) {
            const params = { lat, lng };
            return SafeRouteAPI.get(SafeRouteAPI.endpoints.weather + '/current', params);
        },

        /**
         * Get weather forecast
         */
        async getForecast(lat, lng, days = 5) {
            const params = { lat, lng, days };
            return SafeRouteAPI.get(SafeRouteAPI.endpoints.weather + '/forecast', params);
        },

        /**
         * Get weather alerts
         */
        async getAlerts(lat, lng) {
            const params = { lat, lng };
            return SafeRouteAPI.get(SafeRouteAPI.endpoints.weather + '/alerts', params);
        }
    },

    /**
     * Geocoding API
     */
    geocoding: {
        /**
         * Forward geocoding (address to coordinates)
         */
        async forward(address, options = {}) {
            const params = {
                q: address,
                limit: options.limit || 5,
                country: options.country || 'IN'
            };
            
            return SafeRouteAPI.get(SafeRouteAPI.endpoints.geocoding + '/forward', params);
        },

        /**
         * Reverse geocoding (coordinates to address)
         */
        async reverse(lat, lng, options = {}) {
            const params = {
                lat,
                lng,
                ...options
            };
            
            return SafeRouteAPI.get(SafeRouteAPI.endpoints.geocoding + '/reverse', params);
        },

        /**
         * Search for places
         */
        async search(query, lat = null, lng = null, options = {}) {
            const params = {
                q: query,
                limit: options.limit || 10
            };
            
            if (lat && lng) {
                params.proximity = `${lat},${lng}`;
            }
            
            return SafeRouteAPI.get(SafeRouteAPI.endpoints.geocoding + '/search', params);
        }
    },

    /**
     * Analytics API
     */
    analytics: {
        /**
         * Get route analytics
         */
        async getRouteStats() {
            return SafeRouteAPI.get(SafeRouteAPI.endpoints.analytics + '/routes');
        },

        /**
         * Get hotspot analytics
         */
        async getHotspotStats() {
            return SafeRouteAPI.get(SafeRouteAPI.endpoints.analytics + '/hotspots');
        },

        /**
         * Submit usage analytics
         */
        async submitUsage(eventType, data = {}) {
            const payload = {
                event_type: eventType,
                timestamp: SafeRouteUtils.getCurrentTimestamp(),
                data: data
            };
            
            return SafeRouteAPI.post(SafeRouteAPI.endpoints.analytics + '/usage', payload);
        }
    },

    /**
     * System API
     */
    system: {
        /**
         * Get system status
         */
        async getStatus() {
            return SafeRouteAPI.get(SafeRouteAPI.endpoints.status);
        },

        /**
         * Health check
         */
        async healthCheck() {
            return SafeRouteAPI.get(SafeRouteAPI.endpoints.status + '/health');
        }
    },

    /**
     * Cache management
     */
    cache: {
        store: new Map(),
        maxSize: SafeRouteConfig.performance.cacheSize,
        ttl: SafeRouteConfig.performance.cacheTTL,

        /**
         * Get cached response
         */
        get(key) {
            const item = this.store.get(key);
            if (!item) return null;
            
            if (Date.now() - item.timestamp > this.ttl) {
                this.store.delete(key);
                return null;
            }
            
            SafeRouteUtils.log.debug('Cache hit:', key);
            return item.data;
        },

        /**
         * Store response in cache
         */
        set(key, data) {
            // Clean up old entries if cache is full
            if (this.store.size >= this.maxSize) {
                const oldestKey = this.store.keys().next().value;
                this.store.delete(oldestKey);
            }
            
            this.store.set(key, {
                data: data,
                timestamp: Date.now()
            });
            
            SafeRouteUtils.log.debug('Cache set:', key);
        },

        /**
         * Clear cache
         */
        clear() {
            this.store.clear();
            SafeRouteUtils.log.debug('Cache cleared');
        }
    },

    /**
     * Cached request wrapper
     */
    async cachedRequest(endpoint, params = {}, options = {}) {
        const cacheKey = `${endpoint}_${JSON.stringify(params)}`;
        
        // Try cache first
        const cached = this.cache.get(cacheKey);
        if (cached && !options.noCache) {
            return cached;
        }
        
        // Make request
        const response = await this.get(endpoint, params);
        
        // Cache successful responses
        if (response && response.status === 'success') {
            this.cache.set(cacheKey, response);
        }
        
        return response;
    },

    /**
     * Retry mechanism for failed requests
     */
    async requestWithRetry(requestFn, maxRetries = SafeRouteConfig.api.retries) {
        let lastError;
        
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                SafeRouteUtils.log.debug(`API attempt ${attempt}/${maxRetries}`);
                return await requestFn();
            } catch (error) {
                lastError = error;
                
                if (attempt < maxRetries) {
                    const delay = Math.min(1000 * Math.pow(2, attempt - 1), 10000); // Exponential backoff
                    SafeRouteUtils.log.warn(`API attempt ${attempt} failed, retrying in ${delay}ms:`, error.message);
                    await new Promise(resolve => setTimeout(resolve, delay));
                } else {
                    SafeRouteUtils.log.error(`API failed after ${maxRetries} attempts:`, error);
                }
            }
        }
        
        throw lastError;
    },

    /**
     * Connection status checker
     */
    connection: {
        isOnline: true,
        
        /**
         * Check if API is accessible
         */
        async checkStatus() {
            try {
                await SafeRouteAPI.system.healthCheck();
                this.isOnline = true;
                this.updateConnectionIndicator(true);
                return true;
            } catch (error) {
                this.isOnline = false;
                this.updateConnectionIndicator(false);
                return false;
            }
        },

        /**
         * Update connection indicator in UI
         */
        updateConnectionIndicator(isOnline) {
            const indicator = document.getElementById('connectionStatus');
            if (indicator) {
                const icon = indicator.querySelector('i');
                const text = indicator.querySelector('span');
                
                if (isOnline) {
                    icon.className = 'fas fa-wifi';
                    icon.style.color = '#10B981';
                    text.textContent = 'Connected';
                } else {
                    icon.className = 'fas fa-wifi-slash';
                    icon.style.color = '#EF4444';
                    text.textContent = 'Offline';
                }
            }
        },

        /**
         * Start periodic connection monitoring
         */
        startMonitoring(interval = 30000) {
            this.checkStatus(); // Initial check
            
            setInterval(() => {
                this.checkStatus();
            }, interval);
        }
    }
};

// Export API for use in other modules
window.SafeRouteAPI = SafeRouteAPI;

// Start connection monitoring when API is loaded
document.addEventListener('DOMContentLoaded', () => {
    SafeRouteAPI.connection.startMonitoring();
});