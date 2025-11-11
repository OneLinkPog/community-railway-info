from mysql.connector import Error, pooling
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Tuple
from core.config import config
from core.logger import Logger

logger = Logger("@sql")


class SQLConnector:
    """
    SQL Database Connector with connection pooling and CRUD operations.
    Supports MySQL/MariaDB with prepared statements for security.
    """
    
    def __init__(self):
        """Initialize the SQL connector with connection pool."""
        self.pool = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Create a connection pool for better performance."""
        try:
            self.pool = pooling.MySQLConnectionPool(
                pool_name="railway_info_pool",
                pool_size=20,
                pool_reset_session=True,
                host=config.db_host,
                port=config.db_port,
                user=config.db_user,
                password=config.db_password,
                database=config.db_database,
                autocommit=False,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
        except Error as e:
            logger.error(f"Error creating connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        Automatically handles connection lifecycle and error handling.
        
        Usage:
            with sql.get_connection() as conn:
                cursor = conn.cursor()
                # ... do work ...
        """
        connection = None
        try:
            connection = self.pool.get_connection()
            yield connection
        except Error as e:
            if connection:
                connection.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()
    
    @contextmanager
    def get_cursor(self, dictionary=True):
        """
        Context manager for database cursor.
        Automatically commits on success, rolls back on error.
        
        Args:
            dictionary: If True, returns results as dictionaries
        
        Usage:
            with sql.get_cursor() as cursor:
                cursor.execute("SELECT * FROM users")
                results = cursor.fetchall()
        """
        with self.get_connection() as connection:
            cursor = connection.cursor(dictionary=dictionary)
            try:
                yield cursor
                connection.commit()
            except Error as e:
                connection.rollback()
                logger.error(f"Query error: {e}")
                raise
            finally:
                cursor.close()
    
    # ==================== CREATE Operations ====================
    
    def insert(self, table: str, data: Dict[str, Any]) -> Optional[int]:
        """
        Insert a single record into a table.
        
        Args:
            table: Table name
            data: Dictionary of column names and values
        
        Returns:
            ID of inserted record or None on failure
        
        Example:
            user_id = sql.insert('users', {
                'discord_id': '123456789',
                'username': 'johndoe',
                'email': 'john@example.com'
            })
        """
        if not data:
            logger.warning("Insert called with empty data")
            return None
        
        columns = ', '.join(f"`{col}`" for col in data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO `{table}` ({columns}) VALUES ({placeholders})"
        
        try:
            with self.get_cursor(dictionary=False) as cursor:
                cursor.execute(query, tuple(data.values()))
                return cursor.lastrowid
        except Error as e:
            logger.error(f"Error inserting into {table}: {e}")
            return None
    
    def insert_many(self, table: str, columns: List[str], data: List[Tuple]) -> int:
        """
        Insert multiple records at once (batch insert).
        
        Args:
            table: Table name
            columns: List of column names
            data: List of tuples with values
        
        Returns:
            Number of inserted rows
        
        Example:
            count = sql.insert_many('stations', 
                ['name', 'line_id', 'position'],
                [
                    ('Central Station', 1, 0),
                    ('North Station', 1, 1),
                    ('South Station', 1, 2)
                ]
            )
        """
        if not data:
            return 0
        
        columns_str = ', '.join(f"`{col}`" for col in columns)
        placeholders = ', '.join(['%s'] * len(columns))
        query = f"INSERT INTO `{table}` ({columns_str}) VALUES ({placeholders})"
        
        try:
            with self.get_cursor(dictionary=False) as cursor:
                cursor.executemany(query, data)
                count = cursor.rowcount
                return count
        except Error as e:
            logger.error(f"Error batch inserting into {table}: {e}")
            return 0
    
    # ==================== READ Operations ====================
    
    def select(self, table: str, columns: List[str] = None, 
               where: Dict[str, Any] = None, 
               order_by: str = None, 
               limit: int = None) -> List[Dict[str, Any]]:
        """
        Select records from a table.
        
        Args:
            table: Table name
            columns: List of columns to select (None = all columns)
            where: Dictionary of conditions (AND logic)
            order_by: ORDER BY clause (e.g., 'created_at DESC')
            limit: Maximum number of results
        
        Returns:
            List of dictionaries containing the results
        
        Example:
            users = sql.select('users', 
                columns=['id', 'username'], 
                where={'active': 1},
                order_by='username ASC',
                limit=10
            )
        """
        cols = ', '.join(f"`{col}`" for col in columns) if columns else '*'
        query = f"SELECT {cols} FROM `{table}`"
        params = []
        
        if where:
            conditions = ' AND '.join(f"`{key}` = %s" for key in where.keys())
            query += f" WHERE {conditions}"
            params.extend(where.values())
        
        if order_by:
            query += f" ORDER BY {order_by}"
        
        if limit:
            query += f" LIMIT {int(limit)}"
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, tuple(params))
                results = cursor.fetchall()
                return results
        except Error as e:
            logger.error(f"Error selecting from {table}: {e}")
            return []
    
    def select_one(self, table: str, columns: List[str] = None, 
                   where: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Select a single record from a table.
        
        Args:
            table: Table name
            columns: List of columns to select
            where: Dictionary of conditions
        
        Returns:
            Dictionary with the result or None
        
        Example:
            user = sql.select_one('users', where={'id': 123})
        """
        results = self.select(table, columns, where, limit=1)
        return results[0] if results else None
    
    def select_by_id(self, table: str, record_id: int, 
                     id_column: str = 'id') -> Optional[Dict[str, Any]]:
        """
        Select a record by its ID.
        
        Args:
            table: Table name
            record_id: ID value
            id_column: Name of the ID column (default: 'id')
        
        Returns:
            Dictionary with the result or None
        
        Example:
            line = sql.select_by_id('lines', 42)
        """
        return self.select_one(table, where={id_column: record_id})
    
    def execute_query(self, query: str, params: Tuple = None) -> List[Dict[str, Any]]:
        """
        Execute a custom SELECT query.
        
        Args:
            query: SQL query string
            params: Tuple of parameters for prepared statement
        
        Returns:
            List of dictionaries containing the results
        
        Example:
            results = sql.execute_query(
                "SELECT * FROM lines WHERE operator_uid = %s AND status = %s",
                ('operator1', 'active')
            )
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params or ())
                results = cursor.fetchall()
                return results
        except Error as e:
            logger.error(f"Error executing custom query: {e}")
            return []
    
    # ==================== UPDATE Operations ====================
    
    def update(self, table: str, data: Dict[str, Any], 
               where: Dict[str, Any]) -> int:
        """
        Update records in a table.
        
        Args:
            table: Table name
            data: Dictionary of columns and new values
            where: Dictionary of conditions (AND logic)
        
        Returns:
            Number of affected rows
        
        Example:
            count = sql.update('users', 
                {'username': 'newname', 'updated_at': datetime.now()},
                {'id': 123}
            )
        """
        if not data or not where:
            logger.warning("Update called with empty data or where clause")
            return 0
        
        set_clause = ', '.join(f"`{key}` = %s" for key in data.keys())
        where_clause = ' AND '.join(f"`{key}` = %s" for key in where.keys())
        query = f"UPDATE `{table}` SET {set_clause} WHERE {where_clause}"
        params = list(data.values()) + list(where.values())
        
        try:
            with self.get_cursor(dictionary=False) as cursor:
                #logger.debug(f"Executing update query: {query}")
                #logger.debug(f"With parameters: {tuple(params)}")
                
                # Debug: Check if record exists before update
                if where and len(where) == 1:
                    check_key, check_value = next(iter(where.items()))
                    check_query = f"SELECT COUNT(*) as count FROM `{table}` WHERE `{check_key}` = %s"
                    cursor.execute(check_query, (check_value,))
                    #check_result = cursor.fetchone()
                    #logger.debug(f"Records found with {check_key}={check_value}: {check_result[0] if check_result else 'None'}")
                
                cursor.execute(query, tuple(params))
                count = cursor.rowcount
                #logger.debug(f"Update affected {count} rows")
                return count
        except Error as e:
            logger.error(f"Error updating {table}: {e}")
            logger.error(f"Query was: {query}")
            logger.error(f"Parameters were: {tuple(params)}")
            return 0
    
    def update_by_id(self, table: str, record_id: int, data: Dict[str, Any],
                     id_column: str = 'id') -> bool:
        """
        Update a record by its ID.
        
        Args:
            table: Table name
            record_id: ID value
            data: Dictionary of columns and new values
            id_column: Name of the ID column (default: 'id')
        
        Returns:
            True if record was updated, False otherwise
        
        Example:
            success = sql.update_by_id('lines', 42, {
                'name': 'Blue Line',
                'status': 'active'
            })
        """
        try:
            count = self.update(table, data, {id_column: record_id})
            #logger.debug(f"Update operation for {table} ID {record_id}: affected {count} rows")
            return count > 0
        except Exception as e:
            logger.error(f"Error in update_by_id for {table} ID {record_id}: {e}")
            logger.error(f"Data: {data}")
            raise  # Re-raise so calling code can handle it
    
    # ==================== DELETE Operations ====================
    
    def delete(self, table: str, where: Dict[str, Any]) -> int:
        """
        Delete records from a table.
        
        Args:
            table: Table name
            where: Dictionary of conditions (AND logic)
        
        Returns:
            Number of deleted rows
        
        Example:
            count = sql.delete('sessions', {'expired': 1})
        """
        if not where:
            logger.error("Delete called without WHERE clause - this is dangerous!")
            return 0
        
        where_clause = ' AND '.join(f"`{key}` = %s" for key in where.keys())
        query = f"DELETE FROM `{table}` WHERE {where_clause}"
        
        try:
            with self.get_cursor(dictionary=False) as cursor:
                cursor.execute(query, tuple(where.values()))
                count = cursor.rowcount
                return count
        except Error as e:
            logger.error(f"Error deleting from {table}: {e}")
            return 0
    
    def delete_by_id(self, table: str, record_id: int, 
                     id_column: str = 'id') -> bool:
        """
        Delete a record by its ID.
        
        Args:
            table: Table name
            record_id: ID value
            id_column: Name of the ID column (default: 'id')
        
        Returns:
            True if record was deleted, False otherwise
        
        Example:
            success = sql.delete_by_id('old_logs', 999)
        """
        count = self.delete(table, {id_column: record_id})
        return count > 0
    
    # ==================== Utility Methods ====================
    
    def exists(self, table: str, where: Dict[str, Any]) -> bool:
        """
        Check if a record exists.
        
        Args:
            table: Table name
            where: Dictionary of conditions
        
        Returns:
            True if record exists, False otherwise
        
        Example:
            if sql.exists('users', {'discord_id': '123456789'}):
                print("User already exists")
        """
        result = self.select_one(table, columns=['1'], where=where)
        return result is not None
    
    def count(self, table: str, where: Dict[str, Any] = None) -> int:
        """
        Count records in a table.
        
        Args:
            table: Table name
            where: Dictionary of conditions (optional)
        
        Returns:
            Number of records
        
        Example:
            total_users = sql.count('users')
            active_users = sql.count('users', {'active': 1})
        """
        query = f"SELECT COUNT(*) as count FROM `{table}`"
        params = []
        
        if where:
            conditions = ' AND '.join(f"`{key}` = %s" for key in where.keys())
            query += f" WHERE {conditions}"
            params.extend(where.values())
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, tuple(params))
                result = cursor.fetchone()
                return result['count'] if result else 0
        except Error as e:
            logger.error(f"Error counting records in {table}: {e}")
            return 0
    
    def execute_script(self, sql_script: str) -> bool:
        """
        Execute a multi-statement SQL script.
        
        Args:
            sql_script: SQL script with multiple statements
        
        Returns:
            True on success, False on failure
        
        Example:
            with open('schema.sql', 'r') as f:
                sql.execute_script(f.read())
        """
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                # Execute multi-statement
                for result in cursor.execute(sql_script, multi=True):
                    if result.with_rows:
                        result.fetchall()
                connection.commit()
                cursor.close()
                return True
        except Error as e:
            logger.error(f"Error executing SQL script: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test the database connection.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            with self.get_connection() as connection:
                if connection.is_connected():
                    logger.info("Database connection test successful")
                    return True
            return False
        except Error as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def close_pool(self):
        """Close all connections in the pool."""
        if self.pool:
            # MySQL Connector doesn't have a direct close_pool method
            # but connections will be closed when pool is garbage collected
            self.pool = None


# Global SQL connector instance
try:
    sql = SQLConnector()
except Exception as e:
    logger.error(f"Failed to initialize SQL connector: {e}")
    sql = None
