# Quick Start Guide

Get the Oracle to Fabric DDL Converter running in 5 minutes!

## Prerequisites Check

Before starting, ensure you have:

- ✅ Python 3.10 or higher installed
- ✅ Node.js 18 or higher installed
- ✅ Oracle Client libraries installed
- ✅ ODBC Driver 18 for SQL Server installed
- ✅ Access to Oracle database
- ✅ Access to Fabric Data Warehouse
- ✅ Anthropic API key

## Installation Steps

### 1. Install All Dependencies (One Command!)

From the project root:

```bash
cd fabric-conversion-app
npm run install-all
```

This will install dependencies for both backend and frontend.

### 2. Configure Environment Variables

#### Backend Configuration

```bash
cd backend
cp .env.example .env
```

Edit `backend/.env` with your credentials:

```env
# Oracle
ORACLE_DB_USER=APPL_DATA_ADMIN
ORACLE_DB_PASSWORD=your_actual_password
ORACLE_DB_DSN=esuedwdbp-cl.csmc.edu:1533/EDWP.WORLD
ORACLE_SCHEMA=APPL_DATA_ADMIN

# Fabric
FABRIC_SERVER=your_workspace.datawarehouse.fabric.microsoft.com
FABRIC_DATABASE=EDW_warehouse_dev
FABRIC_SCHEMA=dbo

# Claude API
ANTHROPIC_API_KEY=sk-ant-api03-your_key_here
```

**How to get Fabric Server:**
1. Go to https://app.fabric.microsoft.com
2. Open your workspace
3. Click on your warehouse
4. Click "SQL connection string" at the top
5. Copy the server address

**How to get Claude API Key:**
1. Go to https://console.anthropic.com/settings/keys
2. Create new key
3. Copy the key (starts with `sk-ant-`)

#### Frontend Configuration

```bash
cd ../frontend
cp .env.example .env
```

Edit `frontend/.env` (usually no changes needed):

```env
VITE_API_URL=http://localhost:5000
```

### 3. Start the Application

From the project root:

```bash
npm run dev
```

This starts both backend (port 5000) and frontend (port 5173).

**Or start individually:**

```bash
# Terminal 1 - Backend
npm run server

# Terminal 2 - Frontend
npm run client
```

### 4. Open the Application

Open your browser to: **http://localhost:5173**

## First-Time Setup in the UI

### Step 1: Configure Connections

1. **Oracle Connection:**
   - Enter username, password, DSN, schema
   - Click "Test Connection"
   - Wait for green checkmark ✓

2. **Fabric Connection:**
   - Enter server and database
   - Click "Test Connection"
   - Azure login window will appear
   - Sign in with your Cedars-Sinai account
   - Wait for green checkmark ✓

3. **Claude API:**
   - Enter your API key
   - Click "Test API Key"
   - Wait for green checkmark ✓

4. Click "Save Configuration"
5. Click "Next: Select Tables"

### Step 2: Select Tables

1. Browse available tables from Oracle
2. Use search to filter
3. Click tables to select (multi-select supported)
4. Click "Extract DDL & Continue"

### Step 3: Review & Convert DDL

1. Review Oracle DDL for each table
2. Click "Convert with Claude AI"
3. Wait for conversion (takes ~10-30 seconds)
4. Review Fabric DDL
5. Edit if needed (inline editor available)
6. Click "Next: Create Tables"

### Step 4: Execute

1. Review tables to be created
2. Click "Create All Tables" for batch creation
   - Or click individual "Create Table" buttons
3. Wait for execution
4. See success/error status for each table

## Troubleshooting

### Backend won't start

**Error: "Module not found"**
```bash
cd backend
pip install -r requirements.txt
```

**Error: "Port 5000 already in use"**
```bash
# In backend/.env, change:
PORT=5001
```

### Frontend won't start

**Error: "Cannot find module"**
```bash
cd frontend
npm install
```

**Error: "Port 5173 already in use"**
```bash
npm run dev -- --port 3000
```

### Oracle Connection Failed

- Verify Oracle client libraries installed
- Check firewall allows connection
- Verify DSN format: `host:port/service`
- Test with SQL Developer first

### Fabric Connection Failed

- Install ODBC Driver 18: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
- Verify Fabric server address from portal
- Ensure you're logged into Azure
- Check network/firewall

### Claude API Failed

- Verify API key format: `sk-ant-api03-...`
- Check API credits at console.anthropic.com
- Ensure no extra spaces in key

## Common Tasks

### Convert a Single Table

1. Go to Step 2: Select Tables
2. Select one table
3. Extract DDL
4. Convert with Claude
5. Create in Fabric

### Convert Multiple Tables (Recommended for large batches)

Use the command-line script for better control:

```bash
cd ..
python oracle_to_fabric_ddl_claude.py --table TABLE1,TABLE2,TABLE3
```

### Review DDL Without Creating

1. Complete Steps 1-3
2. Review converted DDL
3. Don't proceed to Step 4
4. DDL files are saved for later use

### Re-run a Failed Table

In Step 4 (Execute):
- Click individual "Create Table" button for failed tables
- Or edit DDL in Step 3 and retry

## Tips for Success

1. **Start Small**: Test with 1-2 tables first
2. **Review DDL**: Always review converted DDL before creating
3. **Check Logs**: Backend logs are in `backend/logs/app.log`
4. **Save Config**: Click "Save Configuration" to persist settings
5. **Batch Wisely**: For 50+ tables, use command-line script

## Video Tutorial

*(Coming soon)*

## Need Help?

- Check `README.md` for detailed documentation
- Review backend logs: `backend/logs/app.log`
- Contact Data Engineering team

---

**Ready to migrate? Let's go! 🚀**
