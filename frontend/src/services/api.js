import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Configuration
export const getConfig = () => api.get('/config')
export const saveConfig = (config) => api.post('/config', config)

// Connection Testing
export const testOracleConnection = (credentials) =>
  api.post('/test-oracle', credentials)

export const testFabricConnection = (credentials) =>
  api.post('/test-fabric', credentials)

export const testClaudeAPI = (apiKey) =>
  api.post('/test-claude', { api_key: apiKey })

// Tables
export const getTables = (schema, oracleCredentials) =>
  api.post(`/tables/${schema}`, oracleCredentials)

export const extractDDL = (payload) =>
  api.post('/extract-ddl', payload)

// DDL Conversion
export const convertDDL = (oracleDDL, claudeApiKey) =>
  api.post('/convert-ddl', {
    oracle_ddl: oracleDDL,
    claude_api_key: claudeApiKey
  })

// Table Creation
export const createTable = (payload) =>
  api.post('/create-table', payload)

export const createTablesBatch = (payload) =>
  api.post('/create-tables-batch', payload)

export default api
