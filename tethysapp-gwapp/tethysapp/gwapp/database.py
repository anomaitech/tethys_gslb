"""
Database utilities for GWapp
"""
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from .model import ColumnScheme, SchemeColumn, DynamicDataTable
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manager class for database operations
    """
    
    def __init__(self, database_engine):
        self.engine = database_engine
        Session = sessionmaker(bind=database_engine)
        self.session = Session()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
        self.session.close()
    
    def get_all_schemes(self):
        """Get all column schemes"""
        try:
            schemes = self.session.query(ColumnScheme).order_by(ColumnScheme.name).all()
            return [self.scheme_to_dict(scheme) for scheme in schemes]
        except Exception as e:
            logger.error(f"Error getting schemes: {e}")
            return []
    
    def get_scheme_by_id(self, scheme_id):
        """Get a specific scheme by ID"""
        try:
            scheme = self.session.query(ColumnScheme).filter_by(id=scheme_id).first()
            return self.scheme_to_dict(scheme) if scheme else None
        except Exception as e:
            logger.error(f"Error getting scheme {scheme_id}: {e}")
            return None
    
    def get_scheme_by_name(self, name):
        """Get a specific scheme by name"""
        try:
            scheme = self.session.query(ColumnScheme).filter_by(name=name).first()
            return self.scheme_to_dict(scheme) if scheme else None
        except Exception as e:
            logger.error(f"Error getting scheme {name}: {e}")
            return None
    
    def create_scheme(self, name, description='', columns_data=None):
        """Create a new column scheme"""
        try:
            # Check if scheme with this name already exists
            existing = self.session.query(ColumnScheme).filter_by(name=name).first()
            if existing:
                raise ValueError(f"Scheme with name '{name}' already exists")
            
            scheme = ColumnScheme(
                name=name,
                description=description,
                is_active=True
            )
            self.session.add(scheme)
            self.session.flush()  # Get the ID
            
            # Add columns if provided
            if columns_data:
                self.add_columns_to_scheme(scheme.id, columns_data)
            
            self.session.commit()
            
            # Create the actual database table
            self.create_scheme_table(scheme)
            
            return self.scheme_to_dict(scheme)
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating scheme: {e}")
            raise e
    
    def update_scheme(self, scheme_id, name=None, description=None, columns_data=None):
        """Update an existing scheme"""
        try:
            scheme = self.session.query(ColumnScheme).filter_by(id=scheme_id).first()
            if not scheme:
                raise ValueError(f"Scheme with ID {scheme_id} not found")
            
            old_table_name = scheme.table_name
            
            if name and name != scheme.name:
                # Check if new name already exists
                existing = self.session.query(ColumnScheme).filter_by(name=name).first()
                if existing and existing.id != scheme_id:
                    raise ValueError(f"Scheme with name '{name}' already exists")
                scheme.name = name
            
            if description is not None:
                scheme.description = description
            
            # Update columns if provided
            if columns_data is not None:
                # Remove existing columns
                self.session.query(SchemeColumn).filter_by(scheme_id=scheme_id).delete()
                # Add new columns
                self.add_columns_to_scheme(scheme_id, columns_data)
            
            self.session.commit()
            
            # Update the database table if name changed or columns changed
            new_table_name = scheme.table_name
            if old_table_name != new_table_name or columns_data is not None:
                self.drop_scheme_table(old_table_name)
                self.create_scheme_table(scheme)
            
            return self.scheme_to_dict(scheme)
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating scheme: {e}")
            raise e
    
    def delete_scheme(self, scheme_id):
        """Delete a scheme and its associated table"""
        try:
            scheme = self.session.query(ColumnScheme).filter_by(id=scheme_id).first()
            if not scheme:
                raise ValueError(f"Scheme with ID {scheme_id} not found")
            
            table_name = scheme.table_name
            
            # Delete from database
            self.session.delete(scheme)
            self.session.commit()
            
            # Drop the actual table
            self.drop_scheme_table(table_name)
            
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting scheme: {e}")
            raise e
    
    def add_columns_to_scheme(self, scheme_id, columns_data):
        """Add columns to a scheme"""
        for col_data in columns_data:
            column = SchemeColumn(
                scheme_id=scheme_id,
                name=col_data.get('name'),
                description=col_data.get('description', ''),
                column_type=col_data.get('column_type', 'required'),
                data_type=col_data.get('data_type', 'TEXT'),
                is_primary_key=col_data.get('is_primary_key', False),
                is_unique=col_data.get('is_unique', False),
                max_length=col_data.get('max_length'),
                default_value=col_data.get('default_value', ''),
                order=col_data.get('order', 0)
            )
            self.session.add(column)
    
    def create_scheme_table(self, scheme):
        """Create a database table based on the scheme"""
        try:
            table_name = f"data_{scheme.table_name}"
            
            # Build CREATE TABLE statement
            columns_sql = []
            for column in sorted(scheme.columns, key=lambda x: x.order):
                columns_sql.append(column.sql_definition)
            
            if not columns_sql:
                logger.warning(f"No columns defined for scheme {scheme.name}, skipping table creation")
                return
            
            create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns_sql)})"
            
            # Execute the CREATE TABLE statement
            with self.engine.connect() as conn:
                conn.execute(text(create_sql))
                conn.commit()
            
            # Record the table in our tracking system
            existing_table = self.session.query(DynamicDataTable).filter_by(table_name=table_name).first()
            if not existing_table:
                data_table = DynamicDataTable(
                    scheme_id=scheme.id,
                    table_name=table_name,
                    record_count=0
                )
                self.session.add(data_table)
                self.session.commit()
            
            logger.info(f"Created table {table_name} for scheme {scheme.name}")
            
        except Exception as e:
            logger.error(f"Error creating table for scheme {scheme.name}: {e}")
            raise e
    
    def drop_scheme_table(self, table_name):
        """Drop a scheme's data table"""
        try:
            full_table_name = f"data_{table_name}" if not table_name.startswith('data_') else table_name
            
            with self.engine.connect() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS {full_table_name}"))
                conn.commit()
            
            # Remove from tracking
            self.session.query(DynamicDataTable).filter_by(table_name=full_table_name).delete()
            self.session.commit()
            
            logger.info(f"Dropped table {full_table_name}")
            
        except Exception as e:
            logger.error(f"Error dropping table {table_name}: {e}")
    
    def scheme_to_dict(self, scheme):
        """Convert a scheme object to dictionary format"""
        if not scheme:
            return None
        
        required_columns = []
        optional_columns = []
        
        for column in sorted(scheme.columns, key=lambda x: x.order):
            col_dict = {
                'name': column.name,
                'description': column.description,
                'data_type': column.data_type,
                'is_primary_key': column.is_primary_key,
                'is_unique': column.is_unique,
                'max_length': column.max_length,
                'default_value': column.default_value,
                'order': column.order
            }
            
            if column.column_type == 'required':
                required_columns.append(col_dict)
            else:
                optional_columns.append(col_dict)
        
        return {
            'id': scheme.id,
            'name': scheme.name,
            'description': scheme.description,
            'required_columns': required_columns,
            'optional_columns': optional_columns,
            'table_name': scheme.table_name,
            'created_at': scheme.created_at.isoformat() if scheme.created_at else None,
            'updated_at': scheme.updated_at.isoformat() if scheme.updated_at else None,
            'is_active': scheme.is_active
        }
    
    def insert_data_into_scheme_table(self, scheme_id, data_rows):
        """Insert data rows into a scheme's table"""
        try:
            scheme = self.session.query(ColumnScheme).filter_by(id=scheme_id).first()
            if not scheme:
                raise ValueError(f"Scheme with ID {scheme_id} not found")
            
            table_name = f"data_{scheme.table_name}"
            
            if not data_rows:
                return 0
            
            # Get column names from the scheme
            column_names = [col.name for col in sorted(scheme.columns, key=lambda x: x.order)]
            
            # Build INSERT statement
            placeholders = ', '.join([f":{col}" for col in column_names])
            insert_sql = f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({placeholders})"
            
            # Execute inserts
            with self.engine.connect() as conn:
                result = conn.execute(text(insert_sql), data_rows)
                conn.commit()
                
                # Update record count
                count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                new_count = count_result.scalar()
                
                # Update tracking table
                data_table = self.session.query(DynamicDataTable).filter_by(table_name=table_name).first()
                if data_table:
                    data_table.record_count = new_count
                    self.session.commit()
                
                return len(data_rows)
            
        except Exception as e:
            logger.error(f"Error inserting data into scheme table: {e}")
            raise e
    
    def get_scheme_data(self, scheme_id, limit=None, offset=None):
        """Get data from a scheme's table"""
        try:
            scheme = self.session.query(ColumnScheme).filter_by(id=scheme_id).first()
            if not scheme:
                raise ValueError(f"Scheme with ID {scheme_id} not found")
            
            table_name = f"data_{scheme.table_name}"
            
            sql = f"SELECT * FROM {table_name}"
            if limit:
                sql += f" LIMIT {limit}"
            if offset:
                sql += f" OFFSET {offset}"
            
            with self.engine.connect() as conn:
                result = conn.execute(text(sql))
                rows = result.fetchall()
                columns = result.keys()
                
                return [dict(zip(columns, row)) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting scheme data: {e}")
            return []
