/**
 * SafeRoute Navigator v2.0 - Configuration
 * Application-wide configuration settings
 */

const SafeRouteConfig = {
    // API Configuration
    api: {
        baseUrl: window.location.origin,
        endpoints: {
            routes: '/api/routes',
            hotspots: '/api/hotspots',
            weather: '/api/weather',
            geocoding: '/api/geocoding',
            analytics: '/api/analytics',
            status: '/api/status'
        },
        timeout: 30000, // 30 seconds
        retries: 3
    },

    // Map Configuration
    map: {
        // Default center (India)
        defaultCenter: [20.5937, 78.9629],
        defaultZoom: 5,
        maxZoom: 18,
        minZoom: 4,
        
        // Tile layers
        tileLayers: {
            default: {
                url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
                attribution: '© OpenStreetMap contributors',
                maxZoom: 18
            },
            satellite: {
                url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                attribution: '© Esri',
                maxZoom: 17
            }
        },

        // Marker styles
        markers: {
            start: {
                color: '#10B981',
                icon: 'fa-play',
                size: 'large'
            },
            end: {
                color: '#EF4444',
                icon: 'fa-flag-checkered',
                size: 'large'
            },
            hotspot: {
                colors: {
                    very_high: '#EF4444',
                    high: '#F97316',
                    medium: '#EAB308',
                    low: '#22C55E',
                    very_low: '#6B7280'
                }
            }
        },

        // Route styles
        routes: {
            recommended: {
                color: '#4F46E5',
                weight: 6,
                opacity: 0.8
            },
            alternative: {
                color: '#6B7280',
                weight: 4,
                opacity: 0.6
            }
        }
    },

    // Weather Configuration
    weather: {
        updateInterval: 10 * 60 * 1000, // 10 minutes
        units: 'metric',
        icons: {
            '01d': 'fa-sun',
            '01n': 'fa-moon',
            '02d': 'fa-cloud-sun',
            '02n': 'fa-cloud-moon',
            '03d': 'fa-cloud',
            '03n': 'fa-cloud',
            '04d': 'fa-cloud',
            '04n': 'fa-cloud',
            '09d': 'fa-cloud-rain',
            '09n': 'fa-cloud-rain',
            '10d': 'fa-cloud-sun-rain',
            '10n': 'fa-cloud-moon-rain',
            '11d': 'fa-bolt',
            '11n': 'fa-bolt',
            '13d': 'fa-snowflake',
            '13n': 'fa-snowflake',
            '50d': 'fa-smog',
            '50n': 'fa-smog'
        }
    },

    // Hotspots Configuration
    hotspots: {
        refreshInterval: 5 * 60 * 1000, // 5 minutes
        maxRadius: 50, // kilometers
        defaultRadius: 25,
        types: {
            accident_prone: {
                icon: 'fa-car-crash',
                color: '#EF4444',
                priority: 'high'
            },
            traffic_congestion: {
                icon: 'fa-traffic-light',
                color: '#F59E0B',
                priority: 'medium'
            },
            construction: {
                icon: 'fa-hard-hat',
                color: '#F97316',
                priority: 'medium'
            },
            flooding_risk: {
                icon: 'fa-water',
                color: '#3B82F6',
                priority: 'critical'
            },
            weather_risk: {
                icon: 'fa-cloud-rain',
                color: '#6B7280',
                priority: 'low'
            },
            pedestrian_risk: {
                icon: 'fa-walking',
                color: '#EC4899',
                priority: 'high'
            }
        }
    },

    // UI Configuration
    ui: {
        notifications: {
            duration: 5000, // 5 seconds
            position: 'top-right'
        },
        animations: {
            enabled: true,
            duration: 300
        },
        sidebar: {
            defaultExpanded: true,
            breakpoint: 768 // px
        }
    },

    // Performance Configuration
    performance: {
        debounceTime: 300, // milliseconds
        throttleTime: 100, // milliseconds
        cacheSize: 100, // number of cached items
        cacheTTL: 10 * 60 * 1000 // 10 minutes
    },

    // Geolocation Configuration
    geolocation: {
        timeout: 10000, // 10 seconds
        maximumAge: 5 * 60 * 1000, // 5 minutes
        enableHighAccuracy: true
    },

    // Debug Configuration
    debug: {
        enabled: window.location.hostname === 'localhost',
        logLevel: 'info', // 'debug', 'info', 'warn', 'error'
        showPerformance: false
    },

    // Application Metadata
    app: {
        name: 'SafeRoute Navigator',
        version: '2.0.0',
        author: 'SafeRoute Team',
        description: 'AI-Powered Route Safety Intelligence'
    }
};

// Export configuration for use in other modules
window.SafeRouteConfig = SafeRouteConfig;

// Freeze configuration to prevent modification
Object.freeze(SafeRouteConfig);

// Log configuration if debug enabled
if (SafeRouteConfig.debug.enabled) {
    console.info('SafeRoute Navigator Configuration:', SafeRouteConfig);
}