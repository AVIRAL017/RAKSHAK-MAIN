"""
Incident Reporting Service
Handles incident reports and saves them to CSV file
"""

import os
import csv
import logging
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd

logger = logging.getLogger(__name__)

class IncidentService:
    def __init__(self):
        """Initialize the incident reporting service."""
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.incidents_file = os.path.join(self.base_dir, 'data', 'incident_reports.csv')
        self._ensure_incidents_file()
        logger.info("✅ Incident Service initialized")
    
    def _ensure_incidents_file(self):
        """Create incidents CSV file if it doesn't exist."""
        if not os.path.exists(self.incidents_file):
            # Create data directory if needed
            os.makedirs(os.path.dirname(self.incidents_file), exist_ok=True)
            
            # Create CSV with headers
            headers = [
                'incident_id', 'timestamp', 'latitude', 'longitude',
                'incident_type', 'severity', 'description', 
                'reporter_type', 'user_id', 'image_url',
                'status', 'verified', 'created_at'
            ]
            
            with open(self.incidents_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            
            logger.info(f"Created incidents file: {self.incidents_file}")
    
    def report_incident(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save incident report to CSV file.
        
        Args:
            incident_data: Dictionary containing incident details
            
        Returns:
            Dictionary with status and incident details
        """
        try:
            # Validate required fields
            required_fields = ['latitude', 'longitude', 'incident_type', 'severity']
            missing_fields = [field for field in required_fields if field not in incident_data]
            
            if missing_fields:
                return {
                    'status': 'error',
                    'message': f'Missing required fields: {", ".join(missing_fields)}'
                }
            
            # Validate coordinates
            lat = float(incident_data['latitude'])
            lng = float(incident_data['longitude'])
            
            if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                return {
                    'status': 'error',
                    'message': 'Invalid coordinates'
                }
            
            # Validate incident type
            valid_types = [
                'accident', 'road_hazard', 'construction', 'flooding',
                'poor_visibility', 'traffic_jam', 'vehicle_breakdown',
                'pedestrian_incident', 'animal_crossing', 'pothole',
                'debris', 'signal_malfunction', 'other'
            ]
            
            incident_type = incident_data['incident_type']
            if incident_type not in valid_types:
                return {
                    'status': 'error',
                    'message': f'Invalid incident type. Must be one of: {", ".join(valid_types)}'
                }
            
            # Validate severity
            valid_severities = ['low', 'medium', 'high', 'critical']
            severity = incident_data['severity']
            
            if severity not in valid_severities:
                return {
                    'status': 'error',
                    'message': f'Invalid severity. Must be one of: {", ".join(valid_severities)}'
                }
            
            # Generate incident ID
            timestamp = datetime.utcnow()
            incident_id = f"INC-{timestamp.strftime('%Y%m%d%H%M%S')}-{hash(str(lat) + str(lng)) % 10000:04d}"
            
            # Extract optional fields
            description = incident_data.get('description', '')
            reporter_type = incident_data.get('reporter_type', 'user')
            user_id = incident_data.get('user_id', '')
            image_url = incident_data.get('image_url', '')
            status = 'reported'
            verified = 1 if reporter_type == 'admin' else 0
            
            # Prepare row data
            row_data = [
                incident_id,
                timestamp.isoformat(),
                lat,
                lng,
                incident_type,
                severity,
                description,
                reporter_type,
                user_id,
                image_url,
                status,
                verified,
                timestamp.strftime('%Y-%m-%d %H:%M:%S')
            ]
            
            # Append to CSV file
            with open(self.incidents_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row_data)
            
            logger.info(f"Incident reported: {incident_id} at ({lat}, {lng}) - Type: {incident_type}, Severity: {severity}")
            
            return {
                'status': 'success',
                'message': 'Incident reported successfully',
                'data': {
                    'incident_id': incident_id,
                    'latitude': lat,
                    'longitude': lng,
                    'incident_type': incident_type,
                    'severity': severity,
                    'verified': verified == 1,
                    'created_at': timestamp.isoformat()
                }
            }
            
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            return {
                'status': 'error',
                'message': f'Invalid data format: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Incident reporting error: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to report incident: {str(e)}'
            }
    
    def get_incidents(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get reported incidents with optional filtering.
        
        Args:
            filters: Optional dictionary with filter criteria
            
        Returns:
            Dictionary with status and list of incidents
        """
        try:
            if not os.path.exists(self.incidents_file):
                return {
                    'status': 'success',
                    'data': {
                        'incidents': [],
                        'count': 0
                    }
                }
            
            # Read incidents from CSV
            df = pd.read_csv(self.incidents_file)
            
            if filters:
                # Apply status filter
                if 'status' in filters and filters['status']:
                    df = df[df['status'] == filters['status']]
                
                # Apply severity filter
                if 'severity' in filters and filters['severity']:
                    df = df[df['severity'] == filters['severity']]
                
                # Apply limit
                if 'limit' in filters and filters['limit']:
                    df = df.head(filters['limit'])
            
            # Convert to list of dictionaries
            incidents = df.to_dict('records')
            
            return {
                'status': 'success',
                'data': {
                    'incidents': incidents,
                    'count': len(incidents)
                }
            }
            
        except Exception as e:
            logger.error(f"Error retrieving incidents: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to retrieve incidents: {str(e)}'
            }
    
    def get_incident_by_id(self, incident_id: str) -> Dict[str, Any]:
        """
        Get a specific incident by ID.
        
        Args:
            incident_id: The incident ID to retrieve
            
        Returns:
            Dictionary with status and incident details
        """
        try:
            if not os.path.exists(self.incidents_file):
                return {
                    'status': 'error',
                    'message': 'Incident not found'
                }
            
            # Read incidents from CSV
            df = pd.read_csv(self.incidents_file)
            incident = df[df['incident_id'] == incident_id]
            
            if incident.empty:
                return {
                    'status': 'error',
                    'message': 'Incident not found'
                }
            
            return {
                'status': 'success',
                'data': incident.iloc[0].to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error retrieving incident: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to retrieve incident: {str(e)}'
            }
    
    def update_incident_status(self, incident_id: str, new_status: str) -> Dict[str, Any]:
        """
        Update the status of an incident.
        
        Args:
            incident_id: The incident ID to update
            new_status: The new status ('reported', 'verified', 'resolved')
            
        Returns:
            Dictionary with status and update result
        """
        try:
            valid_statuses = ['reported', 'verified', 'resolved']
            if new_status not in valid_statuses:
                return {
                    'status': 'error',
                    'message': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
                }
            
            if not os.path.exists(self.incidents_file):
                return {
                    'status': 'error',
                    'message': 'Incident not found'
                }
            
            # Read and update CSV
            df = pd.read_csv(self.incidents_file)
            
            if incident_id not in df['incident_id'].values:
                return {
                    'status': 'error',
                    'message': 'Incident not found'
                }
            
            df.loc[df['incident_id'] == incident_id, 'status'] = new_status
            df.to_csv(self.incidents_file, index=False)
            
            logger.info(f"Updated incident {incident_id} status to {new_status}")
            
            return {
                'status': 'success',
                'message': 'Incident status updated successfully'
            }
            
        except Exception as e:
            logger.error(f"Error updating incident: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to update incident: {str(e)}'
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about reported incidents.
        
        Returns:
            Dictionary with incident statistics
        """
        try:
            if not os.path.exists(self.incidents_file):
                return {
                    'status': 'success',
                    'data': {
                        'total': 0,
                        'by_severity': {},
                        'by_type': {},
                        'by_status': {}
                    }
                }
            
            df = pd.read_csv(self.incidents_file)
            
            stats = {
                'total': len(df),
                'by_severity': df['severity'].value_counts().to_dict(),
                'by_type': df['incident_type'].value_counts().to_dict(),
                'by_status': df['status'].value_counts().to_dict(),
                'verified': int(df['verified'].sum()),
                'unverified': int((df['verified'] == 0).sum())
            }
            
            return {
                'status': 'success',
                'data': stats
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to get statistics: {str(e)}'
            }

# Create singleton instance
incident_service = IncidentService()
