from typing import List, Dict, Any, Optional
from core.sql import sql
from core.logger import Logger
from core import main_dir
import json

logger = Logger("@operator_controller")


class OperatorController:
    """
    Controller for operator-related business logic.
    Handles CRUD operations for railway operators using the database.
    """
    
    @staticmethod
    def get_all_operators() -> List[Dict[str, Any]]:
        """
        Get all operators from the database with their users.
        Falls back to JSON file if database query fails.
        
        Returns:
            List of operator dictionaries
        """
        try:
            operators_query = """
            SELECT o.id, o.name, o.color, o.short, o.uid
            FROM operator o
            ORDER BY o.name
            """
            operators_raw = sql.execute_query(operators_query)
            
            operators = []
            for op in operators_raw:
                users_query = """
                SELECT u.id
                FROM operator_user ou
                JOIN user u ON ou.user_id = u.id
                WHERE ou.operator_id = %s
                """
                users_raw = sql.execute_query(users_query, (op['id'],))
                
                operator = {
                    'name': op['name'],
                    'color': op['color'] or '#808080',
                    'users': [str(user['id']) for user in users_raw],
                    'short': op['short'] or '',
                    'uid': op['uid']
                }
                operators.append(operator)
            
            logger.debug(f"Retrieved {len(operators)} operators from database")
            return operators
        
        except Exception as e:
            logger.error(f"Error fetching operators from database: {str(e)}")
    
    @staticmethod
    def get_operator_by_uid(operator_uid: str) -> Optional[Dict[str, Any]]:
        """
        Get a single operator by its UID.
        
        Args:
            operator_uid: UID of the operator
        
        Returns:
            Operator dictionary or None if not found
        """
        try:
            operator_query = """
            SELECT o.id, o.name, o.color, o.short, o.uid
            FROM operator o
            WHERE o.uid = %s
            """
            operators_raw = sql.execute_query(operator_query, (operator_uid,))
            
            if not operators_raw:
                logger.debug(f"Operator '{operator_uid}' not found in database")
                return None
            
            op = operators_raw[0]
            
            # Get users for this operator
            users_query = """
            SELECT u.id
            FROM operator_user ou
            JOIN user u ON ou.user_id = u.id
            WHERE ou.operator_id = %s
            """
            users_raw = sql.execute_query(users_query, (op['id'],))
            
            operator = {
                'id': op['id'],
                'name': op['name'],
                'color': op['color'] or '#808080',
                'users': [str(user['id']) for user in users_raw],
                'short': op['short'] or '',
                'uid': op['uid']
            }
            
            logger.debug(f"Retrieved operator '{operator_uid}' from database")
            return operator
        
        except Exception as e:
            logger.error(f"Error fetching operator '{operator_uid}': {str(e)}")
            return None
    
    @staticmethod
    def get_operator_by_name(operator_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a single operator by its name.
        
        Args:
            operator_name: Name of the operator
        
        Returns:
            Operator dictionary or None if not found
        """
        try:
            operator_query = """
            SELECT o.id, o.name, o.color, o.short, o.uid
            FROM operator o
            WHERE o.name = %s
            """
            operators_raw = sql.execute_query(operator_query, (operator_name,))
            
            if not operators_raw:
                logger.debug(f"Operator '{operator_name}' not found in database")
                return None
            
            op = operators_raw[0]
            
            # Get users for this operator
            users_query = """
            SELECT u.id
            FROM operator_user ou
            JOIN user u ON ou.user_id = u.id
            WHERE ou.operator_id = %s
            """
            users_raw = sql.execute_query(users_query, (op['id'],))
            
            operator = {
                'id': op['id'],
                'name': op['name'],
                'color': op['color'] or '#808080',
                'users': [str(user['id']) for user in users_raw],
                'short': op['short'] or '',
                'uid': op['uid']
            }
            
            logger.debug(f"Retrieved operator '{operator_name}' from database")
            return operator
        
        except Exception as e:
            logger.error(f"Error fetching operator '{operator_name}': {str(e)}")
            return None
    
    @staticmethod
    def get_operators_by_user(user_id: str) -> List[Dict[str, Any]]:
        """
        Get all operators that a specific user belongs to.
        
        Args:
            user_id: Discord ID of the user
        
        Returns:
            List of operator dictionaries
        """
        try:
            operators_query = """
            SELECT DISTINCT o.id, o.name, o.color, o.short, o.uid
            FROM operator o
            JOIN operator_user ou ON o.id = ou.operator_id
            JOIN user u ON ou.user_id = u.id
            WHERE u.id = %s
            ORDER BY o.name
            """
            operators_raw = sql.execute_query(operators_query, (user_id,))
            
            operators = []
            for op in operators_raw:
                # Get all users for this operator
                users_query = """
                SELECT u.id
                FROM operator_user ou
                JOIN user u ON ou.user_id = u.id
                WHERE ou.operator_id = %s
                """
                users_raw = sql.execute_query(users_query, (op['id'],))
                
                operator = {
                    'name': op['name'],
                    'color': op['color'] or '#808080',
                    'users': [str(user['id']) for user in users_raw],
                    'short': op['short'] or '',
                    'uid': op['uid']
                }
                operators.append(operator)
            
            logger.debug(f"Retrieved {len(operators)} operators for user '{user_id}'")
            return operators
        
        except Exception as e:
            logger.error(f"Error fetching operators for user '{user_id}': {str(e)}")
            return []
    
    @staticmethod
    def create_operator(operator_data: Dict[str, Any]) -> Optional[int]:
        """
        Create a new operator in the database.
        
        Args:
            operator_data: Dictionary containing operator information
                Required: name, uid
                Optional: color, short, users (list of user IDs)
        
        Returns:
            ID of created operator or None on failure
        """
        try:
            # Insert operator
            operator_insert_data = {
                'name': operator_data['name'],
                'uid': operator_data['uid'],
                'color': operator_data.get('color', '#808080'),
                'short': operator_data.get('short', '')
            }
            
            operator_id = sql.insert('operator', operator_insert_data)
            if not operator_id:
                logger.error("Failed to insert operator")
                return None
            
            # Add users if provided
            if 'users' in operator_data and operator_data['users']:
                for user_id in operator_data['users']:
                    # Get or create user
                    user = sql.select_one('user', where={'id': str(user_id)})
                    if not user:
                        # Create user entry
                        user_insert_id = sql.insert('user', {'id': str(user_id)})
                        if not user_insert_id:
                            logger.warning(f"Could not create user entry for {user_id}")
                            continue
                    
                    # Link user to operator
                    sql.insert('operator_user', {
                        'operator_id': operator_id,
                        'user_id': str(user_id)
                    })
            
            logger.info(f"Created operator '{operator_data['name']}' with ID {operator_id}")
            return operator_id
        
        except Exception as e:
            logger.error(f"Error creating operator: {str(e)}")
            return None
    
    @staticmethod
    def update_operator(operator_uid: str, operator_data: Dict[str, Any]) -> bool:
        """
        Update an existing operator.
        
        Args:
            operator_uid: UID of the operator to update
            operator_data: Dictionary with updated operator information
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get operator
            operator = OperatorController.get_operator_by_uid(operator_uid)
            if not operator:
                logger.error(f"Operator '{operator_uid}' not found")
                return False
            
            operator_id = operator['id']
            
            # Update basic operator info
            update_data = {}
            if 'name' in operator_data:
                update_data['name'] = operator_data['name']
            if 'color' in operator_data:
                update_data['color'] = operator_data['color']
            if 'short' in operator_data:
                update_data['short'] = operator_data['short']
            
            if update_data:
                sql.update('operator', update_data, {'id': operator_id})
            
            # Update users if provided
            if 'users' in operator_data:
                # Remove old user associations
                sql.delete('operator_user', {'operator_id': operator_id})
                
                # Add new user associations
                for user_id in operator_data['users']:
                    # Get or create user
                    user = sql.select_one('user', where={'id': str(user_id)})
                    if not user:
                        user_insert_id = sql.insert('user', {'id': str(user_id)})
                        if not user_insert_id:
                            logger.warning(f"Could not create user entry for {user_id}")
                            continue
                    
                    sql.insert('operator_user', {
                        'operator_id': operator_id,
                        'user_id': str(user_id)
                    })
            
            logger.info(f"Updated operator '{operator_uid}'")
            return True
        
        except Exception as e:
            logger.error(f"Error updating operator '{operator_uid}': {str(e)}")
            return False
    
    @staticmethod
    def delete_operator(operator_uid: str) -> bool:
        """
        Delete an operator from the database.
        
        Args:
            operator_uid: UID of the operator to delete
        
        Returns:
            True if successful, False otherwise
        """
        try:
            operator = OperatorController.get_operator_by_uid(operator_uid)
            if not operator:
                logger.error(f"Operator '{operator_uid}' not found")
                return False
            
            operator_id = operator['id']
            
            # Delete related records
            sql.delete('operator_user', {'operator_id': operator_id})
            
            # Check if operator has lines
            line_count = sql.count('line', {'operator_id': operator_id})
            if line_count > 0:
                logger.warning(f"Operator '{operator_uid}' has {line_count} lines. Consider reassigning or deleting them first.")
                # Optionally, we could delete the lines or set operator_id to NULL
                # For now, we'll just log the warning and proceed
            
            # Delete the operator itself
            success = sql.delete_by_id('operator', operator_id)
            
            if success:
                logger.info(f"Deleted operator '{operator_uid}'")
            else:
                logger.error(f"Failed to delete operator '{operator_uid}'")
            
            return success
        
        except Exception as e:
            logger.error(f"Error deleting operator '{operator_uid}': {str(e)}")
            return False
    
    @staticmethod
    def add_user_to_operator(operator_uid: str, user_id: str) -> bool:
        """
        Add a user to an operator.
        
        Args:
            operator_uid: UID of the operator
            user_id: Discord ID of the user
        
        Returns:
            True if successful, False otherwise
        """
        try:
            operator = OperatorController.get_operator_by_uid(operator_uid)
            if not operator:
                logger.error(f"Operator '{operator_uid}' not found")
                return False
            
            operator_id = operator['id']
            
            # Check if user already exists in operator
            existing = sql.execute_query("""
                SELECT * FROM operator_user 
                WHERE operator_id = %s AND user_id = %s
            """, (operator_id, str(user_id)))
            
            if existing:
                logger.warning(f"User '{user_id}' already belongs to operator '{operator_uid}'")
                return True
            
            # Get or create user
            user = sql.select_one('user', where={'id': str(user_id)})
            if not user:
                user_insert_id = sql.insert('user', {'id': str(user_id)})
                if not user_insert_id:
                    logger.error(f"Could not create user entry for {user_id}")
                    return False
            
            # Add user to operator
            result = sql.insert('operator_user', {
                'operator_id': operator_id,
                'user_id': str(user_id)
            })
            
            if result:
                logger.info(f"Added user '{user_id}' to operator '{operator_uid}'")
                return True
            else:
                logger.error(f"Failed to add user '{user_id}' to operator '{operator_uid}'")
                return False
        
        except Exception as e:
            logger.error(f"Error adding user to operator: {str(e)}")
            return False
    
    @staticmethod
    def remove_user_from_operator(operator_uid: str, user_id: str) -> bool:
        """
        Remove a user from an operator.
        
        Args:
            operator_uid: UID of the operator
            user_id: Discord ID of the user
        
        Returns:
            True if successful, False otherwise
        """
        try:
            operator = OperatorController.get_operator_by_uid(operator_uid)
            if not operator:
                logger.error(f"Operator '{operator_uid}' not found")
                return False
            
            operator_id = operator['id']
            
            # Remove user from operator
            count = sql.delete('operator_user', {
                'operator_id': operator_id,
                'user_id': str(user_id)
            })
            
            if count > 0:
                logger.info(f"Removed user '{user_id}' from operator '{operator_uid}'")
                return True
            else:
                logger.warning(f"User '{user_id}' was not a member of operator '{operator_uid}'")
                return False
        
        except Exception as e:
            logger.error(f"Error removing user from operator: {str(e)}")
            return False
    
    @staticmethod
    def operator_exists(operator_uid: str) -> bool:
        """
        Check if an operator exists.
        
        Args:
            operator_uid: UID of the operator
        
        Returns:
            True if operator exists, False otherwise
        """
        return sql.exists('operator', {'uid': operator_uid})
    
    @staticmethod
    def user_belongs_to_operator(operator_uid: str, user_id: str) -> bool:
        """
        Check if a user belongs to an operator.
        
        Args:
            operator_uid: UID of the operator
            user_id: Discord ID of the user
        
        Returns:
            True if user belongs to operator, False otherwise
        """
        try:
            operator = OperatorController.get_operator_by_uid(operator_uid)
            if not operator:
                return False
            
            return str(user_id) in operator['users']
        
        except Exception as e:
            logger.error(f"Error checking user membership: {str(e)}")
            return False
    
    @staticmethod
    def count_operators() -> int:
        """
        Count total operators.
        
        Returns:
            Number of operators
        """
        try:
            return sql.count('operator')
        except Exception as e:
            logger.error(f"Error counting operators: {str(e)}")
            return 0
    
    @staticmethod
    def get_operator_lines(operator_uid: str) -> List[Dict[str, Any]]:
        """
        Get all lines for a specific operator.
        
        Args:
            operator_uid: UID of the operator
        
        Returns:
            List of line dictionaries
        """
        try:
            from core.controller import LineController
            return LineController.get_lines_by_operator(operator_uid)
        except Exception as e:
            logger.error(f"Error fetching lines for operator '{operator_uid}': {str(e)}")
            return []
