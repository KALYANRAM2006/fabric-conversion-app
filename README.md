# Oracle to Fabric DDL Converter

AI-Powered DDL conversion tool with visual interface for migrating Oracle tables to Microsoft Fabric Data Warehouse.

## Features

- 🔌 **Visual Connection Management**: Configure Oracle, Fabric, and Claude API connections through UI
- 📋 **Table Browser**: Browse and select multiple Oracle tables for conversion
- 👁️ **Visual DDL Review**: Side-by-side comparison of Oracle and Fabric DDL
- 🤖 **AI-Powered Conversion**: Uses Claude AI for intelligent DDL conversion
- ✅ **One-Click Execution**: Create tables in Fabric with a single click
- 📊 **Progress Tracking**: Real-time status updates for batch operations

## Architecture

```
fabric-conversion-app/
├── backend/          # Python Flask API
│   ├── app/         # Application code
│   ├── config/      # Configuration management
│   └── logs/        # Application logs
├── frontend/        # React + Vite + Tailwind CSS
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
└── docs/            # Documentation
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Oracle Client libraries
- ODBC Driver 18 for SQL Server
- Anthropic API key

### 1. Install Dependencies

```bash
# Install all dependencies
npm run install-all

# Or manually:
cd backend && pip install -r requirements.txt
cd ../frontend && npm install
```

### 2. Configure Environment

Copy `.env.example` to `.env` in both backend and frontend:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Edit backend/.env with your credentials.

### 3. Start Application

```bash
# Start both backend and frontend
npm run dev

# Or start individually:
npm run server  # Backend on http://localhost:5000
npm run client  # Frontend on http://localhost:5173
```

### 4. Access Application

Open [http://localhost:5173](http://localhost:5173) in your browser.

## Usage Guide

### Step 1: Configure Connections

1. Click **Settings** in the sidebar
2. Enter Oracle connection details
3. Enter Fabric connection details
4. Enter Anthropic API key
5. Click **Test Connection** for each
6. **Save Configuration**

### Step 2: Browse Tables

1. Select your Oracle schema
2. Browse available tables
3. Use search to filter tables
4. Select tables to convert (multi-select supported)

### Step 3: Review Oracle DDL

1. Click **Extract DDL**
2. Review Oracle DDL for each selected table
3. Verify table structure and constraints

### Step 4: Convert with Claude AI

1. Click **Convert to Fabric DDL**
2. Claude AI analyzes and converts each table
3. Review converted Fabric DDL
4. Edit DDL if needed (inline editor)

### Step 5: Create Tables

1. Review side-by-side comparison
2. Click **Create in Fabric** for individual tables
3. Or click **Create All Tables** for batch creation
4. View execution status and results

## Configuration Files

### Backend .env

```env
# Oracle Database
ORACLE_DB_USER=APPL_DATA_ADMIN
ORACLE_DB_PASSWORD=your_password
ORACLE_DB_DSN=host:port/service
ORACLE_SCHEMA=APPL_DATA_ADMIN

# Fabric Data Warehouse
FABRIC_SERVER=workspace.datawarehouse.fabric.microsoft.com
FABRIC_DATABASE=EDW_warehouse_dev
FABRIC_SCHEMA=dbo

# Claude API
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# Application
PORT=5000
LOG_LEVEL=INFO
```

### Frontend .env

```env
VITE_API_URL=http://localhost:5000
```

## API Endpoints

### Connections

- `POST /api/test-oracle` - Test Oracle connection
- `POST /api/test-fabric` - Test Fabric connection
- `POST /api/test-claude` - Test Claude API

### Tables

- `GET /api/tables/:schema` - List tables in schema
- `POST /api/extract-ddl` - Extract Oracle DDL
- `POST /api/convert-ddl` - Convert DDL with Claude
- `POST /api/create-table` - Create table in Fabric

### Configuration

- `GET /api/config` - Get saved configuration
- `POST /api/config` - Save configuration

## Development

### Backend Development

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python run.py
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Build for Production

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm run build
```

## Project Structure

```
fabric-conversion-app/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── routes.py          # API endpoints
│   │   ├── services/
│   │   │   ├── oracle_service.py
│   │   │   ├── fabric_service.py
│   │   │   └── claude_service.py
│   │   └── utils/
│   │       └── ddl_extractor.py
│   ├── config/
│   │   └── config.py          # Configuration management
│   ├── logs/                  # Application logs
│   ├── .env.example
│   ├── requirements.txt
│   └── run.py                 # Entry point
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ConnectionConfig.jsx
│   │   │   ├── TableBrowser.jsx
│   │   │   ├── DDLViewer.jsx
│   │   │   └── ExecutionPanel.jsx
│   │   ├── pages/
│   │   │   └── HomePage.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── public/
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
├── docs/                      # Additional documentation
├── package.json              # Root package.json for scripts
└── README.md
```

## Troubleshooting

### Oracle Connection Issues

- Verify Oracle client libraries are installed
- Check DSN format: `host:port/service`
- Ensure firewall allows connection

### Fabric Connection Issues

- Install ODBC Driver 18 for SQL Server
- Use interactive authentication (will prompt for Azure login)
- Verify Fabric server endpoint from portal

### Claude API Issues

- Get API key from https://console.anthropic.com
- Check API key format starts with `sk-ant-`
- Verify sufficient API credits

### Port Already in Use

```bash
# Backend (default 5000)
PORT=5001 python run.py

# Frontend (default 5173)
npm run dev -- --port 3000
```

## Contributing

This is an internal tool for Cedars-Sinai Health System.

## License

Internal use only - Cedars-Sinai Health System

## Support

For issues or questions, contact the Data Engineering team.
