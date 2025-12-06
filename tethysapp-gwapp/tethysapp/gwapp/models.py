from django.db import models
from django.contrib.auth.models import User


class ColumnScheme(models.Model):
    """
    Model to store column mapping schemes
    """
    name = models.CharField(max_length=100, unique=True, help_text="Unique name for the schema")
    description = models.TextField(blank=True, help_text="Description of the schema")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, help_text="Whether this schema is currently active")
    
    class Meta:
        ordering = ['name']
        verbose_name = "Column Scheme"
        verbose_name_plural = "Column Schemes"
    
    def __str__(self):
        return self.name
    
    @property
    def table_name(self):
        """Generate a valid SQL table name from the scheme name"""
        # Replace spaces and special characters with underscores, convert to lowercase
        import re
        table_name = re.sub(r'[^a-zA-Z0-9_]', '_', self.name.lower())
        table_name = re.sub(r'_+', '_', table_name)  # Replace multiple underscores with single
        table_name = table_name.strip('_')  # Remove leading/trailing underscores
        
        # Ensure it starts with a letter
        if table_name and not table_name[0].isalpha():
            table_name = f"scheme_{table_name}"
        
        return table_name or "default_scheme"


class SchemeColumn(models.Model):
    """
    Model to store individual columns for each scheme
    """
    COLUMN_TYPES = [
        ('required', 'Required'),
        ('optional', 'Optional'),
    ]
    
    DATA_TYPES = [
        ('TEXT', 'Text'),
        ('INTEGER', 'Integer'),
        ('REAL', 'Real Number'),
        ('DATE', 'Date'),
        ('DATETIME', 'DateTime'),
        ('BOOLEAN', 'Boolean'),
    ]
    
    scheme = models.ForeignKey(ColumnScheme, on_delete=models.CASCADE, related_name='columns')
    name = models.CharField(max_length=100, help_text="Column name")
    description = models.TextField(blank=True, help_text="Column description")
    column_type = models.CharField(max_length=10, choices=COLUMN_TYPES, default='required')
    data_type = models.CharField(max_length=10, choices=DATA_TYPES, default='TEXT')
    is_primary_key = models.BooleanField(default=False, help_text="Is this column a primary key")
    is_unique = models.BooleanField(default=False, help_text="Should this column have unique values")
    max_length = models.IntegerField(null=True, blank=True, help_text="Maximum length for text fields")
    default_value = models.TextField(blank=True, help_text="Default value for the column")
    order = models.PositiveIntegerField(default=0, help_text="Order of column in the table")
    
    class Meta:
        ordering = ['scheme', 'order', 'name']
        unique_together = ['scheme', 'name']
        verbose_name = "Scheme Column"
        verbose_name_plural = "Scheme Columns"
    
    def __str__(self):
        return f"{self.scheme.name}.{self.name}"
    
    @property
    def sql_definition(self):
        """Generate SQL column definition"""
        sql_type = self.data_type
        
        # Add length for TEXT fields
        if self.data_type == 'TEXT' and self.max_length:
            sql_type = f"VARCHAR({self.max_length})"
        
        # Build full definition
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


class DynamicDataTable(models.Model):
    """
    Model to track dynamically created data tables
    """
    scheme = models.ForeignKey(ColumnScheme, on_delete=models.CASCADE, related_name='data_tables')
    table_name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    record_count = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "Dynamic Data Table"
        verbose_name_plural = "Dynamic Data Tables"
    
    def __str__(self):
        return f"Table: {self.table_name} (Scheme: {self.scheme.name})"
