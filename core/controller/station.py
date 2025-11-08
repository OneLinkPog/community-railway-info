from typing import List, Dict, Any, Optional
from core.sql import sql
from core.logger import Logger

logger = Logger("@station_controller")


class StationController:
    """
    Controller for station-related business logic.
    Handles CRUD operations for railway stations using the database.
    """
    
    @staticmethod
    def get_all_stations() -> List[Dict[str, Any]]:
        """
        Get all stations from the database.
        
        Returns:
            List of station dictionaries
        """
        try:
            query = """
            SELECT id, name, alt_name, description, type, status, platform_count, symbol, image_path
            FROM station
            ORDER BY name
            """
            
            stations = sql.execute_query(query)
            
            return stations
        
        except Exception as e:
            logger.error(f"Error fetching stations from database: {str(e)}")
            return []
    
    @staticmethod
    def get_station_by_id(station_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a single station by its ID.
        
        Args:
            station_id: ID of the station
        
        Returns:
            Station dictionary or None if not found
        """
        try:
            station = sql.select_by_id('station', station_id)
            
            return station
        
        except Exception as e:
            logger.error(f"Error fetching station with ID {station_id}: {str(e)}")
            return None
    
    @staticmethod
    def get_station_by_name(station_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a single station by its name.
        
        Args:
            station_name: Name of the station
        
        Returns:
            Station dictionary or None if not found
        """
        try:
            station = sql.select_one('station', where={'name': station_name})
            
            return station
        
        except Exception as e:
            logger.error(f"Error fetching station '{station_name}': {str(e)}")
            return None
    
    @staticmethod
    def get_stations_by_line(line_name: str) -> List[Dict[str, Any]]:
        """
        Get all stations for a specific line, in order.
        
        Args:
            line_name: Name of the line
        
        Returns:
            List of station dictionaries in order
        """
        try:
            query = """
            SELECT s.id, s.name, s.alt_name, ls.station_order
            FROM station s
            JOIN line_station ls ON s.id = ls.station_id
            JOIN line l ON ls.line_id = l.id
            WHERE l.name = %s
            ORDER BY ls.station_order
            """
            
            stations = sql.execute_query(query, (line_name,))
            
            return stations
        
        except Exception as e:
            logger.error(f"Error fetching stations for line '{line_name}': {str(e)}")
            return []
    
    @staticmethod
    def get_lines_at_station(station_name: str) -> List[Dict[str, Any]]:
        """
        Get all lines that serve a specific station.
        
        Args:
            station_name: Name of the station
        
        Returns:
            List of line dictionaries
        """
        try:
            query = """
            SELECT l.id, l.name, l.color, l.status, l.type, o.name as operator_name, o.uid as operator_uid
            FROM line l
            JOIN line_station ls ON l.id = ls.line_id
            JOIN station s ON ls.station_id = s.id
            LEFT JOIN operator o ON l.operator_id = o.id
            WHERE s.name = %s
            ORDER BY l.name
            """
            
            lines = sql.execute_query(query, (station_name,))
            
            return lines
        
        except Exception as e:
            logger.error(f"Error fetching lines at station '{station_name}': {str(e)}")
            return []
    
    @staticmethod
    def create_station(station_name: str) -> Optional[int]:
        """
        Create a new station in the database.
        
        Args:
            station_name: Name of the station
        
        Returns:
            ID of created station or None on failure
        """
        try:
            # Check if station already exists
            existing = StationController.get_station_by_name(station_name)
            if existing:
                logger.warning(f"Station '{station_name}' already exists with ID {existing['id']}")
                return existing['id']
            
            station_id = sql.insert('station', {'name': station_name})
            
            if not station_id:
                logger.error(f"Failed to create station '{station_name}'")
            
            return station_id
        
        except Exception as e:
            logger.error(f"Error creating station '{station_name}': {str(e)}")
            return None
    
    @staticmethod
    def update_station(station_id: int, **kwargs) -> bool:
        """
        Update a station's properties.
        
        Args:
            station_id: ID of the station to update
            **kwargs: Station properties to update (name, alt_name, description, type, status, platform_count, symbol, image_path)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if station exists
            station = StationController.get_station_by_id(station_id)
            if not station:
                logger.error(f"Station with ID {station_id} not found")
                return False
            
            # Filter valid fields
            valid_fields = {'name', 'alt_name', 'description', 'type', 'status', 
                          'platform_count', 'symbol', 'image_path'}
            update_data = {k: v for k, v in kwargs.items() if k in valid_fields}
            
            if not update_data:
                logger.warning(f"No valid fields provided for station ID {station_id}")
                return False
            
            # Check if new name already exists (if name is being updated)
            if 'name' in update_data:
                existing = StationController.get_station_by_name(update_data['name'])
                if existing:
                    existing_id = int(existing['id'])
                    current_id = int(station_id)
                    logger.debug(f"Name check: existing ID {existing_id}, current ID {current_id}")
                    if existing_id != current_id:
                        logger.error(f"Station name '{update_data['name']}' already exists with ID {existing['id']}")
                        return False
                    else:
                        logger.debug(f"Name '{update_data['name']}' belongs to current station {station_id}, allowing update")
            
            # Convert platform_count to int if provided
            if 'platform_count' in update_data and update_data['platform_count']:
                try:
                    update_data['platform_count'] = int(update_data['platform_count'])
                except (ValueError, TypeError):
                    logger.warning(f"Invalid platform_count value: {update_data['platform_count']}, setting to None")
                    update_data['platform_count'] = None
            
            success = sql.update_by_id('station', station_id, update_data)
            
            if not success:
                logger.error(f"Failed to update station ID {station_id}")
            else:
                logger.info(f"Successfully updated station ID {station_id} with fields: {list(update_data.keys())}")
            
            return success
        
        except Exception as e:
            logger.error(f"Error updating station ID {station_id}: {str(e)}")
            return False
    
    @staticmethod
    def delete_station(station_id: int) -> bool:
        """
        Delete a station from the database.
        Warning: This will also remove all line-station associations.
        
        Args:
            station_id: ID of the station to delete
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if station exists
            station = StationController.get_station_by_id(station_id)
            if not station:
                logger.error(f"Station with ID {station_id} not found")
                return False
            
            # Check if station is used by any lines
            line_count = sql.count('line_station', {'station_id': station_id})
            if line_count > 0:
                logger.warning(f"Station ID {station_id} is used by {line_count} line(s)")
                # Delete line-station associations first
                sql.delete('line_station', {'station_id': station_id})
            
            # Delete the station
            success = sql.delete_by_id('station', station_id)
            
            if not success:
                logger.error(f"Failed to delete station ID {station_id}")
            
            return success
        
        except Exception as e:
            logger.error(f"Error deleting station ID {station_id}: {str(e)}")
            return False
    
    @staticmethod
    def add_station_to_line(line_name: str, station_name: str, order: int) -> bool:
        """
        Add a station to a line at a specific position.
        
        Args:
            line_name: Name of the line
            station_name: Name of the station
            order: Position of the station on the line (0-based)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get line ID
            line = sql.select_one('line', where={'name': line_name})
            if not line:
                logger.error(f"Line '{line_name}' not found")
                return False
            
            # Get or create station
            station = StationController.get_station_by_name(station_name)
            if not station:
                station_id = StationController.create_station(station_name)
                if not station_id:
                    logger.error(f"Failed to create station '{station_name}'")
                    return False
            else:
                station_id = station['id']
            
            # Check if association already exists
            existing = sql.execute_query("""
                SELECT * FROM line_station 
                WHERE line_id = %s AND station_id = %s
            """, (line['id'], station_id))
            
            if existing:
                logger.warning(f"Station '{station_name}' already exists on line '{line_name}'")
                # Update the order
                count = sql.update('line_station', 
                    {'station_order': order},
                    {'line_id': line['id'], 'station_id': station_id}
                )
                return count > 0
            
            # Add station to line
            result = sql.insert('line_station', {
                'line_id': line['id'],
                'station_id': station_id,
                'station_order': order
            })
            
            if result:
                return True
            else:
                logger.error(f"Failed to add station '{station_name}' to line '{line_name}'")
                return False
        
        except Exception as e:
            logger.error(f"Error adding station to line: {str(e)}")
            return False
    
    @staticmethod
    def remove_station_from_line(line_name: str, station_name: str) -> bool:
        """
        Remove a station from a line.
        
        Args:
            line_name: Name of the line
            station_name: Name of the station
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get line ID
            line = sql.select_one('line', where={'name': line_name})
            if not line:
                logger.error(f"Line '{line_name}' not found")
                return False
            
            # Get station ID
            station = StationController.get_station_by_name(station_name)
            if not station:
                logger.error(f"Station '{station_name}' not found")
                return False
            
            # Remove association
            count = sql.delete('line_station', {
                'line_id': line['id'],
                'station_id': station['id']
            })
            
            if count > 0:
                return True
            else:
                logger.warning(f"Station '{station_name}' was not on line '{line_name}'")
                return False
        
        except Exception as e:
            logger.error(f"Error removing station from line: {str(e)}")
            return False
    
    @staticmethod
    def reorder_stations_on_line(line_name: str, station_order: List[str]) -> bool:
        """
        Reorder stations on a line.
        
        Args:
            line_name: Name of the line
            station_order: List of station names in the desired order
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get line ID
            line = sql.select_one('line', where={'name': line_name})
            if not line:
                logger.error(f"Line '{line_name}' not found")
                return False
            
            # Update each station's order
            for order, station_name in enumerate(station_order):
                station = StationController.get_station_by_name(station_name)
                if not station:
                    logger.warning(f"Station '{station_name}' not found, skipping")
                    continue
                
                sql.update('line_station',
                    {'station_order': order},
                    {'line_id': line['id'], 'station_id': station['id']}
                )
            
            return True
        
        except Exception as e:
            logger.error(f"Error reordering stations on line '{line_name}': {str(e)}")
            return False
    
    @staticmethod
    def station_exists(station_name: str) -> bool:
        """
        Check if a station exists.
        
        Args:
            station_name: Name of the station
        
        Returns:
            True if station exists, False otherwise
        """
        return sql.exists('station', {'name': station_name})
    
    @staticmethod
    def count_stations() -> int:
        """
        Count total stations.
        
        Returns:
            Number of stations
        """
        try:
            return sql.count('station')
        except Exception as e:
            logger.error(f"Error counting stations: {str(e)}")
            return 0
    
    @staticmethod
    def search_stations(search_term: str) -> List[Dict[str, Any]]:
        """
        Search for stations by name (partial match).
        
        Args:
            search_term: Search term for station name
        
        Returns:
            List of matching station dictionaries
        """
        try:
            query = """
            SELECT id, name
            FROM station
            WHERE name LIKE %s
            ORDER BY name
            """
            
            stations = sql.execute_query(query, (f"%{search_term}%",))
            
            return stations
        
        except Exception as e:
            logger.error(f"Error searching stations: {str(e)}")
            return []
    
    @staticmethod
    def get_station_statistics(station_name: str) -> Dict[str, Any]:
        """
        Get statistics for a specific station.
        
        Args:
            station_name: Name of the station
        
        Returns:
            Dictionary with station statistics
        """
        try:
            station = StationController.get_station_by_name(station_name)
            if not station:
                logger.error(f"Station '{station_name}' not found")
                return {}
            
            lines = StationController.get_lines_at_station(station_name)
            
            # Count lines by type
            line_types = {}
            for line in lines:
                line_type = line.get('type', 'public')
                line_types[line_type] = line_types.get(line_type, 0) + 1
            
            # Count operators
            operators = set(line.get('operator_name') for line in lines if line.get('operator_name'))
            
            stats = {
                'station_name': station_name,
                'station_id': station['id'],
                'total_lines': len(lines),
                'lines_by_type': line_types,
                'operators_count': len(operators),
                'operators': list(operators),
                'lines': [{'name': line['name'], 'color': line.get('color')} for line in lines]
            }
            
            return stats
        
        except Exception as e:
            logger.error(f"Error generating statistics for station '{station_name}': {str(e)}")
            return {}
