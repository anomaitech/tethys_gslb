"""
Simple SQLite database utilities for GWapp
"""
import os
import sqlite3
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SQLiteManager:
    """
    Simple SQLite database manager for column schemes
    """
    
    def __init__(self, db_path=None):
        if db_path is None:
            # Use a default path in the current working directory
            db_path = os.path.join(os.getcwd(), 'gwapp.db')
        
        # Ensure the directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize database tables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create column_schemes table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS column_schemes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        description TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        is_active INTEGER DEFAULT 1
                    )
                ''')
                
                # Create scheme_columns table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS scheme_columns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        scheme_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        description TEXT,
                        column_type TEXT NOT NULL DEFAULT 'required',
                        data_type TEXT NOT NULL DEFAULT 'TEXT',
                        is_primary_key INTEGER DEFAULT 0,
                        is_unique INTEGER DEFAULT 0,
                        max_length INTEGER,
                        default_value TEXT,
                        order_index INTEGER DEFAULT 0,
                        FOREIGN KEY (scheme_id) REFERENCES column_schemes (id) ON DELETE CASCADE,
                        UNIQUE (scheme_id, name)
                    )
                ''')
                
                # Create dynamic_data_tables tracking table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS dynamic_data_tables (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        scheme_id INTEGER NOT NULL,
                        table_name TEXT UNIQUE NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        record_count INTEGER DEFAULT 0,
                        FOREIGN KEY (scheme_id) REFERENCES column_schemes (id) ON DELETE CASCADE
                    )
                ''')
                
                # Create basins management table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS basins (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        description TEXT,
                        latitude_column TEXT NOT NULL,
                        longitude_column TEXT NOT NULL,
                        date_column TEXT NOT NULL,
                        value_columns TEXT NOT NULL,
                        scheme_id INTEGER NOT NULL,
                        table_name TEXT UNIQUE NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        record_count INTEGER DEFAULT 0,
                        FOREIGN KEY (scheme_id) REFERENCES column_schemes (id) ON DELETE CASCADE
                    )
                ''')
                
                conn.commit()
                
                # Check if we need to add default data
                cursor.execute('SELECT COUNT(*) FROM column_schemes')
                count = cursor.fetchone()[0]
                
                if count == 0:
                    self.create_default_scheme()
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def create_default_scheme(self):
        """Create default groundwater scheme"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create default scheme
                cursor.execute('''
                    INSERT INTO column_schemes (name, description, is_active)
                    VALUES (?, ?, ?)
                ''', ('Default Groundwater Scheme', 'Standard groundwater monitoring data columns', 1))
                
                scheme_id = cursor.lastrowid
                
                # Add default required columns
                required_columns = [
                    ('well_id', 'Unique well identifier', 'TEXT', 1, 0, None, '', 1),
                    ('latitude', 'Latitude coordinates', 'REAL', 0, 0, None, '', 2),
                    ('longitude', 'Longitude coordinates', 'REAL', 0, 0, None, '', 3),
                    ('date', 'Measurement date', 'DATE', 0, 0, None, '', 4),
                    ('water_table_elevation', 'Water table elevation', 'REAL', 0, 0, None, '', 5)
                ]
                
                for name, desc, data_type, is_pk, is_unique, max_len, default_val, order in required_columns:
                    cursor.execute('''
                        INSERT INTO scheme_columns 
                        (scheme_id, name, description, column_type, data_type, is_primary_key, is_unique, max_length, default_value, order_index)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (scheme_id, name, desc, 'required', data_type, is_pk, is_unique, max_len, default_val, order))
                
                # Add default optional columns
                optional_columns = [
                    ('temperature', 'Water temperature', 'REAL', 0, 0, None, '', 6),
                    ('pH', 'pH value', 'REAL', 0, 0, None, '', 7),
                    ('conductivity', 'Electrical conductivity', 'REAL', 0, 0, None, '', 8)
                ]
                
                for name, desc, data_type, is_pk, is_unique, max_len, default_val, order in optional_columns:
                    cursor.execute('''
                        INSERT INTO scheme_columns 
                        (scheme_id, name, description, column_type, data_type, is_primary_key, is_unique, max_length, default_value, order_index)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (scheme_id, name, desc, 'optional', data_type, is_pk, is_unique, max_len, default_val, order))
                
                conn.commit()
                logger.info("Created default groundwater scheme")
                
        except Exception as e:
            logger.error(f"Error creating default scheme: {e}")
    
    def get_all_schemes(self):
        """Get all column schemes"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get schemes
                cursor.execute('SELECT * FROM column_schemes ORDER BY name')
                schemes = cursor.fetchall()
                
                result = []
                for scheme in schemes:
                    scheme_dict = {
                        'id': scheme[0],
                        'name': scheme[1],
                        'description': scheme[2] or '',
                        'created_at': scheme[3],
                        'updated_at': scheme[4],
                        'is_active': bool(scheme[5]),
                        'required_columns': [],
                        'optional_columns': []
                    }
                    
                    # Get columns for this scheme
                    cursor.execute('''
                        SELECT name, description, column_type, data_type, is_primary_key, is_unique, max_length, default_value, order_index
                        FROM scheme_columns 
                        WHERE scheme_id = ? 
                        ORDER BY order_index, name
                    ''', (scheme[0],))
                    
                    columns = cursor.fetchall()
                    
                    for col in columns:
                        col_dict = {
                            'name': col[0],
                            'description': col[1] or '',
                            'data_type': col[3],
                            'is_primary_key': bool(col[4]),
                            'is_unique': bool(col[5]),
                            'max_length': col[6],
                            'default_value': col[7] or '',
                            'order': col[8]
                        }
                        
                        if col[2] == 'required':
                            scheme_dict['required_columns'].append(col_dict)
                        else:
                            scheme_dict['optional_columns'].append(col_dict)
                    
                    result.append(scheme_dict)
                
                return result
                
        except Exception as e:
            logger.error(f"Error getting schemes: {e}")
            return []
    
    def create_scheme(self, name, description='', required_columns=None, optional_columns=None):
        """Create a new column scheme"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if scheme with this name already exists
                cursor.execute('SELECT id FROM column_schemes WHERE name = ?', (name,))
                if cursor.fetchone():
                    raise ValueError(f"Scheme with name '{name}' already exists")
                
                # Create scheme
                cursor.execute('''
                    INSERT INTO column_schemes (name, description, is_active)
                    VALUES (?, ?, ?)
                ''', (name, description, 1))
                
                scheme_id = cursor.lastrowid
                
                # Add required columns
                if required_columns:
                    for i, col in enumerate(required_columns):
                        cursor.execute('''
                            INSERT INTO scheme_columns 
                            (scheme_id, name, description, column_type, data_type, is_primary_key, is_unique, max_length, default_value, order_index)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            scheme_id, col['name'], col.get('description', ''), 'required',
                            col.get('data_type', 'TEXT'), col.get('is_primary_key', 0),
                            col.get('is_unique', 0), col.get('max_length'), 
                            col.get('default_value', ''), col.get('order', i + 1)
                        ))
                
                # Add optional columns
                if optional_columns:
                    start_order = len(required_columns) if required_columns else 0
                    for i, col in enumerate(optional_columns):
                        cursor.execute('''
                            INSERT INTO scheme_columns 
                            (scheme_id, name, description, column_type, data_type, is_primary_key, is_unique, max_length, default_value, order_index)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            scheme_id, col['name'], col.get('description', ''), 'optional',
                            col.get('data_type', 'TEXT'), col.get('is_primary_key', 0),
                            col.get('is_unique', 0), col.get('max_length'), 
                            col.get('default_value', ''), col.get('order', start_order + i + 1)
                        ))
                
                conn.commit()
                
                # Create the actual data table
                self.create_scheme_table(scheme_id)
                
                # Get the created scheme
                return self.get_scheme_by_id(scheme_id)
                
        except Exception as e:
            logger.error(f"Error creating scheme: {e}")
            raise e
    
    def get_scheme_by_id(self, scheme_id):
        """Get a specific scheme by ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM column_schemes WHERE id = ?', (scheme_id,))
                scheme = cursor.fetchone()
                
                if not scheme:
                    return None
                
                scheme_dict = {
                    'id': scheme[0],
                    'name': scheme[1],
                    'description': scheme[2] or '',
                    'created_at': scheme[3],
                    'updated_at': scheme[4],
                    'is_active': bool(scheme[5]),
                    'required_columns': [],
                    'optional_columns': []
                }
                
                # Get columns
                cursor.execute('''
                    SELECT name, description, column_type, data_type, is_primary_key, is_unique, max_length, default_value, order_index
                    FROM scheme_columns 
                    WHERE scheme_id = ? 
                    ORDER BY order_index, name
                ''', (scheme_id,))
                
                columns = cursor.fetchall()
                
                for col in columns:
                    col_dict = {
                        'name': col[0],
                        'description': col[1] or '',
                        'data_type': col[3],
                        'is_primary_key': bool(col[4]),
                        'is_unique': bool(col[5]),
                        'max_length': col[6],
                        'default_value': col[7] or '',
                        'order': col[8]
                    }
                    
                    if col[2] == 'required':
                        scheme_dict['required_columns'].append(col_dict)
                    else:
                        scheme_dict['optional_columns'].append(col_dict)
                
                return scheme_dict
                
        except Exception as e:
            logger.error(f"Error getting scheme {scheme_id}: {e}")
            return None
    
    def update_scheme(self, scheme_id, name=None, description=None, required_columns=None, optional_columns=None):
        """Update an existing scheme"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if scheme exists
                cursor.execute('SELECT name FROM column_schemes WHERE id = ?', (scheme_id,))
                existing = cursor.fetchone()
                if not existing:
                    raise ValueError(f"Scheme with ID {scheme_id} not found")
                
                old_table_name = self.generate_table_name(existing[0])
                
                # Update scheme info
                if name is not None:
                    # Check if new name already exists
                    cursor.execute('SELECT id FROM column_schemes WHERE name = ? AND id != ?', (name, scheme_id))
                    if cursor.fetchone():
                        raise ValueError(f"Scheme with name '{name}' already exists")
                    
                    cursor.execute('UPDATE column_schemes SET name = ?, updated_at = ? WHERE id = ?', 
                                 (name, datetime.now().isoformat(), scheme_id))
                
                if description is not None:
                    cursor.execute('UPDATE column_schemes SET description = ?, updated_at = ? WHERE id = ?', 
                                 (description, datetime.now().isoformat(), scheme_id))
                
                # Update columns if provided
                if required_columns is not None or optional_columns is not None:
                    # Remove existing columns
                    cursor.execute('DELETE FROM scheme_columns WHERE scheme_id = ?', (scheme_id,))
                    
                    # Add new required columns
                    if required_columns:
                        for i, col in enumerate(required_columns):
                            cursor.execute('''
                                INSERT INTO scheme_columns 
                                (scheme_id, name, description, column_type, data_type, is_primary_key, is_unique, max_length, default_value, order_index)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                scheme_id, col['name'], col.get('description', ''), 'required',
                                col.get('data_type', 'TEXT'), col.get('is_primary_key', 0),
                                col.get('is_unique', 0), col.get('max_length'), 
                                col.get('default_value', ''), col.get('order', i + 1)
                            ))
                    
                    # Add new optional columns
                    if optional_columns:
                        start_order = len(required_columns) if required_columns else 0
                        for i, col in enumerate(optional_columns):
                            cursor.execute('''
                                INSERT INTO scheme_columns 
                                (scheme_id, name, description, column_type, data_type, is_primary_key, is_unique, max_length, default_value, order_index)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                scheme_id, col['name'], col.get('description', ''), 'optional',
                                col.get('data_type', 'TEXT'), col.get('is_primary_key', 0),
                                col.get('is_unique', 0), col.get('max_length'), 
                                col.get('default_value', ''), col.get('order', start_order + i + 1)
                            ))
                
                conn.commit()
                
                # Update the data table if structure changed
                if required_columns is not None or optional_columns is not None:
                    new_scheme = self.get_scheme_by_id(scheme_id)
                    new_table_name = self.generate_table_name(new_scheme['name'])
                    
                    if old_table_name != new_table_name:
                        self.drop_scheme_table(old_table_name)
                    
                    self.create_scheme_table(scheme_id)
                
                return self.get_scheme_by_id(scheme_id)
                
        except Exception as e:
            logger.error(f"Error updating scheme: {e}")
            raise e
    
    def delete_scheme(self, scheme_id):
        """Delete a scheme and its associated table"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get scheme name for table deletion
                cursor.execute('SELECT name FROM column_schemes WHERE id = ?', (scheme_id,))
                scheme = cursor.fetchone()
                if not scheme:
                    raise ValueError(f"Scheme with ID {scheme_id} not found")
                
                table_name = self.generate_table_name(scheme[0])
                
                # Delete the scheme (cascade will handle columns)
                cursor.execute('DELETE FROM column_schemes WHERE id = ?', (scheme_id,))
                conn.commit()
                
                # Drop the actual data table
                self.drop_scheme_table(table_name)
                
                return True
                
        except Exception as e:
            logger.error(f"Error deleting scheme: {e}")
            raise e
    
    def generate_table_name(self, scheme_name):
        """Generate a valid SQL table name from scheme name"""
        import re
        table_name = re.sub(r'[^a-zA-Z0-9_]', '_', scheme_name.lower())
        table_name = re.sub(r'_+', '_', table_name)
        table_name = table_name.strip('_')
        
        if table_name and not table_name[0].isalpha():
            table_name = f"scheme_{table_name}"
        
        return f"data_{table_name or 'default_scheme'}"
    
    def create_scheme_table(self, scheme_id):
        """Create a data table based on the scheme"""
        try:
            scheme = self.get_scheme_by_id(scheme_id)
            if not scheme:
                return
            
            table_name = self.generate_table_name(scheme['name'])
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build CREATE TABLE statement
                columns_sql = []
                all_columns = scheme['required_columns'] + scheme['optional_columns']
                all_columns.sort(key=lambda x: x['order'])
                
                for col in all_columns:
                    sql_type = col['data_type']
                    if col['data_type'] == 'TEXT' and col.get('max_length'):
                        sql_type = f"VARCHAR({col['max_length']})"
                    
                    definition = f"{col['name']} {sql_type}"
                    
                    if col.get('is_primary_key'):
                        definition += " PRIMARY KEY"
                    elif col in scheme['required_columns']:
                        definition += " NOT NULL"
                    
                    if col.get('is_unique') and not col.get('is_primary_key'):
                        definition += " UNIQUE"
                    
                    if col.get('default_value'):
                        if col['data_type'] in ['TEXT', 'DATE', 'DATETIME']:
                            definition += f" DEFAULT '{col['default_value']}'"
                        else:
                            definition += f" DEFAULT {col['default_value']}"
                    
                    columns_sql.append(definition)
                
                if columns_sql:
                    create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns_sql)})"
                    cursor.execute(create_sql)
                    
                    # Record the table in tracking
                    cursor.execute('''
                        INSERT OR REPLACE INTO dynamic_data_tables (scheme_id, table_name, record_count)
                        VALUES (?, ?, 0)
                    ''', (scheme_id, table_name))
                    
                    conn.commit()
                    logger.info(f"Created table {table_name} for scheme {scheme['name']}")
                
        except Exception as e:
            logger.error(f"Error creating table for scheme {scheme_id}: {e}")
    
    def drop_scheme_table(self, table_name):
        """Drop a scheme's data table"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                cursor.execute('DELETE FROM dynamic_data_tables WHERE table_name = ?', (table_name,))
                
                conn.commit()
                logger.info(f"Dropped table {table_name}")
                
        except Exception as e:
            logger.error(f"Error dropping table {table_name}: {e}")
    
    def create_basin(self, name, description, latitude_column, longitude_column, date_column, value_columns, scheme_id, table_name):
        """Create a new basin and its data table"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if basin with this name already exists
                cursor.execute('SELECT id FROM basins WHERE name = ?', (name,))
                if cursor.fetchone():
                    raise ValueError(f"Basin with name '{name}' already exists")
                
                # Create basin record
                cursor.execute('''
                    INSERT INTO basins (name, description, latitude_column, longitude_column, date_column, value_columns, scheme_id, table_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (name, description, latitude_column, longitude_column, date_column, value_columns, scheme_id, table_name))
                
                basin_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Created basin: {name} (ID: {basin_id})")
                return basin_id
                
        except Exception as e:
            logger.error(f"Error creating basin: {e}")
            raise e
    
    def get_basin_by_name(self, name):
        """Get basin by name"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM basins WHERE name = ?', (name,))
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                return {
                    'id': row[0],
                    'name': row[1],
                    'description': row[2] or '',
                    'latitude_column': row[3],
                    'longitude_column': row[4],
                    'date_column': row[5],
                    'value_columns': row[6].split(',') if row[6] else [],
                    'scheme_id': row[7],
                    'table_name': row[8],
                    'created_at': row[9],
                    'updated_at': row[10],
                    'record_count': row[11]
                }
        except Exception as e:
            logger.error(f"Error getting basin: {e}")
            return None
    
    def get_all_basins(self):
        """Get all basins"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM basins ORDER BY name')
                rows = cursor.fetchall()
                
                basins = []
                for row in rows:
                    basins.append({
                        'id': row[0],
                        'name': row[1],
                        'description': row[2] or '',
                        'latitude_column': row[3],
                        'longitude_column': row[4],
                        'date_column': row[5],
                        'value_columns': row[6].split(',') if row[6] else [],
                        'scheme_id': row[7],
                        'table_name': row[8],
                        'created_at': row[9],
                        'updated_at': row[10],
                        'record_count': row[11]
                    })
                
                return basins
        except Exception as e:
            logger.error(f"Error getting basins: {e}")
            return []
    
    def create_basin_table(self, table_name, scheme_columns, column_mappings):
        """Create a data table for a basin with mapped columns"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build CREATE TABLE statement
                columns_sql = []
                
                # Always add an auto-incrementing id as primary key
                # We ignore any is_primary_key flags from the schema and always use auto-incrementing id
                columns_sql.append("id INTEGER PRIMARY KEY AUTOINCREMENT")
                logger.info(f"Adding auto-incrementing 'id' column as primary key for table {table_name}")
                
                # Get required columns list for checking
                required_cols = [c for c in scheme_columns if c.get('column_type') == 'required']
                
                # Build column definitions - NEVER use any column as primary key (we use auto-incrementing id)
                for col_def in scheme_columns:
                    col_name = col_def['name']
                    if col_name in column_mappings:
                        data_type = col_def.get('data_type', 'TEXT')
                        if data_type == 'TEXT' and col_def.get('max_length'):
                            sql_type = f"VARCHAR({col_def['max_length']})"
                        else:
                            sql_type = data_type
                        
                        definition = f"{col_name} {sql_type}"
                        
                        # NEVER add PRIMARY KEY to any column - we use auto-incrementing id
                        # Only add NOT NULL for required columns
                        if col_def in required_cols:
                            definition += " NOT NULL"
                        
                        # Don't add UNIQUE constraint to well_id (allows duplicates)
                        # Also skip UNIQUE for other columns to allow flexibility
                        # Only add UNIQUE if explicitly specified AND it's not well_id
                        if col_def.get('is_unique'):
                            # Skip UNIQUE for well_id columns to allow multiple measurements per well
                            if 'well' not in col_name.lower() or 'id' not in col_name.lower():
                                definition += " UNIQUE"
                        
                        if col_def.get('default_value'):
                            if data_type in ['TEXT', 'DATE', 'DATETIME']:
                                definition += f" DEFAULT '{col_def['default_value']}'"
                            else:
                                definition += f" DEFAULT {col_def['default_value']}"
                        
                        columns_sql.append(definition)
                
                if columns_sql:
                    create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns_sql)})"
                    cursor.execute(create_sql)
                    conn.commit()
                    logger.info(f"Created basin table {table_name}")
                else:
                    raise ValueError("No columns to create in basin table")
                
        except Exception as e:
            logger.error(f"Error creating basin table {table_name}: {e}")
            raise e
    
    def insert_data_into_basin_table(self, table_name, data_rows):
        """Insert data rows into a basin's table, handling duplicates"""
        try:
            if not data_rows:
                return 0
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get column names from first row
                column_names = list(data_rows[0].keys())
                placeholders = ', '.join(['?' for _ in column_names])
                
                # Use INSERT OR IGNORE to skip duplicates, or INSERT OR REPLACE to update them
                insert_sql = f"INSERT OR IGNORE INTO {table_name} ({', '.join(column_names)}) VALUES ({placeholders})"
                
                # Prepare data rows
                values_list = []
                for row in data_rows:
                    values = [row.get(col) for col in column_names]
                    values_list.append(values)
                
                cursor.executemany(insert_sql, values_list)
                inserted_count = cursor.rowcount
                
                # Update record count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                cursor.execute('UPDATE basins SET record_count = ?, updated_at = ? WHERE table_name = ?', 
                             (count, datetime.now().isoformat(), table_name))
                
                conn.commit()
                logger.info(f"Inserted {inserted_count} rows into {table_name} (skipped {len(data_rows) - inserted_count} duplicates)")
                return inserted_count
                
        except Exception as e:
            logger.error(f"Error inserting data into basin table: {e}")
            raise e
    
    def insert_data_into_scheme_table(self, scheme_id, data_rows):
        """Insert data rows into a scheme's table, handling duplicates"""
        try:
            if not data_rows:
                return 0
            
            scheme = self.get_scheme_by_id(scheme_id)
            if not scheme:
                raise ValueError(f"Scheme with ID {scheme_id} not found")
            
            table_name = self.generate_table_name(scheme['name'])
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get column names from the scheme (only mapped columns that exist in data)
                scheme_column_names = [col['name'] for col in sorted(scheme['required_columns'] + scheme['optional_columns'], key=lambda x: x.get('order', 0))]
                
                # Filter to only columns that exist in the data
                column_names = [col for col in scheme_column_names if col in data_rows[0].keys()]
                
                if not column_names:
                    raise ValueError("No matching columns found between scheme and data")
                
                placeholders = ', '.join(['?' for _ in column_names])
                # Use INSERT OR IGNORE to skip duplicates
                insert_sql = f"INSERT OR IGNORE INTO {table_name} ({', '.join(column_names)}) VALUES ({placeholders})"
                
                # Prepare data rows
                values_list = []
                for row in data_rows:
                    values = [row.get(col) for col in column_names]
                    values_list.append(values)
                
                cursor.executemany(insert_sql, values_list)
                inserted_count = cursor.rowcount
                
                # Update record count in dynamic_data_tables
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                cursor.execute('''
                    UPDATE dynamic_data_tables 
                    SET record_count = ? 
                    WHERE table_name = ?
                ''', (count, table_name))
                
                conn.commit()
                logger.info(f"Inserted {inserted_count} rows into {table_name} (skipped {len(data_rows) - inserted_count} duplicates)")
                return inserted_count
                
        except Exception as e:
            logger.error(f"Error inserting data into scheme table: {e}")
            raise e
    
    def get_unique_points_for_basin(self, basin_id):
        """Get unique latitude/longitude points for a basin"""
        try:
            basin = self.get_basin_by_id(basin_id)
            if not basin:
                logger.warning(f"Basin {basin_id} not found")
                return []
            
            table_name = basin['table_name']
            csv_lat_col = basin['latitude_column']  # CSV column name (e.g., "lat_dec")
            csv_lon_col = basin['longitude_column']  # CSV column name (e.g., "long_dec")
            scheme_id = basin['scheme_id']
            
            logger.info(f"Getting unique points from table {table_name}")
            logger.info(f"CSV columns configured: lat={csv_lat_col}, lon={csv_lon_col}")
            
            # Get the scheme to find which schema columns map to these CSV columns
            scheme = self.get_scheme_by_id(scheme_id)
            if not scheme:
                logger.error(f"Scheme {scheme_id} not found")
                return []
            
            # Find which schema column names map to the CSV column names
            # We need to check the scheme_columns table to see the mappings
            # But actually, the table columns are named after the schema column names
            # So we need to find which schema column was mapped to the CSV column
            
            # Get all scheme columns
            all_scheme_columns = scheme.get('required_columns', []) + scheme.get('optional_columns', [])
            
            # The table columns are named after schema column names
            # We need to find which schema column name corresponds to the CSV column
            # Since we don't store the reverse mapping, we'll check the actual table columns
            # and match based on the CSV column name stored in the basin config
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # First, check if table exists and has data
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                total_rows = cursor.fetchone()[0]
                logger.info(f"Total rows in {table_name}: {total_rows}")
                
                # Get actual table columns
                cursor.execute(f"PRAGMA table_info(\"{table_name}\")")
                columns_info = cursor.fetchall()
                actual_columns = [col[1] for col in columns_info]
                logger.info(f"Table {table_name} actual columns: {actual_columns}")
                
                # Find well_id column (could be well_id, Well_ID, etc.)
                well_id_col = None
                for col in actual_columns:
                    if 'well' in col.lower() and 'id' in col.lower():
                        well_id_col = col
                        break
                
                if not well_id_col:
                    logger.error(f"Could not find well_id column in table {table_name}")
                    return []
                
                logger.info(f"Using well_id column: {well_id_col}")
                
                # Find lat/lon columns
                lat_col = None
                lon_col = None
                
                # First, check if CSV column names exist in table
                if csv_lat_col in actual_columns:
                    lat_col = csv_lat_col
                    logger.info(f"Found CSV column name '{csv_lat_col}' in table")
                else:
                    # Find schema column that likely maps to latitude
                    for schema_col in all_scheme_columns:
                        schema_col_name = schema_col.get('name', '')
                        if schema_col_name in actual_columns and 'lat' in schema_col_name.lower():
                            lat_col = schema_col_name
                            logger.info(f"Using schema column '{lat_col}' for latitude (mapped from CSV '{csv_lat_col}')")
                            break
                
                if csv_lon_col in actual_columns:
                    lon_col = csv_lon_col
                    logger.info(f"Found CSV column name '{csv_lon_col}' in table")
                else:
                    # Find schema column that likely maps to longitude
                    for schema_col in all_scheme_columns:
                        schema_col_name = schema_col.get('name', '')
                        if schema_col_name in actual_columns and ('lon' in schema_col_name.lower() or 'lng' in schema_col_name.lower()):
                            lon_col = schema_col_name
                            logger.info(f"Using schema column '{lon_col}' for longitude (mapped from CSV '{csv_lon_col}')")
                            break
                
                if not lat_col or not lon_col:
                    logger.error(f"Could not find latitude/longitude columns. Lat: {lat_col}, Lon: {lon_col}")
                    return []
                
                logger.info(f"Using columns: {well_id_col} (well_id), {lat_col} (lat), {lon_col} (lon)")
                
                # Group by well_id and count measurements, get lat/lon for each well
                # Use AVG to get representative lat/lon for each well (in case there are slight variations)
                query = f'''
                    SELECT 
                        "{well_id_col}" as well_id,
                        AVG("{lat_col}") as avg_lat,
                        AVG("{lon_col}") as avg_lon,
                        COUNT(*) as measurement_count
                    FROM "{table_name}"
                    WHERE "{lat_col}" IS NOT NULL 
                    AND "{lon_col}" IS NOT NULL
                    AND "{well_id_col}" IS NOT NULL
                    GROUP BY "{well_id_col}"
                    HAVING COUNT(*) >= 10
                    ORDER BY measurement_count DESC
                '''
                
                logger.info(f"Executing query: {query}")
                cursor.execute(query)
                rows = cursor.fetchall()
                
                logger.info(f"Found {len(rows)} wells with at least 10 measurements")
                
                points = []
                for row in rows:
                    try:
                        well_id = row[0]
                        lat = float(row[1])  # avg_lat
                        lon = float(row[2])  # avg_lon
                        measurement_count = int(row[3])  # measurement_count
                        
                        # Validate coordinates are reasonable (within valid ranges)
                        if abs(lat) > 90 or abs(lon) > 180:
                            logger.warning(f"Skipping invalid coordinates for well {well_id}: lat={lat}, lon={lon}")
                            continue
                        
                        # Only include wells with 10+ measurements (already filtered in query, but double-check)
                        if measurement_count < 10:
                            continue
                            
                        points.append({
                            'latitude': lat,
                            'longitude': lon,
                            'coordinates': [lon, lat],  # GeoJSON format: [lon, lat]
                            'measurement_count': measurement_count,
                            'well_id': well_id
                        })
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error parsing coordinates for row {row}, error: {e}")
                        continue
                
                logger.info(f"Returning {len(points)} valid points")
                return points
        except Exception as e:
            logger.error(f"Error getting unique points for basin: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def get_basin_by_id(self, basin_id):
        """Get basin by ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM basins WHERE id = ?', (basin_id,))
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                return {
                    'id': row[0],
                    'name': row[1],
                    'description': row[2] or '',
                    'latitude_column': row[3],
                    'longitude_column': row[4],
                    'date_column': row[5],
                    'value_columns': row[6].split(',') if row[6] else [],
                    'scheme_id': row[7],
                    'table_name': row[8],
                    'created_at': row[9],
                    'updated_at': row[10],
                    'record_count': row[11]
                }
        except Exception as e:
            logger.error(f"Error getting basin by ID: {e}")
            return None
    
    def delete_basin(self, basin_id):
        """Delete a basin and its associated table"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get basin info to find table name
                basin = self.get_basin_by_id(basin_id)
                if not basin:
                    raise ValueError(f"Basin with ID {basin_id} not found")
                
                table_name = basin['table_name']
                
                # Drop the basin table
                try:
                    cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
                    logger.info(f"Dropped table {table_name} for basin {basin_id}")
                except Exception as e:
                    logger.warning(f"Error dropping table {table_name}: {e}")
                    # Continue with deletion even if table drop fails
                
                # Delete the basin record
                cursor.execute('DELETE FROM basins WHERE id = ?', (basin_id,))
                
                if cursor.rowcount == 0:
                    raise ValueError(f"Basin with ID {basin_id} not found")
                
                conn.commit()
                logger.info(f"Successfully deleted basin {basin_id} ({basin['name']})")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting basin {basin_id}: {e}")
            raise
    
    def get_timeseries_for_well(self, basin_id, well_id):
        """Get time series data for a specific well_id"""
        try:
            basin = self.get_basin_by_id(basin_id)
            if not basin:
                logger.warning(f"Basin {basin_id} not found")
                return []
            
            table_name = basin['table_name']
            csv_date_col = basin['date_column']
            value_cols_str = basin['value_columns']
            scheme_id = basin['scheme_id']
            
            # Parse value columns
            if isinstance(value_cols_str, str):
                csv_value_cols = [col.strip() for col in value_cols_str.split(',')]
            else:
                csv_value_cols = value_cols_str if isinstance(value_cols_str, list) else []
            
            logger.info(f"Getting timeseries for well_id: {well_id} from table {table_name}")
            
            # Get the scheme to find schema column names
            scheme = self.get_scheme_by_id(scheme_id)
            if not scheme:
                logger.error(f"Scheme {scheme_id} not found")
                return []
            
            all_scheme_columns = scheme.get('required_columns', []) + scheme.get('optional_columns', [])
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get actual table columns
                cursor.execute(f"PRAGMA table_info(\"{table_name}\")")
                columns_info = cursor.fetchall()
                actual_columns = [col[1] for col in columns_info]
                logger.info(f"Table {table_name} actual columns: {actual_columns}")
                
                # Find well_id column
                well_id_col = None
                for col in actual_columns:
                    if 'well' in col.lower() and 'id' in col.lower():
                        well_id_col = col
                        break
                
                if not well_id_col:
                    logger.error(f"Could not find well_id column in table {table_name}")
                    return []
                
                # Find date and value columns (same logic as get_timeseries_for_point)
                date_col = None
                csv_date_col_lower = csv_date_col.lower().strip()
                
                for actual_col in actual_columns:
                    if actual_col.lower() == csv_date_col_lower:
                        date_col = actual_col
                        break
                
                if not date_col:
                    for schema_col in all_scheme_columns:
                        schema_col_name = schema_col.get('name', '')
                        if schema_col_name in actual_columns:
                            if csv_date_col_lower == schema_col_name.lower() or 'date' in schema_col_name.lower() or 'time' in schema_col_name.lower():
                                date_col = schema_col_name
                                break
                
                value_cols = []
                for csv_val_col in csv_value_cols:
                    csv_val_col_lower = csv_val_col.lower().strip()
                    for actual_col in actual_columns:
                        if actual_col.lower() == csv_val_col_lower:
                            value_cols.append(actual_col)
                            break
                    if not any(v == actual_col for v in value_cols for actual_col in actual_columns if actual_col.lower() == csv_val_col_lower):
                        for schema_col in all_scheme_columns:
                            schema_col_name = schema_col.get('name', '')
                            if schema_col_name in actual_columns and csv_val_col_lower == schema_col_name.lower():
                                value_cols.append(schema_col_name)
                                break
                
                if not date_col:
                    logger.error(f"Could not find date column")
                    return []
                
                logger.info(f"Using columns: well_id={well_id_col}, date={date_col}, values={value_cols}")
                
                # Build SELECT statement
                select_cols = [date_col] + value_cols
                select_sql = ', '.join([f'"{col}"' for col in select_cols])
                
                # Get all records for this well_id
                query = f'''
                    SELECT {select_sql}
                    FROM "{table_name}"
                    WHERE "{well_id_col}" = ?
                    ORDER BY "{date_col}"
                '''
                
                logger.info(f"Executing query: {query}")
                logger.info(f"Parameters: well_id={well_id}")
                cursor.execute(query, (well_id,))
                
                rows = cursor.fetchall()
                logger.info(f"Found {len(rows)} time series records for well_id {well_id}")
                
                timeseries = []
                for row in rows:
                    record = {
                        'date': row[0]
                    }
                    # Add all value columns
                    for i, val_col in enumerate(value_cols, start=1):
                        record[val_col] = row[i]
                    timeseries.append(record)
                
                return timeseries
        except Exception as e:
            logger.error(f"Error getting timeseries for well: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def get_timeseries_for_point(self, basin_id, latitude, longitude, tolerance=0.0001):
        """Get time series data for a specific lat/lon point"""
        try:
            basin = self.get_basin_by_id(basin_id)
            if not basin:
                logger.warning(f"Basin {basin_id} not found")
                return []
            
            table_name = basin['table_name']
            csv_lat_col = basin['latitude_column']  # CSV column name
            csv_lon_col = basin['longitude_column']  # CSV column name
            csv_date_col = basin['date_column']  # CSV column name
            value_cols_str = basin['value_columns']  # Comma-separated CSV column names
            scheme_id = basin['scheme_id']
            
            # Parse value columns (comma-separated string)
            if isinstance(value_cols_str, str):
                csv_value_cols = [col.strip() for col in value_cols_str.split(',')]
            else:
                csv_value_cols = value_cols_str if isinstance(value_cols_str, list) else []
            
            logger.info(f"Getting timeseries for point: lat={latitude}, lon={longitude}")
            logger.info(f"CSV columns: lat={csv_lat_col}, lon={csv_lon_col}, date={csv_date_col}, values={csv_value_cols}")
            
            # Get the scheme to find schema column names
            scheme = self.get_scheme_by_id(scheme_id)
            if not scheme:
                logger.error(f"Scheme {scheme_id} not found")
                return []
            
            all_scheme_columns = scheme.get('required_columns', []) + scheme.get('optional_columns', [])
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get actual table columns
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns_info = cursor.fetchall()
                actual_columns = [col[1] for col in columns_info]
                logger.info(f"Table {table_name} actual columns: {actual_columns}")
                
                # Find schema column names that correspond to CSV columns
                lat_col = None
                lon_col = None
                date_col = None
                value_cols = []
                
                # Find latitude column
                if csv_lat_col in actual_columns:
                    lat_col = csv_lat_col
                else:
                    for schema_col in all_scheme_columns:
                        schema_col_name = schema_col.get('name', '')
                        if schema_col_name in actual_columns and 'lat' in schema_col_name.lower():
                            lat_col = schema_col_name
                            break
                
                # Find longitude column
                if csv_lon_col in actual_columns:
                    lon_col = csv_lon_col
                else:
                    for schema_col in all_scheme_columns:
                        schema_col_name = schema_col.get('name', '')
                        if schema_col_name in actual_columns and ('lon' in schema_col_name.lower() or 'lng' in schema_col_name.lower()):
                            lon_col = schema_col_name
                            break
                
                # Find date column
                csv_date_col_lower = csv_date_col.lower().strip()
                date_col = None
                
                # First check if CSV column name exists in table (case-insensitive)
                for actual_col in actual_columns:
                    if actual_col.lower() == csv_date_col_lower:
                        date_col = actual_col
                        logger.info(f"Found date column: CSV '{csv_date_col}' -> table '{actual_col}'")
                        break
                
                if not date_col:
                    # Try to find by matching schema column names
                    for schema_col in all_scheme_columns:
                        schema_col_name = schema_col.get('name', '')
                        if schema_col_name in actual_columns:
                            # Check if CSV column name matches schema column name (case-insensitive)
                            if csv_date_col_lower == schema_col_name.lower():
                                date_col = schema_col_name
                                logger.info(f"Found date column via schema: CSV '{csv_date_col}' -> schema '{schema_col_name}'")
                                break
                            # Also check if it's a date/time column
                            elif 'date' in schema_col_name.lower() or 'time' in schema_col_name.lower():
                                date_col = schema_col_name
                                logger.info(f"Found date column via date/time match: CSV '{csv_date_col}' -> schema '{schema_col_name}'")
                                break
                
                # Find value columns
                for csv_val_col in csv_value_cols:
                    csv_val_col_lower = csv_val_col.lower().strip()
                    found = False
                    
                    # First check if CSV column name exists in table (case-insensitive)
                    for actual_col in actual_columns:
                        if actual_col.lower() == csv_val_col_lower:
                            value_cols.append(actual_col)
                            found = True
                            logger.info(f"Found value column: CSV '{csv_val_col}' -> table '{actual_col}'")
                            break
                    
                    if not found:
                        # Try to find by matching schema column names (case-insensitive)
                        for schema_col in all_scheme_columns:
                            schema_col_name = schema_col.get('name', '')
                            if schema_col_name in actual_columns:
                                # Check if CSV column name matches schema column name (case-insensitive)
                                if csv_val_col_lower == schema_col_name.lower():
                                    value_cols.append(schema_col_name)
                                    found = True
                                    logger.info(f"Found value column via schema: CSV '{csv_val_col}' -> schema '{schema_col_name}'")
                                    break
                                # Also check if CSV column name is contained in schema column name or vice versa
                                elif csv_val_col_lower in schema_col_name.lower() or schema_col_name.lower() in csv_val_col_lower:
                                    value_cols.append(schema_col_name)
                                    found = True
                                    logger.info(f"Found value column via partial match: CSV '{csv_val_col}' -> schema '{schema_col_name}'")
                                    break
                    
                    if not found:
                        logger.warning(f"Could not find value column '{csv_val_col}' in table or schema")
                
                if not lat_col or not lon_col or not date_col:
                    logger.error(f"Could not find required columns. Lat: {lat_col}, Lon: {lon_col}, Date: {date_col}")
                    return []
                
                if not value_cols:
                    logger.warning(f"No value columns found")
                
                logger.info(f"Using columns: lat={lat_col}, lon={lon_col}, date={date_col}, values={value_cols}")
                
                # Build SELECT statement
                select_cols = [date_col] + value_cols
                select_sql = ', '.join([f'"{col}"' for col in select_cols])
                
                # Get all records for this point (within tolerance)
                query = f'''
                    SELECT {select_sql}
                    FROM "{table_name}"
                    WHERE ABS("{lat_col}" - ?) < ? 
                    AND ABS("{lon_col}" - ?) < ?
                    ORDER BY "{date_col}"
                '''
                
                logger.info(f"Executing query: {query}")
                logger.info(f"Parameters: lat={latitude}, tolerance={tolerance}, lon={longitude}")
                
                cursor.execute(query, (latitude, tolerance, longitude, tolerance))
                rows = cursor.fetchall()
                
                logger.info(f"Found {len(rows)} time series records")
                
                timeseries = []
                for row in rows:
                    record = {
                        'date': row[0]
                    }
                    # Add all value columns
                    for i, val_col in enumerate(value_cols, start=1):
                        record[val_col] = row[i] if i < len(row) else None
                    timeseries.append(record)
                
                logger.info(f"Returning {len(timeseries)} time series records")
                return timeseries
        except Exception as e:
            logger.error(f"Error getting timeseries for point: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []


# Global instance cache (keyed by workspace path)
_db_managers = {}

def get_db_manager(workspace_path=None):
    """Get the database manager instance for a given workspace
    
    Args:
        workspace_path: Optional path to the app workspace. If provided, 
                       the database will be stored in the workspace.
                       If None, uses current working directory.
    
    Returns:
        SQLiteManager instance
    """
    # Use workspace path if provided, otherwise use current directory
    if workspace_path:
        db_path = os.path.join(workspace_path, 'gwapp.db')
        cache_key = db_path
    else:
        db_path = os.path.join(os.getcwd(), 'gwapp.db')
        cache_key = 'default'
    
    # Return cached instance if available
    if cache_key in _db_managers:
        return _db_managers[cache_key]
    
    # Create new instance
    _db_managers[cache_key] = SQLiteManager(db_path=db_path)
    return _db_managers[cache_key]
