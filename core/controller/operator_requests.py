from typing import List, Dict, Any, Optional
from datetime import datetime
from core.sql import sql
from core.logger import Logger
import json

logger = Logger("@operator_requests_controller")


class OperatorRequestController:
    """
    Controller for operator request management.
    Handles CRUD operations for operator requests using the database.
    """
    
    @staticmethod
    def get_all_requests() -> List[Dict[str, Any]]:
        """
        Get all operator requests from the database.
        
        Returns:
            List of request dictionaries
        """
        try:
            query = """
            SELECT 
                id,
                timestamp,
                status,
                requester_id,
                requester_username,
                company_name,
                short_code,
                color,
                additional_users,
                company_uid
            FROM operator_request
            ORDER BY timestamp DESC
            """
            
            results = sql.execute_query(query)
            
            requests = []
            for row in results:
                request = {
                    'id': row['id'],
                    'timestamp': row['timestamp'].isoformat() if isinstance(row['timestamp'], datetime) else row['timestamp'],
                    'status': row['status'],
                    'requester': {
                        'id': str(row['requester_id']),
                        'username': row['requester_username']
                    },
                    'company_name': row['company_name'],
                    'short_code': row['short_code'],
                    'color': row['color'],
                    'additional_users': json.loads(row['additional_users']) if row['additional_users'] else [],
                    'company_uid': row['company_uid']
                }
                requests.append(request)
            
            logger.debug(f"Retrieved {len(requests)} operator requests from database")
            return requests
        
        except Exception as e:
            logger.error(f"Error fetching operator requests: {str(e)}")
            return []
    
    @staticmethod
    def get_request_by_timestamp(timestamp: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific operator request by timestamp.
        
        Args:
            timestamp: ISO format timestamp string
        
        Returns:
            Request dictionary or None if not found
        """
        try:
            query = """
            SELECT 
                id,
                timestamp,
                status,
                requester_id,
                requester_username,
                company_name,
                short_code,
                color,
                additional_users,
                company_uid
            FROM operator_request
            WHERE timestamp = %s
            """
            
            results = sql.execute_query(query, (timestamp,))
            
            if not results:
                logger.debug(f"Request with timestamp {timestamp} not found")
                return None
            
            row = results[0]
            request = {
                'id': row['id'],
                'timestamp': row['timestamp'].isoformat() if isinstance(row['timestamp'], datetime) else row['timestamp'],
                'status': row['status'],
                'requester': {
                    'id': str(row['requester_id']),
                    'username': row['requester_username']
                },
                'company_name': row['company_name'],
                'short_code': row['short_code'],
                'color': row['color'],
                'additional_users': json.loads(row['additional_users']) if row['additional_users'] else [],
                'company_uid': row['company_uid']
            }
            
            logger.debug(f"Found request with timestamp {timestamp}")
            return request
        
        except Exception as e:
            logger.error(f"Error fetching request by timestamp: {str(e)}")
            return None
    
    @staticmethod
    def get_request_by_id(request_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific operator request by ID.
        
        Args:
            request_id: ID of the request
        
        Returns:
            Request dictionary or None if not found
        """
        try:
            request = sql.select_by_id('operator_request', request_id)
            
            if not request:
                logger.debug(f"Request with ID {request_id} not found")
                return None
            
            formatted_request = {
                'id': request['id'],
                'timestamp': request['timestamp'].isoformat() if isinstance(request['timestamp'], datetime) else request['timestamp'],
                'status': request['status'],
                'requester': {
                    'id': str(request['requester_id']),
                    'username': request['requester_username']
                },
                'company_name': request['company_name'],
                'short_code': request['short_code'],
                'color': request['color'],
                'additional_users': json.loads(request['additional_users']) if request['additional_users'] else [],
                'company_uid': request['company_uid']
            }
            
            logger.debug(f"Found request with ID {request_id}")
            return formatted_request
        
        except Exception as e:
            logger.error(f"Error fetching request by ID: {str(e)}")
            return None
    
    @staticmethod
    def get_pending_requests() -> List[Dict[str, Any]]:
        """
        Get all pending operator requests.
        
        Returns:
            List of pending request dictionaries
        """
        try:
            query = """
            SELECT 
                id,
                timestamp,
                status,
                requester_id,
                requester_username,
                company_name,
                short_code,
                color,
                additional_users,
                company_uid
            FROM operator_request
            WHERE status = 'pending'
            ORDER BY timestamp DESC
            """
            
            results = sql.execute_query(query)
            
            requests = []
            for row in results:
                request = {
                    'id': row['id'],
                    'timestamp': row['timestamp'].isoformat() if isinstance(row['timestamp'], datetime) else row['timestamp'],
                    'status': row['status'],
                    'requester': {
                        'id': str(row['requester_id']),
                        'username': row['requester_username']
                    },
                    'company_name': row['company_name'],
                    'short_code': row['short_code'],
                    'color': row['color'],
                    'additional_users': json.loads(row['additional_users']) if row['additional_users'] else [],
                    'company_uid': row['company_uid']
                }
                requests.append(request)
            
            logger.debug(f"Retrieved {len(requests)} pending operator requests from database")
            return requests
        
        except Exception as e:
            logger.error(f"Error fetching pending requests: {str(e)}")
            return []
    
    @staticmethod
    def create_request(request_data: Dict[str, Any]) -> Optional[int]:
        """
        Create a new operator request in the database.
        
        Args:
            request_data: Dictionary containing request information
                Required: requester (dict with id and username), company_name, 
                         short_code, color, additional_users, company_uid
        
        Returns:
            ID of created request or None on failure
        """
        try:
            user_id = request_data['requester']['id']
            user = sql.select_one('user', where={'id': str(user_id)})
            if not user:
                sql.insert('user', {'id': str(user_id)})
            
            insert_data = {
                'timestamp': datetime.now(),
                'status': 'pending',
                'requester_id': str(request_data['requester']['id']),
                'requester_username': request_data['requester']['username'],
                'company_name': request_data['company_name'],
                'short_code': request_data['short_code'],
                'color': request_data['color'],
                'additional_users': json.dumps(request_data['additional_users']),
                'company_uid': request_data['company_uid']
            }
            
            request_id = sql.insert('operator_request', insert_data)
            
            if request_id:
                logger.info(f"Created operator request for '{request_data['company_name']}' by user {request_data['requester']['username']}")
            else:
                logger.error(f"Failed to create operator request for '{request_data['company_name']}'")
            
            return request_id
        
        except Exception as e:
            logger.error(f"Error creating operator request: {str(e)}")
            return None
    
    @staticmethod
    def update_request_status(timestamp: str, status: str) -> bool:
        """
        Update the status of an operator request.
        
        Args:
            timestamp: ISO format timestamp of the request
            status: New status ('pending', 'accepted', 'rejected')
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if status not in ['pending', 'accepted', 'rejected']:
                logger.error(f"Invalid status: {status}")
                return False
            
            query = "UPDATE operator_request SET status = %s WHERE timestamp = %s"
            result = sql.execute_update(query, (status, timestamp))
            
            if result:
                logger.info(f"Updated request status to '{status}' for timestamp {timestamp}")
            else:
                logger.error(f"Request with timestamp {timestamp} not found or update failed")
            
            return result
        
        except Exception as e:
            logger.error(f"Error updating request status: {str(e)}")
            return False
    
    @staticmethod
    def delete_request(timestamp: str) -> bool:
        """
        Delete an operator request by timestamp.
        
        Args:
            timestamp: ISO format timestamp of the request
        
        Returns:
            True if successful, False otherwise
        """
        try:
            query = "DELETE FROM operator_request WHERE timestamp = %s"
            count = sql.execute_update(query, (timestamp,))
            
            if count > 0:
                logger.info(f"Deleted operator request with timestamp {timestamp}")
                return True
            else:
                logger.warning(f"Request with timestamp {timestamp} not found")
                return False
        
        except Exception as e:
            logger.error(f"Error deleting operator request: {str(e)}")
            return False
    
    @staticmethod
    def delete_request_by_id(request_id: int) -> bool:
        """
        Delete an operator request by ID.
        
        Args:
            request_id: ID of the request
        
        Returns:
            True if successful, False otherwise
        """
        try:
            success = sql.delete_by_id('operator_request', request_id)
            
            if success:
                logger.info(f"Deleted operator request with ID {request_id}")
            else:
                logger.warning(f"Request with ID {request_id} not found")
            
            return success
        
        except Exception as e:
            logger.error(f"Error deleting operator request: {str(e)}")
            return False
    
    @staticmethod
    def count_requests(status: Optional[str] = None) -> int:
        """
        Count operator requests, optionally filtered by status.
        
        Args:
            status: Optional status to filter by ('pending', 'accepted', 'rejected')
        
        Returns:
            Number of requests
        """
        try:
            if status:
                return sql.count('operator_request', {'status': status})
            else:
                return sql.count('operator_request')
        except Exception as e:
            logger.error(f"Error counting requests: {str(e)}")
            return 0

