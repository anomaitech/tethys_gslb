"""
Database model initialization for GWapp
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()


def init_gwapp_db(engine, first_time):
    """
    Initialize the GWapp database.
    """
    Base.metadata.create_all(engine)
    
    if first_time:
        # Add default column scheme
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Create default scheme
            default_scheme = ColumnScheme(
                name='Default Groundwater Scheme',
                description='Standard groundwater monitoring data columns',
                is_active=True
            )
            session.add(default_scheme)
            session.flush()  # Get the ID
            
            # Add default required columns
            required_columns = [
                {'name': 'well_id', 'description': 'Unique well identifier', 'data_type': 'TEXT', 'is_primary_key': True, 'order': 1},
                {'name': 'latitude', 'description': 'Latitude coordinates', 'data_type': 'REAL', 'order': 2},
                {'name': 'longitude', 'description': 'Longitude coordinates', 'data_type': 'REAL', 'order': 3},
                {'name': 'date', 'description': 'Measurement date', 'data_type': 'DATE', 'order': 4},
                {'name': 'water_table_elevation', 'description': 'Water table elevation', 'data_type': 'REAL', 'order': 5}
            ]
            
            for col_data in required_columns:
                column = SchemeColumn(
                    scheme_id=default_scheme.id,
                    column_type='required',
                    **col_data
                )
                session.add(column)
            
            # Add default optional columns
            optional_columns = [
                {'name': 'temperature', 'description': 'Water temperature', 'data_type': 'REAL', 'order': 6},
                {'name': 'pH', 'description': 'pH value', 'data_type': 'REAL', 'order': 7},
                {'name': 'conductivity', 'description': 'Electrical conductivity', 'data_type': 'REAL', 'order': 8}
            ]
            
            for col_data in optional_columns:
                column = SchemeColumn(
                    scheme_id=default_scheme.id,
                    column_type='optional',
                    **col_data
                )
                session.add(column)
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            print(f"Error initializing default data: {e}")
        finally:
            session.close()


class ColumnScheme(Base):
    """
    SQLAlchemy model for column mapping schemes
    """
    __tablename__ = 'column_schemes'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationship with columns
    columns = relationship("SchemeColumn", back_populates="scheme", cascade="all, delete-orphan")
    data_tables = relationship("DynamicDataTable", back_populates="scheme", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ColumnScheme(name='{self.name}')>"
    
    @property
    def table_name(self):
        """Generate a valid SQL table name from the scheme name"""
        import re
        table_name = re.sub(r'[^a-zA-Z0-9_]', '_', self.name.lower())
        table_name = re.sub(r'_+', '_', table_name)
        table_name = table_name.strip('_')
        
        if table_name and not table_name[0].isalpha():
            table_name = f"scheme_{table_name}"
        
        return table_name or "default_scheme"


class SchemeColumn(Base):
    """
    SQLAlchemy model for individual columns in schemes
    """
    __tablename__ = 'scheme_columns'
    
    id = Column(Integer, primary_key=True)
    scheme_id = Column(Integer, ForeignKey('column_schemes.id'), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    column_type = Column(String(10), nullable=False, default='required')  # 'required' or 'optional'
    data_type = Column(String(10), nullable=False, default='TEXT')  # 'TEXT', 'INTEGER', 'REAL', 'DATE', 'DATETIME', 'BOOLEAN'
    is_primary_key = Column(Boolean, default=False)
    is_unique = Column(Boolean, default=False)
    max_length = Column(Integer)
    default_value = Column(Text)
    order = Column(Integer, default=0)
    
    # Relationship with scheme
    scheme = relationship("ColumnScheme", back_populates="columns")
    
    # Ensure unique column names within a scheme
    __table_args__ = (UniqueConstraint('scheme_id', 'name', name='unique_column_per_scheme'),)
    
    def __repr__(self):
        return f"<SchemeColumn(scheme='{self.scheme.name}', name='{self.name}')>"
    
    @property
    def sql_definition(self):
        """Generate SQL column definition"""
        sql_type = self.data_type
        
        if self.data_type == 'TEXT' and self.max_length:
            sql_type = f"VARCHAR({self.max_length})"
        
        definition = f"{self.name} {sql_type}"
        
        if self.is_primary_key:
            definition += " PRIMARY KEY"
        elif self.column_type == 'required':
            definition += " NOT NULL"
        
        if self.is_unique and not self.is_primary_key:
            definition += " UNIQUE"
        
        if self.default_value:
            if self.data_type in ['TEXT', 'DATE', 'DATETIME']:
                definition += f" DEFAULT '{self.default_value}'"
            else:
                definition += f" DEFAULT {self.default_value}"
        
        return definition


class DynamicDataTable(Base):
    """
    SQLAlchemy model to track dynamically created data tables
    """
    __tablename__ = 'dynamic_data_tables'
    
    id = Column(Integer, primary_key=True)
    scheme_id = Column(Integer, ForeignKey('column_schemes.id'), nullable=False)
    table_name = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    record_count = Column(Integer, default=0)
    
    # Relationship with scheme
    scheme = relationship("ColumnScheme", back_populates="data_tables")
    
    def __repr__(self):
        return f"<DynamicDataTable(table_name='{self.table_name}', scheme='{self.scheme.name}')>"
