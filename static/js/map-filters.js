/**
 * RAKSHAK - Map Filters and Layer Controls
 * Handles filtering hotspots by risk level and type, and toggling map layers
 */

const MapFilters = {
    // Active filters
    activeFilters: {
        riskLevels: new Set(['low', 'medium', 'high', 'critical']), // All enabled by default
        hotspotTypes: new Set(), // Empty = all types shown
        showHospitals: true,
        showPolice: true,
        showAmbulances: true
    },
    
    // All hotspots data
    allHotspots: [],
    
    /**
     * Initialize filter controls
     */
    init() {
        console.log('Initializing Map Filters...');
        this.setupFilterListeners();
        this.setupLayerToggles();
        console.log('Map Filters initialized');
    },
    
    /**
     * Set hotspots data
     */
    setHotspots(hotspots) {
        this.allHotspots = hotspots;
        this.applyFilters();
    },
    
    /**
     * Setup risk level filter listeners
     */
    setupFilterListeners() {
        // Risk level checkboxes
        const riskCheckboxes = document.querySelectorAll('.risk-filter-checkbox');
        riskCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const riskLevel = e.target.value;
                if (e.target.checked) {
                    this.activeFilters.riskLevels.add(riskLevel);
                } else {
                    this.activeFilters.riskLevels.delete(riskLevel);
                }
                this.applyFilters();
            });
        });
        
        // Hotspot type filters
        const typeSelectors = document.querySelectorAll('.hotspot-type-filter');
        typeSelectors.forEach(selector => {
            selector.addEventListener('change', (e) => {
                const selectedType = e.target.value;
                if (selectedType === 'all') {
                    this.activeFilters.hotspotTypes.clear();
                } else {
                    this.activeFilters.hotspotTypes.clear();
                    this.activeFilters.hotspotTypes.add(selectedType);
                }
                this.applyFilters();
            });
        });
        
        // Reset filters button
        const resetBtn = document.getElementById('resetFiltersBtn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.resetFilters());
        }
    },
    
    /**
     * Setup layer toggle switches
     */
    setupLayerToggles() {
        // Hospital layer toggle
        const hospitalToggle = document.getElementById('toggleHospitals');
        if (hospitalToggle) {
            hospitalToggle.addEventListener('change', (e) => {
                this.activeFilters.showHospitals = e.target.checked;
                this.toggleLayer('hospitals', e.target.checked);
            });
        }
        
        // Police layer toggle
        const policeToggle = document.getElementById('togglePolice');
        if (policeToggle) {
            policeToggle.addEventListener('change', (e) => {
                this.activeFilters.showPolice = e.target.checked;
                this.toggleLayer('police', e.target.checked);
            });
        }
        
        // Ambulance layer toggle
        const ambulanceToggle = document.getElementById('toggleAmbulances');
        if (ambulanceToggle) {
            ambulanceToggle.addEventListener('change', (e) => {
                this.activeFilters.showAmbulances = e.target.checked;
                this.toggleLayer('ambulances', e.target.checked);
            });
        }
    },
    
    /**
     * Apply all active filters to hotspots
     */
    applyFilters() {
        if (!this.allHotspots || this.allHotspots.length === 0) {
            console.log('No hotspots to filter');
            return;
        }
        
        // Filter hotspots based on active filters
        const filteredHotspots = this.allHotspots.filter(hotspot => {
            // Filter by risk level
            const riskLevel = this.getRiskLevelName(hotspot.risk_level);
            if (!this.activeFilters.riskLevels.has(riskLevel)) {
                return false;
            }
            
            // Filter by type (if any type filter is active)
            if (this.activeFilters.hotspotTypes.size > 0) {
                const hotspotType = hotspot.type || 'unknown';
                if (!this.activeFilters.hotspotTypes.has(hotspotType)) {
                    return false;
                }
            }
            
            return true;
        });
        
        console.log(`Filtered hotspots: ${filteredHotspots.length} of ${this.allHotspots.length}`);
        
        // Update map with filtered hotspots
        if (window.SafeRouteMap && window.SafeRouteMap.addHotspots) {
            window.SafeRouteMap.addHotspots(filteredHotspots);
        }
        
        // Update filter count display
        this.updateFilterCount(filteredHotspots.length, this.allHotspots.length);
    },
    
    /**
     * Toggle specific layer visibility
     */
    toggleLayer(layerName, show) {
        console.log(`Toggling ${layerName} layer: ${show}`);
        
        if (window.SafeRouteMap && window.SafeRouteMap.layers) {
            const layer = window.SafeRouteMap.layers[layerName];
            
            if (layer) {
                if (show) {
                    window.SafeRouteMap.map.addLayer(layer);
                } else {
                    window.SafeRouteMap.map.removeLayer(layer);
                }
            }
        }
    },
    
    /**
     * Reset all filters to default
     */
    resetFilters() {
        // Reset risk levels (all enabled)
        this.activeFilters.riskLevels = new Set(['low', 'medium', 'high', 'critical']);
        
        // Reset type filter
        this.activeFilters.hotspotTypes.clear();
        
        // Reset layer toggles
        this.activeFilters.showHospitals = true;
        this.activeFilters.showPolice = true;
        this.activeFilters.showAmbulances = true;
        
        // Update UI
        document.querySelectorAll('.risk-filter-checkbox').forEach(cb => {
            cb.checked = true;
        });
        
        document.querySelectorAll('.hotspot-type-filter').forEach(select => {
            select.value = 'all';
        });
        
        document.querySelectorAll('.layer-toggle').forEach(toggle => {
            toggle.checked = true;
        });
        
        // Reapply filters
        this.applyFilters();
        
        // Show all layers
        this.toggleLayer('hospitals', true);
        this.toggleLayer('police', true);
        this.toggleLayer('ambulances', true);
        
        console.log('Filters reset to default');
    },
    
    /**
     * Get risk level name from numeric value
     */
    getRiskLevelName(riskLevel) {
        if (riskLevel <= 1) return 'low';
        if (riskLevel === 2) return 'medium';
        if (riskLevel === 3) return 'high';
        return 'critical';
    },
    
    /**
     * Update filter count display
     */
    updateFilterCount(filtered, total) {
        const countDisplay = document.getElementById('filterCount');
        if (countDisplay) {
            countDisplay.textContent = `Showing ${filtered} of ${total} hotspots`;
        }
    },
    
    /**
     * Get current filter state
     */
    getFilterState() {
        return {
            riskLevels: Array.from(this.activeFilters.riskLevels),
            hotspotTypes: Array.from(this.activeFilters.hotspotTypes),
            showHospitals: this.activeFilters.showHospitals,
            showPolice: this.activeFilters.showPolice,
            showAmbulances: this.activeFilters.showAmbulances
        };
    },
    
    /**
     * Restore filter state
     */
    restoreFilterState(state) {
        this.activeFilters.riskLevels = new Set(state.riskLevels);
        this.activeFilters.hotspotTypes = new Set(state.hotspotTypes);
        this.activeFilters.showHospitals = state.showHospitals;
        this.activeFilters.showPolice = state.showPolice;
        this.activeFilters.showAmbulances = state.showAmbulances;
        this.applyFilters();
    }
};

// Export for use
window.MapFilters = MapFilters;

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => MapFilters.init());
} else {
    MapFilters.init();
}
