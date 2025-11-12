/**
 * SafeRoute Navigator v2.0 - Utility Functions
 * Common utility functions used throughout the application
 */

const SafeRouteUtils = {
    /**
     * Debounce function to limit the rate of function execution
     */
    debounce(func, wait, immediate = false) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func(...args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func(...args);
        };
    },

    /**
     * Throttle function to limit function execution rate
     */
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    /**
     * Format distance for display
     */
    formatDistance(distance) {
        if (distance < 1) {
            return `${Math.round(distance * 1000)}m`;
        } else if (distance < 10) {
            return `${distance.toFixed(1)}km`;
        } else {
            return `${Math.round(distance)}km`;
        }
    },

    /**
     * Format duration for display
     */
    formatDuration(minutes) {
        if (minutes < 60) {
            return `${Math.round(minutes)}m`;
        } else {
            const hours = Math.floor(minutes / 60);
            const remainingMinutes = Math.round(minutes % 60);
            return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
        }
    },

    /**
     * Format risk level for display
     */
    formatRiskLevel(riskLevel) {
        return riskLevel.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    },

    /**
     * Get risk color based on risk level
     */
    getRiskColor(riskLevel) {
        const colors = SafeRouteConfig.map.markers.hotspot.colors;
        return colors[riskLevel] || colors.medium;
    },

    /**
     * Get risk class for CSS styling
     */
    getRiskClass(riskLevel) {
        return `risk-${riskLevel.replace('_', '-')}`;
    },

    /**
     * Calculate distance between two coordinates (Haversine formula)
     */
    calculateDistance(lat1, lng1, lat2, lng2) {
        const R = 6371; // Earth's radius in kilometers
        const dLat = this.toRadians(lat2 - lat1);
        const dLng = this.toRadians(lng2 - lng1);
        const a = 
            Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(this.toRadians(lat1)) * Math.cos(this.toRadians(lat2)) *
            Math.sin(dLng/2) * Math.sin(dLng/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    },

    /**
     * Convert degrees to radians
     */
    toRadians(degrees) {
        return degrees * (Math.PI / 180);
    },

    /**
     * Get current timestamp
     */
    getCurrentTimestamp() {
        return new Date().toISOString();
    },

    /**
     * Format timestamp for display
     */
    formatTimestamp(timestamp, options = {}) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);

        if (options.relative !== false) {
            if (diffMins < 1) return 'Just now';
            if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
            
            const diffHours = Math.floor(diffMins / 60);
            if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
            
            const diffDays = Math.floor(diffHours / 24);
            if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
        }

        return date.toLocaleString();
    },

    /**
     * Show notification to user
     */
    showNotification(message, type = 'info', duration = null) {
        const notificationsContainer = document.getElementById('notifications');
        if (!notificationsContainer) return;

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas ${this.getNotificationIcon(type)}"></i>
                <span>${message}</span>
            </div>
            <button class="notification-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;

        notificationsContainer.appendChild(notification);

        // Auto-remove after duration
        const timeout = duration || SafeRouteConfig.ui.notifications.duration;
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, timeout);

        return notification;
    },

    /**
     * Get notification icon based on type
     */
    getNotificationIcon(type) {
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        return icons[type] || icons.info;
    },

    /**
     * Show loading overlay
     */
    showLoading(message = 'Loading...') {
        const overlay = document.getElementById('loadingOverlay');
        const text = document.getElementById('loadingText');
        if (overlay && text) {
            text.textContent = message;
            overlay.style.display = 'flex';
        }
    },

    /**
     * Hide loading overlay
     */
    hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    },

    /**
     * Show/hide map loading indicator
     */
    toggleMapLoading(show, message = 'Loading route data...') {
        const mapLoading = document.getElementById('mapLoading');
        if (mapLoading) {
            if (show) {
                mapLoading.querySelector('p').textContent = message;
                mapLoading.style.display = 'block';
            } else {
                mapLoading.style.display = 'none';
            }
        }
    },

    /**
     * Validate coordinates
     */
    isValidCoordinate(lat, lng) {
        return lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180;
    },

    /**
     * Sanitize HTML to prevent XSS
     */
    sanitizeHtml(html) {
        const div = document.createElement('div');
        div.textContent = html;
        return div.innerHTML;
    },

    /**
     * Generate unique ID
     */
    generateId(prefix = 'id') {
        return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    },

    /**
     * Deep clone object
     */
    deepClone(obj) {
        if (obj === null || typeof obj !== 'object') return obj;
        if (obj instanceof Date) return new Date(obj.getTime());
        if (obj instanceof Array) return obj.map(item => this.deepClone(item));
        if (typeof obj === 'object') {
            const cloned = {};
            for (const key in obj) {
                if (obj.hasOwnProperty(key)) {
                    cloned[key] = this.deepClone(obj[key]);
                }
            }
            return cloned;
        }
    },

    /**
     * Get user's current location
     */
    getCurrentLocation(options = {}) {
        return new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                reject(new Error('Geolocation is not supported'));
                return;
            }

            const config = {
                ...SafeRouteConfig.geolocation,
                ...options
            };

            navigator.geolocation.getCurrentPosition(
                position => {
                    resolve({
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                        accuracy: position.coords.accuracy
                    });
                },
                error => {
                    let message = 'Unable to get location';
                    switch (error.code) {
                        case error.PERMISSION_DENIED:
                            message = 'Location access denied by user';
                            break;
                        case error.POSITION_UNAVAILABLE:
                            message = 'Location information unavailable';
                            break;
                        case error.TIMEOUT:
                            message = 'Location request timed out';
                            break;
                    }
                    reject(new Error(message));
                },
                config
            );
        });
    },

    /**
     * Storage helpers
     */
    storage: {
        set(key, value, expiry = null) {
            const item = {
                value: value,
                timestamp: Date.now(),
                expiry: expiry
            };
            localStorage.setItem(key, JSON.stringify(item));
        },

        get(key) {
            try {
                const item = JSON.parse(localStorage.getItem(key));
                if (!item) return null;

                // Check if expired
                if (item.expiry && Date.now() > item.timestamp + item.expiry) {
                    localStorage.removeItem(key);
                    return null;
                }

                return item.value;
            } catch (e) {
                return null;
            }
        },

        remove(key) {
            localStorage.removeItem(key);
        },

        clear() {
            localStorage.clear();
        }
    },

    /**
     * URL helpers
     */
    url: {
        /**
         * Parse URL parameters
         */
        parseParams(url = window.location.href) {
            const params = {};
            const urlObj = new URL(url);
            urlObj.searchParams.forEach((value, key) => {
                params[key] = value;
            });
            return params;
        },

        /**
         * Update URL parameters
         */
        updateParams(params, replace = false) {
            const url = new URL(window.location);
            Object.entries(params).forEach(([key, value]) => {
                if (value === null || value === undefined) {
                    url.searchParams.delete(key);
                } else {
                    url.searchParams.set(key, value);
                }
            });

            if (replace) {
                window.history.replaceState({}, '', url);
            } else {
                window.history.pushState({}, '', url);
            }
        }
    },

    /**
     * Performance helpers
     */
    performance: {
        mark(name) {
            if (SafeRouteConfig.debug.showPerformance && performance.mark) {
                performance.mark(name);
            }
        },

        measure(name, startMark, endMark) {
            if (SafeRouteConfig.debug.showPerformance && performance.measure) {
                try {
                    performance.measure(name, startMark, endMark);
                    const measure = performance.getEntriesByName(name)[0];
                    console.log(`Performance: ${name} took ${measure.duration.toFixed(2)}ms`);
                } catch (e) {
                    console.warn('Performance measurement failed:', e);
                }
            }
        }
    },

    /**
     * Logging helpers
     */
    log: {
        debug(...args) {
            if (SafeRouteConfig.debug.enabled && ['debug'].includes(SafeRouteConfig.debug.logLevel)) {
                console.debug(...args);
            }
        },

        info(...args) {
            if (SafeRouteConfig.debug.enabled && ['debug', 'info'].includes(SafeRouteConfig.debug.logLevel)) {
                console.info(...args);
            }
        },

        warn(...args) {
            if (SafeRouteConfig.debug.enabled && ['debug', 'info', 'warn'].includes(SafeRouteConfig.debug.logLevel)) {
                console.warn(...args);
            }
        },

        error(...args) {
            console.error(...args);
        }
    }
};

// Export utils for use in other modules
window.SafeRouteUtils = SafeRouteUtils;

// Freeze utils to prevent modification
Object.freeze(SafeRouteUtils);