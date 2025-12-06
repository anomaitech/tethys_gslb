# GWapp - Groundwater Well Analysis and Visualization Platform

GWapp is a Tethys Platform application designed for managing, analyzing, and visualizing groundwater well data. It provides an intuitive interface for uploading CSV files, mapping columns to schemas, and exploring well locations and time series data on interactive maps.

## Features

### 📊 Data Management
- **Schema Management**: Create and manage custom column mapping schemes for different CSV formats
- **CSV Upload**: Upload groundwater well data in CSV format
- **Basin Management**: Organize data by basins (geographic regions)
- **Column Mapping**: Flexible column mapping system for latitude, longitude, date, and value columns

### 🗺️ Interactive Visualization
- **Interactive Map**: Leaflet-based map showing well locations
- **Point Filtering**: Automatically filters to show only wells with 10+ measurements
- **Time Series Plotting**: Click on any well point to view its time series data
- **Chart Visualization**: Interactive line charts using Chart.js for time series data
- **CSV Export**: Export time series data to CSV format

### 🔧 Settings & Configuration
- **Schema Management Tab**: Create, edit, copy, and delete column schemes
- **Upload File Tab**: Upload and process CSV files
- **Imported Basins Tab**: View and manage all imported basins
- **API Tab**: Interactive API documentation and testing interface

### 🌐 REST API
GWapp provides a comprehensive REST API for programmatic access: This helps for a tethys-dash app

- `GET /api/basins/` - List all basins
- `GET /api/basins/{id}/` - Get basin details
- `GET /api/basins/{id}/wells/` - Get wells for a basin
- `GET /api/basins/{id}/wells/{well_id}/timeseries/` - Get time series for a well
- `GET /api/basins/{id}/statistics/` - Get basin statistics
- `GET /api/basins/{id}/query/` - Query basin data with filters
- `GET /api/schemes/` - List all column schemes
- `POST /api/delete-basin/` - Delete a basin

## Installation

### Prerequisites
- Tethys Platform installed and configured
- Python 3.11+
- SQLite (included with Python)

### Install GWapp

1. **Navigate to the app directory:**
   ```bash
   cd tethysapp-gwapp
   ```

2. **Install the app:**
   ```bash
   tethys install -d
   ```
   
   Or using pip:
   ```bash
   pip install -e .
   ```

3. **Sync the database (if using persistent store):**
   ```bash
   tethys syncstores gwapp
   ```

4. **Start the Tethys server:**
   ```bash
   tethys manage start
   ```

5. **Access the app:**
   Open your browser and navigate to: `http://localhost:8000/apps/gwapp/`

## Usage

### Getting Started

1. **Create a Column Scheme:**
   - Go to **Settings** → **Schema Management** tab
   - Click **New Scheme**
   - Define required and optional columns
   - Save the scheme

2. **Upload Data:**
   - Go to **Settings** → **Upload File** tab
   - Select a CSV file
   - Choose a column scheme
   - Click **Upload**

3. **Map Columns:**
   - After upload, you'll be redirected to the column mapping page
   - Map CSV columns to schema fields
   - Configure basin information:
     - Basin name
     - Basin description
     - Latitude column
     - Longitude column
     - Date column
     - Value column(s)
   - Click **Confirm Mapping**

4. **View Data:**
   - Go to **Home** page
   - The map automatically loads the first basin
   - Click on any well point to view its time series
   - Use the navigation panel to switch between basins

### Managing Basins

- **View Basins**: Settings → Imported Basins tab shows all imported basins
- **Delete Basin**: Click the delete button next to any basin (deletes basin and all its data)
- **View Basin Data**: Click the view button to see basin details

### Using the API

1. Go to **Settings** → **API** tab
2. Browse available endpoints
3. Test endpoints directly from the interface
4. Copy API URLs for use in external applications

## Project Structure

```
tethysapp-gwapp/
├── tethysapp/
│   └── gwapp/
│       ├── app.py              # App configuration and URL routing
│       ├── controllers.py       # Request handlers and business logic
│       ├── sqlite_db.py         # Database operations
│       ├── templates/
│       │   └── gwapp/
│       │       ├── base.html           # Base template
│       │       ├── custom_map.html      # Home page with map
│       │       ├── settings.html        # Settings page
│       │       └── column_mapping.html  # Column mapping interface
│       └── public/
│           ├── css/
│           └── js/
└── README.md
```

## Database

GWapp uses SQLite for data storage. The database is stored in the app workspace directory:
- Location: `workspaces/app_workspace/gwapp.db`
- Tables:
  - `column_schemes`: Column mapping schemes
  - `scheme_columns`: Columns for each scheme
  - `basins`: Basin metadata
  - `basin_{name}`: Dynamic tables for each basin's data

## Technologies Used

- **Backend**: Python, Django, Tethys Platform
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript, jQuery, Bootstrap
- **Mapping**: Leaflet.js
- **Charts**: Chart.js
- **Data Processing**: Pandas

## Features in Detail

### Column Schemes
Column schemes define the structure of your CSV files:
- **Required Columns**: Must be present in the CSV
- **Optional Columns**: May be present
- Each column can have:
  - Name
  - Data type (TEXT, INTEGER, REAL, etc.)
  - Primary key flag
  - Unique constraint
  - Default value

### Basin Configuration
When mapping columns, you configure:
- **Basin Name**: Unique identifier for the basin
- **Plotting Columns**: Which columns to use for:
  - Latitude
  - Longitude
  - Date/Time
  - Value(s) - can select multiple value columns

### Map Features
- **Auto-initialization**: Map automatically loads the first basin on page load
- **Point Filtering**: Only shows wells with 10+ measurements
- **Interactive Markers**: Click markers to view time series
- **Time Series Panel**: Slide-up panel showing charts and data
- **Export Functionality**: Download time series as CSV

## Troubleshooting

### Map Not Showing
- Ensure Leaflet.js is loaded
- Check browser console for JavaScript errors
- Verify basins are imported and have data

### Upload Fails
- Check CSV file format matches selected scheme
- Ensure required columns are present
- Verify file encoding (UTF-8 recommended)

### Points Not Appearing
- Check that wells have at least 10 measurements
- Verify latitude/longitude columns are correctly mapped
- Check database for imported data

## License

This application is part of the Tethys Platform ecosystem.

## Support

For issues or questions, please refer to the Tethys Platform documentation or contact your system administrator.

