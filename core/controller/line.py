from typing import List, Dict, Any, Optional
from core.sql import sql
from core.logger import Logger

logger = Logger("@line_controller")


class LineController:
    """
    Controller for line-related business logic.
    Handles CRUD operations for railway lines using the database.
    """
    
    @staticmethod
    def get_all_lines() -> List[Dict[str, Any]]:
        """
        Get all lines from the database with their stations and compositions.
        Falls back to JSON file if database query fails.
        OPTIMIZED: Uses only 2 queries instead of N+1
        
        Returns:
            List of line dictionaries
        """
        try:
            # Query 1: Get all lines with stations in ONE query
            query = """
            SELECT 
                l.id,
                l.name,
                l.color,
                l.status,
                l.type,
                l.notice,
                o.name as operator_name,
                o.uid as operator_uid,
                GROUP_CONCAT(DISTINCT s.name ORDER BY ls.station_order SEPARATOR '||') as stations
            FROM line l
            LEFT JOIN operator o ON l.operator_id = o.id
            LEFT JOIN line_station ls ON l.id = ls.line_id
            LEFT JOIN station s ON ls.station_id = s.id
            GROUP BY l.id, l.name, l.color, l.status, l.type, l.notice, o.name, o.uid
            ORDER BY l.name
            """
            
            results = sql.execute_query(query)
            
            # Query 2: Get ALL compositions for ALL lines in ONE query
            comp_query = """
            SELECT 
                lc.line_id,
                c.parts, 
                c.name as comp_name
            FROM line_composition lc
            JOIN composition c ON lc.composition_id = c.id
            ORDER BY lc.line_id, c.id
            """
            all_compositions = sql.execute_query(comp_query)
            
            # Build composition map: {line_id: [compositions]}
            comp_map = {}
            for comp in all_compositions:
                line_id = comp['line_id']
                if line_id not in comp_map:
                    comp_map[line_id] = []
                comp_map[line_id].append({
                    'name': comp['comp_name'] or '',
                    'parts': comp['parts']
                })
            
            # Build final lines list
            lines = []
            for row in results:
                line = {
                    'name': row['name'],
                    'color': row['color'],
                    'status': row['status'] or 'Running',
                    'type': row['type'] or 'public',
                    'notice': row['notice'] or '',
                    'stations': row['stations'].split('||') if row['stations'] else [],
                    'compositions': comp_map.get(row['id'], []),
                    'operator': row['operator_name'] or '',
                    'operator_uid': row['operator_uid'] or ''
                }
                lines.append(line)
            
            logger.debug(f"Retrieved {len(lines)} lines from database (optimized: 2 queries)")
            return lines
        
        except Exception as e:
            logger.error(f"Error fetching lines from database: {str(e)}")
    
    @staticmethod
    def get_line_by_name(line_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a single line by its name.
        
        Args:
            line_name: Name of the line
        
        Returns:
            Line dictionary or None if not found
        """
        try:
            query = """
            SELECT 
                l.id,
                l.name,
                l.color,
                l.status,
                l.type,
                l.notice,
                o.name as operator_name,
                o.uid as operator_uid,
                GROUP_CONCAT(DISTINCT s.name ORDER BY ls.station_order SEPARATOR '||') as stations
            FROM line l
            LEFT JOIN operator o ON l.operator_id = o.id
            LEFT JOIN line_station ls ON l.id = ls.line_id
            LEFT JOIN station s ON ls.station_id = s.id
            WHERE l.name = %s
            GROUP BY l.id, l.name, l.color, l.status, l.type, l.notice, o.name, o.uid
            """
            
            results = sql.execute_query(query, (line_name,))
            
            if not results:
                logger.debug(f"Line '{line_name}' not found in database")
                return None
            
            row = results[0]
            
            # Get compositions
            comp_query = """
            SELECT c.parts, c.name as comp_name
            FROM line_composition lc
            JOIN composition c ON lc.composition_id = c.id
            WHERE lc.line_id = %s
            ORDER BY c.id
            """
            compositions_raw = sql.execute_query(comp_query, (row['id'],))
            
            compositions = []
            for comp in compositions_raw:
                compositions.append({
                    'name': comp['comp_name'] or '',
                    'parts': comp['parts']
                })
            
            line = {
                'id': row['id'],
                'name': row['name'],
                'color': row['color'],
                'status': row['status'] or 'Running',
                'type': row['type'] or 'public',
                'notice': row['notice'] or '',
                'stations': row['stations'].split('||') if row['stations'] else [],
                'compositions': compositions,
                'operator': row['operator_name'] or '',
                'operator_uid': row['operator_uid'] or ''
            }
            
            logger.debug(f"Retrieved line '{line_name}' from database")
            return line
        
        except Exception as e:
            logger.error(f"Error fetching line '{line_name}': {str(e)}")
            return None
    
    @staticmethod
    def get_lines_by_operator(operator_uid: str) -> List[Dict[str, Any]]:
        """
        Get all lines for a specific operator.
        
        Args:
            operator_uid: UID of the operator
        
        Returns:
            List of line dictionaries
        """
        try:
            query = """
            SELECT 
                l.id,
                l.name,
                l.color,
                l.status,
                l.type,
                l.notice,
                o.name as operator_name,
                o.uid as operator_uid,
                GROUP_CONCAT(DISTINCT s.name ORDER BY ls.station_order SEPARATOR '||') as stations
            FROM line l
            LEFT JOIN operator o ON l.operator_id = o.id
            LEFT JOIN line_station ls ON l.id = ls.line_id
            LEFT JOIN station s ON ls.station_id = s.id
            WHERE o.uid = %s
            GROUP BY l.id, l.name, l.color, l.status, l.type, l.notice, o.name, o.uid
            ORDER BY l.name
            """
            
            results = sql.execute_query(query, (operator_uid,))
            
            lines = []
            for row in results:
                comp_query = """
                SELECT c.parts, c.name as comp_name
                FROM line_composition lc
                JOIN composition c ON lc.composition_id = c.id
                WHERE lc.line_id = %s
                ORDER BY c.id
                """
                compositions_raw = sql.execute_query(comp_query, (row['id'],))
                
                compositions = []
                for comp in compositions_raw:
                    compositions.append({
                        'name': comp['comp_name'] or '',
                        'parts': comp['parts']
                    })
                
                line = {
                    'name': row['name'],
                    'color': row['color'],
                    'status': row['status'] or 'Running',
                    'type': row['type'] or 'public',
                    'notice': row['notice'] or '',
                    'stations': row['stations'].split('||') if row['stations'] else [],
                    'compositions': compositions,
                    'operator': row['operator_name'] or '',
                    'operator_uid': row['operator_uid'] or ''
                }
                lines.append(line)
            
            logger.debug(f"Retrieved {len(lines)} lines for operator '{operator_uid}'")
            return lines
        
        except Exception as e:
            logger.error(f"Error fetching lines for operator '{operator_uid}': {str(e)}")
            return []
    
    @staticmethod
    def create_line(line_data: Dict[str, Any]) -> Optional[int]:
        """
        Create a new line in the database.
        
        Args:
            line_data: Dictionary containing line information
                Required: name, color, status, type, operator_uid
                Optional: notice, stations (list), compositions (list)
        
        Returns:
            ID of created line or None on failure
        """
        try:
            # Get operator ID from UID
            operator = sql.select_one('operator', where={'uid': line_data['operator_uid']})
            if not operator:
                logger.error(f"Operator with UID '{line_data['operator_uid']}' not found")
                return None
            
            # Insert line
            line_insert_data = {
                'name': line_data['name'],
                'color': line_data['color'],
                'status': line_data.get('status', 'Running'),
                'type': line_data.get('type', 'public'),
                'notice': line_data.get('notice', ''),
                'operator_id': operator['id']
            }
            
            line_id = sql.insert('line', line_insert_data)
            if not line_id:
                logger.error("Failed to insert line")
                return None
            
            # Insert stations if provided
            if 'stations' in line_data and line_data['stations']:
                for order, station_name in enumerate(line_data['stations']):
                    # Get or create station
                    station = sql.select_one('station', where={'name': station_name})
                    if not station:
                        station_id = sql.insert('station', {'name': station_name})
                    else:
                        station_id = station['id']
                    
                    # Link station to line
                    sql.insert('line_station', {
                        'line_id': line_id,
                        'station_id': station_id,
                        'station_order': order
                    })
            
            # Insert compositions if provided
            if 'compositions' in line_data and line_data['compositions']:
                for comp in line_data['compositions']:
                    if isinstance(comp, dict):
                        # New format: {name: '', parts: ''}
                        comp_name = comp.get('name', '')
                        comp_parts = comp.get('parts', '')
                    else:
                        # Old format: just the parts string
                        comp_name = ''
                        comp_parts = comp
                    
                    # Get or create composition
                    composition = sql.select_one('composition', where={
                        'parts': comp_parts,
                        'name': comp_name
                    })
                    if not composition:
                        composition_id = sql.insert('composition', {
                            'parts': comp_parts,
                            'name': comp_name
                        })
                    else:
                        composition_id = composition['id']
                    
                    # Link composition to line
                    sql.insert('line_composition', {
                        'line_id': line_id,
                        'composition_id': composition_id
                    })
            
            logger.info(f"Created line '{line_data['name']}' with ID {line_id}")
            return line_id
        
        except Exception as e:
            logger.error(f"Error creating line: {str(e)}")
            return None
    
    @staticmethod
    def update_line(line_name: str, line_data: Dict[str, Any]) -> bool:
        """
        Update an existing line.
        
        Args:
            line_name: Name of the line to update
            line_data: Dictionary with updated line information
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get line
            line = LineController.get_line_by_name(line_name)
            if not line:
                logger.error(f"Line '{line_name}' not found")
                return False
            
            line_id = line['id']
            
            # Update basic line info
            update_data = {}
            if 'name' in line_data:
                update_data['name'] = line_data['name']
            if 'color' in line_data:
                update_data['color'] = line_data['color']
            if 'status' in line_data:
                update_data['status'] = line_data['status']
            if 'type' in line_data:
                update_data['type'] = line_data['type']
            if 'notice' in line_data:
                update_data['notice'] = line_data['notice']
            
            if update_data:
                sql.update('line', update_data, {'id': line_id})
            
            # Update stations if provided
            if 'stations' in line_data:
                # Remove old stations
                sql.delete('line_station', {'line_id': line_id})
                
                # Add new stations
                for order, station_name in enumerate(line_data['stations']):
                    station = sql.select_one('station', where={'name': station_name})
                    if not station:
                        station_id = sql.insert('station', {'name': station_name})
                    else:
                        station_id = station['id']
                    
                    sql.insert('line_station', {
                        'line_id': line_id,
                        'station_id': station_id,
                        'station_order': order
                    })
            
            # Update compositions if provided
            if 'compositions' in line_data:
                # Remove old compositions
                sql.delete('line_composition', {'line_id': line_id})
                
                # Add new compositions
                for comp in line_data['compositions']:
                    if isinstance(comp, dict):
                        comp_name = comp.get('name', '')
                        comp_parts = comp.get('parts', '')
                    else:
                        comp_name = ''
                        comp_parts = comp
                    
                    composition = sql.select_one('composition', where={
                        'parts': comp_parts,
                        'name': comp_name
                    })
                    if not composition:
                        composition_id = sql.insert('composition', {
                            'parts': comp_parts,
                            'name': comp_name
                        })
                    else:
                        composition_id = composition['id']
                    
                    sql.insert('line_composition', {
                        'line_id': line_id,
                        'composition_id': composition_id
                    })
            
            logger.info(f"Updated line '{line_name}'")
            return True
        
        except Exception as e:
            logger.error(f"Error updating line '{line_name}': {str(e)}")
            return False
    
    @staticmethod
    def delete_line(line_name: str) -> bool:
        """
        Delete a line from the database.
        
        Args:
            line_name: Name of the line to delete
        
        Returns:
            True if successful, False otherwise
        """
        try:
            line = LineController.get_line_by_name(line_name)
            if not line:
                logger.error(f"Line '{line_name}' not found")
                return False
            
            line_id = line['id']
            
            # Delete related records (cascading delete)
            sql.delete('line_station', {'line_id': line_id})
            sql.delete('line_composition', {'line_id': line_id})
            
            # Delete the line itself
            success = sql.delete_by_id('line', line_id)
            
            if success:
                logger.info(f"Deleted line '{line_name}'")
            else:
                logger.error(f"Failed to delete line '{line_name}'")
            
            return success
        
        except Exception as e:
            logger.error(f"Error deleting line '{line_name}': {str(e)}")
            return False
    
    @staticmethod
    def line_exists(line_name: str) -> bool:
        """
        Check if a line exists.
        
        Args:
            line_name: Name of the line
        
        Returns:
            True if line exists, False otherwise
        """
        return sql.exists('line', {'name': line_name})
    
    @staticmethod
    def count_lines(operator_uid: Optional[str] = None) -> int:
        """
        Count total lines, optionally filtered by operator.
        
        Args:
            operator_uid: Optional operator UID to filter by
        
        Returns:
            Number of lines
        """
        try:
            if operator_uid:
                operator = sql.select_one('operator', where={'uid': operator_uid})
                if not operator:
                    return 0
                return sql.count('line', {'operator_id': operator['id']})
            else:
                return sql.count('line')
        except Exception as e:
            logger.error(f"Error counting lines: {str(e)}")
            return 0
