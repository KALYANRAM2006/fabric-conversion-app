import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Health Check
export const checkHealth = () => api.get('/health', { timeout: 3000 })

// Configuration
export const getConfig = () => api.get('/config')
export const saveConfig = (config) => api.post('/config', config)

// Database Registry
export const getDatabases = () => api.get('/databases')
export const getDatabaseCredentials = (dbKey) => api.get(`/databases/${dbKey}/credentials`)
export const testOraclePreset = (databaseKey) =>
  api.post('/test-oracle-preset', { database_key: databaseKey })

// Connection Testing
export const testOracleConnection = (credentials) =>
  api.post('/test-oracle', credentials)

export const testFabricConnection = (credentials) =>
  api.post('/test-fabric', credentials)

export const getFabricSchemas = (server, database) =>
  api.post('/fabric-schemas', { server, database })

export const testClaudeAPI = (apiKey) =>
  api.post('/test-claude', { api_key: apiKey })

// Tables
export const getTables = (schema, oracleCredentials) =>
  api.post(`/tables/${schema}`, oracleCredentials)

export const getTablesPreset = (schema, databaseKey) =>
  api.post(`/tables/${schema}`, { database_key: databaseKey })

export const extractDDL = (payload) =>
  api.post('/extract-ddl', payload)

// DDL Conversion
export const convertDDL = (oracleDDL, claudeApiKey, customInstructions) =>
  api.post('/convert-ddl', {
    oracle_ddl: oracleDDL,
    claude_api_key: claudeApiKey,
    custom_instructions: customInstructions
  })

// Table Creation
export const createTable = (payload) =>
  api.post('/create-table', payload)

export const createTablesBatch = (payload) =>
  api.post('/create-tables-batch', payload)

// Column Comparison
export const compareColumns = (payload) =>
  api.post('/compare-columns', payload)

export default api
