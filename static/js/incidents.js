/**
 * RAKSHAK - Incident Reporting Module
 * Handles reporting of safety incidents by users and admins
 */

const IncidentReporter = {
    // Modal elements
    modal: null,
    form: null,
    
    /**
     * Initialize incident reporting module
     */
    init() {
        console.log('Initializing Incident Reporter...');
        
        // Get modal elements
        this.modal = document.getElementById('incidentModal');
        this.form = document.getElementById('incidentForm');
        
        // Setup event listeners
        this.setupEventListeners();
        
        console.log('Incident Reporter initialized');
    },
    
    /**
     * Setup event listeners for modal and form
     */
    setupEventListeners() {
        // Report incident button
        const reportBtn = document.getElementById('reportIncident');
        if (reportBtn) {
            reportBtn.addEventListener('click', () => this.openModal());
        }
        
        // Close modal button
        const closeBtn = document.getElementById('closeIncidentModal');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closeModal());
        }
        
        // Cancel button
        const cancelBtn = document.getElementById('cancelIncidentReport');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.closeModal());
        }
        
        // Modal overlay click
        const overlay = document.getElementById('incidentModalOverlay');
        if (overlay) {
            overlay.addEventListener('click', () => this.closeModal());
        }
        
        // Use map location button
        const useMapBtn = document.getElementById('useMapLocation');
        if (useMapBtn) {
            useMapBtn.addEventListener('click', () => this.useMapCenter());
        }
        
        // Form submission
        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }
    },
    
    /**
     * Open incident reporting modal
     */
    openModal() {
        if (!this.modal) return;
        
        // Set current location as default
        this.useMapCenter();
        
        // Show modal
        this.modal.style.display = 'block';
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
    },
    
    /**
     * Close incident reporting modal
     */
    closeModal() {
        if (!this.modal) return;
        
        // Hide modal
        this.modal.style.display = 'none';
        document.body.style.overflow = ''; // Restore scrolling
        
        // Reset form
        if (this.form) {
            this.form.reset();
        }
    },
    
    /**
     * Use map center as incident location
     */
    useMapCenter() {
        if (!window.SafeRouteMap || !SafeRouteMap.map) {
            console.error('Map not available');
            return;
        }
        
        const center = SafeRouteMap.map.getCenter();
        
        document.getElementById('incidentLat').value = center.lat.toFixed(6);
        document.getElementById('incidentLng').value = center.lng.toFixed(6);
        
        console.log(`Using map center: ${center.lat.toFixed(6)}, ${center.lng.toFixed(6)}`);
    },
    
    /**
     * Handle form submission
     */
    async handleSubmit(e) {
        e.preventDefault();
        
        try {
            // Get form data
            const incidentType = document.getElementById('incidentType').value;
            const severity = document.getElementById('incidentSeverity').value;
            const latitude = parseFloat(document.getElementById('incidentLat').value);
            const longitude = parseFloat(document.getElementById('incidentLng').value);
            const description = document.getElementById('incidentDescription').value;
            
            // Validate
            if (!incidentType || !severity) {
                SafeRouteUtils.showNotification('Please fill all required fields', 'warning');
                return;
            }
            
            if (isNaN(latitude) || isNaN(longitude)) {
                SafeRouteUtils.showNotification('Invalid location coordinates', 'error');
                return;
            }
            
            // Prepare incident data
            const incidentData = {
                incident_type: incidentType,
                severity: severity,
                latitude: latitude,
                longitude: longitude,
                description: description,
                reporter_type: 'user', // or 'admin' if admin user
                user_id: null // Optional: Add user ID if authenticated
            };
            
            // Show loading
            const submitBtn = document.getElementById('submitIncidentReport');
            const originalText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
            
            // Submit to API
            const response = await fetch('/api/incidents/report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(incidentData)
            });
            
            const result = await response.json();
            
            // Restore button
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
            
            if (response.ok && result.status === 'success') {
                SafeRouteUtils.showNotification('Incident reported successfully!', 'success');
                this.closeModal();
                
                // Add marker to map
                this.addIncidentMarker(result.data);
                
                // Reload hotspots to include new incident
                if (window.SafeRouteApp && SafeRouteApp.state.currentLocation) {
                    setTimeout(() => {
                        SafeRouteApp.loadHotspots(
                            SafeRouteApp.state.currentLocation.latitude,
                            SafeRouteApp.state.currentLocation.longitude
                        );
                    }, 1000);
                }
            } else {
                SafeRouteUtils.showNotification(
                    result.message || 'Failed to report incident',
                    'error'
                );
            }
            
        } catch (error) {
            console.error('Incident reporting error:', error);
            SafeRouteUtils.showNotification('Failed to report incident: ' + error.message, 'error');
            
            // Restore button
            const submitBtn = document.getElementById('submitIncidentReport');
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Submit Report';
        }
    },
    
    /**
     * Add incident marker to map
     */
    addIncidentMarker(incident) {
        if (!window.SafeRouteMap || !SafeRouteMap.map) return;
        
        const iconHtml = `
            <div class="incident-marker" style="
                width: 28px;
                height: 28px;
                background: #e74c3c;
                border: 3px solid white;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3);
                animation: pulse-incident 2s infinite;
            ">
                <i class="fas fa-exclamation" style="color: white; font-size: 14px;"></i>
            </div>
        `;
        
        const icon = L.divIcon({
            html: iconHtml,
            className: 'custom-incident-marker',
            iconSize: [28, 28],
            iconAnchor: [14, 14],
            popupAnchor: [0, -14]
        });
        
        const marker = L.marker([incident.latitude, incident.longitude], { icon })
            .bindPopup(`
                <div class="incident-popup">
                    <h4>Reported Incident</h4>
                    <div class="info-row">
                        <strong>Type:</strong>
                        <span>${incident.incident_type.replace('_', ' ')}</span>
                    </div>
                    <div class="info-row">
                        <strong>Severity:</strong>
                        <span class="severity-badge ${incident.severity}">${incident.severity}</span>
                    </div>
                    <div class="info-row">
                        <strong>Status:</strong>
                        <span>${incident.verified ? 'Verified' : 'Pending Verification'}</span>
                    </div>
                    <div class="info-row">
                        <strong>Reported:</strong>
                        <span>Just now</span>
                    </div>
                </div>
            `)
            .addTo(SafeRouteMap.layers.markers);
        
        // Center on new incident
        SafeRouteMap.map.setView([incident.latitude, incident.longitude], 15);
        marker.openPopup();
    }
};

// Add CSS for pulse animation
const style = document.createElement('style');
style.textContent = `
    @keyframes pulse-incident {
        0%, 100% {
            transform: scale(1);
            opacity: 1;
        }
        50% {
            transform: scale(1.1);
            opacity: 0.8;
        }
    }
    
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.6);
        z-index: 10000;
    }
    
    .severity-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 12px;
        text-transform: uppercase;
    }
    
    .severity-badge.low {
        background: #51cf66;
        color: white;
    }
    
    .severity-badge.medium {
        background: #ffa500;
        color: white;
    }
    
    .severity-badge.high {
        background: #ff6b6b;
        color: white;
    }
    
    .severity-badge.critical {
        background: #8B0000;
        color: white;
    }
`;
document.head.appendChild(style);

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.IncidentReporter = IncidentReporter;
}
