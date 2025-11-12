/**
 * RAKSHAK - Emergency Command Center
 * Complete emergency response management system
 */

const EmergencyCommand = {
    // Map instance
    map: null,
    
    // Layer groups
    layers: {
        ambulances: null,
        police: null,
        ndrf: null,
        relief: null,
        hospitals: null,
        hotspots: null
    },
    
    // Cluster groups for large datasets
    clusterGroups: {
        hospitals: null,
        police: null
    },
    
    // Data storage
    data: {
        ambulances: [],
        police: [],
        ndrf: [],
        relief: [],
        hospitals: [],
        hotspots: []
    },
    
    // Selected resource for dispatch
    selectedResource: null,
    
    /**
     * Initialize Emergency Command Center
     */
    async init() {
        console.log('Initializing Emergency Command Center...');
        
        // Initialize map
        this.initMap();
        
        // Initialize tabs
        this.initTabs();
        
        // Initialize filters
        this.initFilters();
        
        // Initialize dispatch modal
        this.initDispatchModal();
        
        // Load all data
        await this.loadAllData();
        
        console.log('Emergency Command Center initialized');
    },
    
    /**
     * Initialize map
     */
    initMap() {
        this.map = L.map('commandMap').setView([28.6139, 77.2090], 6);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(this.map);
        
        // Initialize layer groups
        this.layers.ambulances = L.layerGroup().addTo(this.map);
        this.layers.ndrf = L.layerGroup().addTo(this.map);
        this.layers.relief = L.layerGroup().addTo(this.map);
        this.layers.hotspots = L.layerGroup().addTo(this.map);

        // Initialize cluster groups for heavy layers
        this.clusterGroups.hospitals = L.markerClusterGroup({
            maxClusterRadius: 60,
            disableClusteringAtZoom: 14,
        }).addTo(this.map);
        this.clusterGroups.police = L.markerClusterGroup({
            maxClusterRadius: 60,
            disableClusteringAtZoom: 14,
        }).addTo(this.map);
        
        // Map click for dispatch location
        this.map.on('click', (e) => {
            if (document.getElementById('dispatchModal').style.display === 'block') {
                document.getElementById('dispatch-lat').value = e.latlng.lat.toFixed(6);
                document.getElementById('dispatch-lng').value = e.latlng.lng.toFixed(6);
            }
        });
    },
    
    /**
     * Initialize tabs
     */
    initTabs() {
        const tabs = document.querySelectorAll('.command-tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                // Remove active from all tabs
                tabs.forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                
                // Add active to clicked tab
                tab.classList.add('active');
                const tabName = tab.dataset.tab;
                document.getElementById(`${tabName}-tab`).classList.add('active');
                
                // Show corresponding markers on map
                this.showLayerForTab(tabName);
            });
        });
    },
    
    /**
     * Show layer for active tab
     */
    showLayerForTab(tabName) {
        // Hide all resource layers
        Object.keys(this.layers).forEach(key => {
            if (key !== 'hospitals' && key !== 'hotspots') {
                this.map.removeLayer(this.layers[key]);
            }
        });
        
        // Show selected layer
        if (this.layers[tabName]) {
            this.map.addLayer(this.layers[tabName]);
        }
    },
    
    /**
     * Initialize filters
     */
    initFilters() {
        // Ambulance filters
        document.getElementById('ambulance-status-filter')?.addEventListener('change', () => this.filterAmbulances());
        document.getElementById('ambulance-city-filter')?.addEventListener('change', () => this.filterAmbulances());
        
        // Police filters
        document.getElementById('police-city-filter')?.addEventListener('change', () => this.filterPolice());
        
        // NDRF filters
        document.getElementById('ndrf-specialization-filter')?.addEventListener('change', () => this.filterNDRF());
        
        // Relief filters
        document.getElementById('relief-type-filter')?.addEventListener('change', () => this.filterRelief());
    },
    
    /**
     * Initialize dispatch modal
     */
    initDispatchModal() {
        document.getElementById('closeDispatchModal')?.addEventListener('click', () => this.closeDispatchModal());
        document.getElementById('cancelDispatch')?.addEventListener('click', () => this.closeDispatchModal());
        
        document.getElementById('dispatchForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleDispatch();
        });
        
        document.querySelector('.modal-overlay')?.addEventListener('click', () => this.closeDispatchModal());
    },
    
    /**
     * Load all data
     */
    async loadAllData() {
        try {
            await Promise.all([
                this.loadAmbulances(),
                this.loadPolice(),
                this.loadNDRF(),
                this.loadRelief(),
                this.loadHospitals(),
                this.loadHotspots()
            ]);
            
            console.log('All emergency data loaded');
        } catch (error) {
            console.error('Error loading emergency data:', error);
        }
    },
    
    /**
     * Load ambulances
     */
    async loadAmbulances() {
        try {
            const response = await fetch('/api/emergency/ambulances?mode=demo', { credentials: 'same-origin' });
            const result = await response.json();
            
            if (result.status === 'success') {
                this.data.ambulances = result.data.ambulances;
                this.displayAmbulances(this.data.ambulances);
                this.updateAmbulanceStats();
                console.log(`Loaded ${this.data.ambulances.length} ambulances`);
            }
        } catch (error) {
            console.error('Error loading ambulances:', error);
        }
    },
    
    /**
     * Load police units (nationwide cached dataset)
     */
    async loadPolice() {
        try {
            const response = await fetch('/api/emergency/police-stations?limit=100000', { credentials: 'same-origin' });
            const result = await response.json();
            
            if (result.status === 'success') {
                // Add status to police stations
                this.data.police = result.data.police_stations.map((station, i) => ({
                    ...station,
                    id: `POLICE-${i + 1}`,
                    status: i % 3 === 0 ? 'deployed' : 'available',
                    units: Math.floor(Math.random() * 5) + 2,
                    personnel: Math.floor(Math.random() * 20) + 10
                }));
                
                this.displayPolice(this.data.police);
                this.updatePoliceStats();
                console.log(`Loaded ${this.data.police.length} police units`);
            }
        } catch (error) {
            console.error('Error loading police:', error);
        }
    },
    
    /**
     * Load NDRF teams
     */
    async loadNDRF() {
        // Generate demo NDRF teams
        this.data.ndrf = [
            {
                id: 'NDRF-1-Delhi',
                name: 'NDRF Battalion 1 (Delhi)',
                latitude: 28.6139,
                longitude: 77.2090,
                specialization: 'flood',
                personnel: 45,
                equipment: ['Rescue Boats', 'Life Jackets', 'Pumps'],
                status: 'available'
            },
            {
                id: 'NDRF-2-Mumbai',
                name: 'NDRF Battalion 2 (Mumbai)',
                latitude: 19.0760,
                longitude: 72.8777,
                specialization: 'earthquake',
                personnel: 52,
                equipment: ['Search & Rescue', 'Medical Kits', 'Heavy Machinery'],
                status: 'available'
            },
            {
                id: 'NDRF-3-Bangalore',
                name: 'NDRF Battalion 3 (Bangalore)',
                latitude: 12.9716,
                longitude: 77.5946,
                specialization: 'fire',
                personnel: 38,
                equipment: ['Fire Equipment', 'Hazmat Suits', 'Medical Supplies'],
                status: 'available'
            },
            {
                id: 'NDRF-4-Chennai',
                name: 'NDRF Battalion 4 (Chennai)',
                latitude: 13.0827,
                longitude: 80.2707,
                specialization: 'flood',
                personnel: 41,
                equipment: ['Rescue Boats', 'Diving Gear', 'Communication Equipment'],
                status: 'deployed'
            },
            {
                id: 'NDRF-5-Kolkata',
                name: 'NDRF Battalion 5 (Kolkata)',
                latitude: 22.5726,
                longitude: 88.3639,
                specialization: 'flood',
                personnel: 47,
                equipment: ['Rescue Boats', 'Pumps', 'Medical Kits'],
                status: 'available'
            }
        ];
        
        this.displayNDRF(this.data.ndrf);
        this.updateNDRFStats();
        console.log(`Loaded ${this.data.ndrf.length} NDRF teams`);
    },
    
    /**
     * Load relief equipment
     */
    async loadRelief() {
        // Generate demo relief centers
        this.data.relief = [
            {
                id: 'RELIEF-DL-1',
                name: 'Delhi Relief Warehouse',
                latitude: 28.7041,
                longitude: 77.1025,
                type: 'warehouse',
                supplies: {
                    medical: 5000,
                    food: 10000,
                    shelter: 2000,
                    equipment: 1500
                },
                capacity: '50,000 items',
                status: 'operational'
            },
            {
                id: 'RELIEF-MH-1',
                name: 'Mumbai Relief Center',
                latitude: 19.0176,
                longitude: 72.8561,
                type: 'warehouse',
                supplies: {
                    medical: 4500,
                    food: 8000,
                    shelter: 1800,
                    equipment: 1200
                },
                capacity: '45,000 items',
                status: 'operational'
            },
            {
                id: 'RELIEF-KA-1',
                name: 'Bangalore Supply Point',
                latitude: 12.9716,
                longitude: 77.5946,
                type: 'supply_point',
                supplies: {
                    medical: 3000,
                    food: 5000,
                    shelter: 1000,
                    equipment: 800
                },
                capacity: '25,000 items',
                status: 'operational'
            }
        ];
        
        this.displayRelief(this.data.relief);
        this.updateReliefStats();
        console.log(`Loaded ${this.data.relief.length} relief centers`);
    },
    
    /**
     * Load hospitals (nationwide)
     */
    async loadHospitals() {
        try {
            const response = await fetch('/api/emergency/hospitals?limit=100000', { credentials: 'same-origin' });
            const result = await response.json();
            
            if (result.status === 'success') {
                this.data.hospitals = result.data.hospitals;
                this.displayHospitals(this.data.hospitals);
                console.log(`Loaded ${this.data.hospitals.length} hospitals`);
            }
        } catch (error) {
            console.error('Error loading hospitals:', error);
        }
    },
    
    /**
     * Load hotspots
     */
    async loadHotspots() {
        try {
            const response = await fetch('/api/hotspots?limit=50');
            const result = await response.json();
            
            if (result.status === 'success') {
                this.data.hotspots = result.data.hotspots;
                this.displayHotspots(this.data.hotspots);
                console.log(`Loaded ${this.data.hotspots.length} hotspots`);
            }
        } catch (error) {
            console.error('Error loading hotspots:', error);
        }
    },
    
    /**
     * Display ambulances
     */
    displayAmbulances(ambulances) {
        this.layers.ambulances.clearLayers();
        
        const listHtml = ambulances.map(amb => {
            const statusClass = `status-${amb.status.replace('-', '')}`;
            return `
                <div class="resource-card" data-resource-type="ambulance" data-resource-id="${amb.id}">
                    <div class="resource-header">
                        <div class="resource-id">${amb.id}</div>
                        <span class="status-badge ${statusClass}">${amb.status}</span>
                    </div>
                    <div class="resource-details">
                        <div><i class="fas fa-hospital"></i> ${amb.hospital}</div>
                        <div><i class="fas fa-map-marker-alt"></i> ${amb.city}</div>
                        <div><i class="fas fa-map-pin"></i> ${amb.latitude.toFixed(4)}, ${amb.longitude.toFixed(4)}</div>
                    </div>
                    <div class="resource-actions">
                        <button class="action-btn dispatch" onclick="EmergencyCommand.openDispatch('${amb.id}', 'ambulance')">
                            <i class="fas fa-paper-plane"></i> Dispatch
                        </button>
                        <button class="action-btn track" onclick="EmergencyCommand.trackResource('${amb.id}', ${amb.latitude}, ${amb.longitude})">
                            <i class="fas fa-crosshairs"></i> Track
                        </button>
                    </div>
                </div>
            `;
        }).join('');
        
        document.getElementById('ambulances-list').innerHTML = listHtml;
        
        // Add to map
        ambulances.forEach(amb => {
            const icon = L.divIcon({
                html: '<div style="background: #f39c12; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; border: 3px solid white; box-shadow: 0 2px 6px rgba(0,0,0,0.3);"><i class="fas fa-ambulance"></i></div>',
                className: '',
                iconSize: [32, 32],
                iconAnchor: [16, 16]
            });
            
            L.marker([amb.latitude, amb.longitude], { icon })
                .bindPopup(`
                    <strong>${amb.id}</strong><br>
                    ${amb.hospital}<br>
                    Status: ${amb.status}<br>
                    <button onclick="EmergencyCommand.openDispatch('${amb.id}', 'ambulance')" style="margin-top: 8px; padding: 6px 12px; background: #667eea; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        Dispatch
                    </button>
                `)
                .addTo(this.layers.ambulances);
        });
    },
    
    /**
     * Display police units
     */
    displayPolice(police) {
        if (this.clusterGroups.police) { this.clusterGroups.police.clearLayers(); }
        
        const listHtml = police.slice(0, 20).map(unit => {
            const statusClass = `status-${unit.status}`;
            return `
                <div class="resource-card">
                    <div class="resource-header">
                        <div class="resource-id">${unit.id}</div>
                        <span class="status-badge ${statusClass}">${unit.status}</span>
                    </div>
                    <div class="resource-details">
                        <div><i class="fas fa-building"></i> ${unit.name}</div>
                        <div><i class="fas fa-users"></i> ${unit.personnel} Personnel, ${unit.units} Units</div>
                        <div><i class="fas fa-map-marker-alt"></i> ${unit.city || 'Unknown'}</div>
                    </div>
                    <div class="resource-actions">
                        <button class="action-btn dispatch" onclick="EmergencyCommand.openDispatch('${unit.id}', 'police')">
                            <i class="fas fa-paper-plane"></i> Dispatch
                        </button>
                        <button class="action-btn track" onclick="EmergencyCommand.trackResource('${unit.id}', ${unit.latitude}, ${unit.longitude})">
                            <i class="fas fa-crosshairs"></i> Track
                        </button>
                    </div>
                </div>
            `;
        }).join('');
        
        document.getElementById('police-list').innerHTML = listHtml;
        
        // Add to map
        police.forEach(unit => {
            const icon = L.divIcon({
                html: '<div style="background: #3498db; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; border: 3px solid white; box-shadow: 0 2px 6px rgba(0,0,0,0.3);"><i class="fas fa-shield-alt"></i></div>',
                className: '',
                iconSize: [32, 32],
                iconAnchor: [16, 16]
            });
            
            L.marker([unit.latitude, unit.longitude], { icon })
                .bindPopup(`<strong>${unit.name}</strong><br>${unit.personnel} Personnel`)
                .addTo(this.clusterGroups.police);
        });
    },
    
    /**
     * Display NDRF teams
     */
    displayNDRF(teams) {
        this.layers.ndrf.clearLayers();
        
        const listHtml = teams.map(team => {
            const statusClass = `status-${team.status}`;
            return `
                <div class="resource-card">
                    <div class="resource-header">
                        <div class="resource-id">${team.id}</div>
                        <span class="status-badge ${statusClass}">${team.status}</span>
                    </div>
                    <div class="resource-details">
                        <div><i class="fas fa-building"></i> ${team.name}</div>
                        <div><i class="fas fa-users"></i> ${team.personnel} Personnel</div>
                        <div><i class="fas fa-toolbox"></i> ${team.equipment.join(', ')}</div>
                        <div><i class="fas fa-star"></i> Specialization: ${team.specialization}</div>
                    </div>
                    <div class="resource-actions">
                        <button class="action-btn dispatch" onclick="EmergencyCommand.openDispatch('${team.id}', 'ndrf')">
                            <i class="fas fa-paper-plane"></i> Deploy
                        </button>
                        <button class="action-btn track" onclick="EmergencyCommand.trackResource('${team.id}', ${team.latitude}, ${team.longitude})">
                            <i class="fas fa-crosshairs"></i> Track
                        </button>
                    </div>
                </div>
            `;
        }).join('');
        
        document.getElementById('ndrf-list').innerHTML = listHtml;
        
        // Add to map
        teams.forEach(team => {
            const icon = L.divIcon({
                html: '<div style="background: #f39c12; width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; border: 3px solid white; box-shadow: 0 2px 6px rgba(0,0,0,0.3);"><i class="fas fa-life-ring"></i></div>',
                className: '',
                iconSize: [34, 34],
                iconAnchor: [17, 17]
            });
            
            L.marker([team.latitude, team.longitude], { icon })
                .bindPopup(`<strong>${team.name}</strong><br>${team.personnel} Personnel<br>Specialization: ${team.specialization}`)
                .addTo(this.layers.ndrf);
        });
    },
    
    /**
     * Display relief equipment
     */
    displayRelief(relief) {
        this.layers.relief.clearLayers();
        
        const listHtml = relief.map(center => {
            return `
                <div class="resource-card">
                    <div class="resource-header">
                        <div class="resource-id">${center.id}</div>
                        <span class="status-badge status-available">${center.status}</span>
                    </div>
                    <div class="resource-details">
                        <div><i class="fas fa-warehouse"></i> ${center.name}</div>
                        <div><i class="fas fa-boxes"></i> Capacity: ${center.capacity}</div>
                        <div style="margin-top: 8px; padding: 8px; background: #f8f9fa; border-radius: 4px;">
                            <strong>Supplies:</strong>
                            <div style="font-size: 12px; margin-top: 4px;">
                                Medical: ${center.supplies.medical} | Food: ${center.supplies.food}<br>
                                Shelter: ${center.supplies.shelter} | Equipment: ${center.supplies.equipment}
                            </div>
                        </div>
                    </div>
                    <div class="resource-actions">
                        <button class="action-btn dispatch" onclick="EmergencyCommand.openDispatch('${center.id}', 'relief')">
                            <i class="fas fa-truck"></i> Deploy
                        </button>
                        <button class="action-btn track" onclick="EmergencyCommand.trackResource('${center.id}', ${center.latitude}, ${center.longitude})">
                            <i class="fas fa-crosshairs"></i> Track
                        </button>
                    </div>
                </div>
            `;
        }).join('');
        
        document.getElementById('relief-list').innerHTML = listHtml;
        
        // Add to map
        relief.forEach(center => {
            const icon = L.divIcon({
                html: '<div style="background: #16a085; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; border: 3px solid white; box-shadow: 0 2px 6px rgba(0,0,0,0.3);"><i class="fas fa-warehouse"></i></div>',
                className: '',
                iconSize: [32, 32],
                iconAnchor: [16, 16]
            });
            
            L.marker([center.latitude, center.longitude], { icon })
                .bindPopup(`<strong>${center.name}</strong><br>Capacity: ${center.capacity}`)
                .addTo(this.layers.relief);
        });
    },
    
    /**
     * Display hospitals
     */
    displayHospitals(hospitals) {
        if (this.clusterGroups.hospitals) { this.clusterGroups.hospitals.clearLayers(); }
        
        hospitals.forEach(hospital => {
            const icon = L.divIcon({
                html: '<div style="background: #e74c3c; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"><i class="fas fa-plus"></i></div>',
                className: '',
                iconSize: [24, 24],
                iconAnchor: [12, 12]
            });
            
            L.marker([hospital.latitude, hospital.longitude], { icon })
                .bindPopup(`<strong>${hospital.name}</strong><br>${hospital.district}, ${hospital.state}`)
                .addTo(this.clusterGroups.hospitals);
        });
    },
    
    /**
     * Display hotspots
     */
    displayHotspots(hotspots) {
        this.layers.hotspots.clearLayers();
        
        hotspots.forEach(hotspot => {
            const icon = L.divIcon({
                html: '<div style="background: #ff6b6b; width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"><i class="fas fa-exclamation"></i></div>',
                className: '',
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            });
            
            L.marker([hotspot.latitude, hotspot.longitude], { icon })
                .bindPopup(`<strong>${hotspot.name}</strong><br>Risk: ${hotspot.risk_level}`)
                .addTo(this.layers.hotspots);
        });
    },
    
    /**
     * Update ambulance stats
     */
    updateAmbulanceStats() {
        const available = this.data.ambulances.filter(a => a.status === 'available').length;
        const onDuty = this.data.ambulances.filter(a => a.status === 'on-duty').length;
        
        document.getElementById('ambulances-available').textContent = available;
        document.getElementById('ambulances-on-duty').textContent = onDuty;
    },
    
    /**
     * Update police stats
     */
    updatePoliceStats() {
        const available = this.data.police.filter(p => p.status === 'available').length;
        const deployed = this.data.police.filter(p => p.status === 'deployed').length;
        
        document.getElementById('police-available').textContent = available;
        document.getElementById('police-deployed').textContent = deployed;
    },
    
    /**
     * Update NDRF stats
     */
    updateNDRFStats() {
        const teams = this.data.ndrf.length;
        const personnel = this.data.ndrf.reduce((sum, team) => sum + team.personnel, 0);
        
        document.getElementById('ndrf-teams').textContent = teams;
        document.getElementById('ndrf-personnel').textContent = personnel;
    },
    
    /**
     * Update relief stats
     */
    updateReliefStats() {
        const warehouses = this.data.relief.filter(r => r.type === 'warehouse').length;
        const supplyPoints = this.data.relief.filter(r => r.type === 'supply_point').length;
        
        document.getElementById('relief-warehouses').textContent = warehouses;
        document.getElementById('relief-supplies').textContent = warehouses + supplyPoints;
    },
    
    /**
     * Filter ambulances
     */
    filterAmbulances() {
        const statusFilter = document.getElementById('ambulance-status-filter').value;
        const cityFilter = document.getElementById('ambulance-city-filter').value;
        
        let filtered = this.data.ambulances;
        
        if (statusFilter !== 'all') {
            filtered = filtered.filter(a => a.status === statusFilter);
        }
        
        if (cityFilter !== 'all') {
            filtered = filtered.filter(a => a.city === cityFilter);
        }
        
        this.displayAmbulances(filtered);
    },
    
    /**
     * Filter police
     */
    filterPolice() {
        const cityFilter = document.getElementById('police-city-filter').value;
        
        let filtered = this.data.police;
        
        if (cityFilter !== 'all') {
            filtered = filtered.filter(p => p.city === cityFilter);
        }
        
        this.displayPolice(filtered);
    },
    
    /**
     * Filter NDRF
     */
    filterNDRF() {
        const specFilter = document.getElementById('ndrf-specialization-filter').value;
        
        let filtered = this.data.ndrf;
        
        if (specFilter !== 'all') {
            filtered = filtered.filter(n => n.specialization === specFilter);
        }
        
        this.displayNDRF(filtered);
    },
    
    /**
     * Filter relief
     */
    filterRelief() {
        // Relief filtering can be added here if needed
        this.displayRelief(this.data.relief);
    },
    
    /**
     * Open dispatch modal
     */
    openDispatch(resourceId, resourceType) {
        this.selectedResource = { id: resourceId, type: resourceType };
        document.getElementById('dispatch-resource-id').value = resourceId;
        document.getElementById('dispatchModal').style.display = 'block';
    },
    
    /**
     * Close dispatch modal
     */
    closeDispatchModal() {
        document.getElementById('dispatchModal').style.display = 'none';
        document.getElementById('dispatchForm').reset();
        this.selectedResource = null;
    },
    
    /**
     * Handle dispatch
     */
    async handleDispatch() {
        const resourceId = document.getElementById('dispatch-resource-id').value;
        const dispatchType = document.getElementById('dispatch-type').value;
        const priority = document.getElementById('dispatch-priority').value;
        const lat = parseFloat(document.getElementById('dispatch-lat').value);
        const lng = parseFloat(document.getElementById('dispatch-lng').value);
        const notes = document.getElementById('dispatch-notes').value;
        
        // Simulate dispatch
        console.log('Dispatching:', {
            resourceId,
            dispatchType,
            priority,
            location: [lat, lng],
            notes
        });
        
        // Show success message
        alert(`✅ ${resourceId} dispatched successfully!\n\nType: ${dispatchType}\nPriority: ${priority}\nLocation: ${lat.toFixed(4)}, ${lng.toFixed(4)}`);
        
        // Close modal
        this.closeDispatchModal();
        
        // Update resource status (demo)
        if (this.selectedResource.type === 'ambulance') {
            const amb = this.data.ambulances.find(a => a.id === resourceId);
            if (amb) amb.status = 'on-duty';
            this.displayAmbulances(this.data.ambulances);
            this.updateAmbulanceStats();
        }
    },
    
    /**
     * Track resource on map
     */
    trackResource(resourceId, lat, lng) {
        this.map.setView([lat, lng], 15);
        
        // Flash the marker
        setTimeout(() => {
            alert(`📍 Tracking ${resourceId}\nLocation: ${lat.toFixed(4)}, ${lng.toFixed(4)}`);
        }, 500);
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    EmergencyCommand.init();
});

// Export for use in HTML
window.EmergencyCommand = EmergencyCommand;
