import React, { useState, useEffect } from 'react'
import { CheckCircle, XCircle, Loader, ChevronRight, Database, Cloud, Bot, ChevronDown } from 'lucide-react'
import * as api from '../services/api'

function ConnectionConfig({ config, setConfig, onNext }) {
  const [loading, setLoading] = useState({})
  const [testResults, setTestResults] = useState({})
  const [saveMessage, setSaveMessage] = useState('')
  const [availableDatabases, setAvailableDatabases] = useState([])
  const [selectedDatabase, setSelectedDatabase] = useState('')
  const [usePreset, setUsePreset] = useState(true)
  const [fabricSchemas, setFabricSchemas] = useState(['APPL_STAR', 'caboodle', 'caboodle_staging', 'config', 'dbo', 'idmc_cdv'])
  const [loadingSchemas, setLoadingSchemas] = useState(false)

  // Load saved config and available databases on mount
  useEffect(() => {
    loadConfig()
    loadDatabases()
  }, [])

  const loadDatabases = async () => {
    try {
      const response = await api.getDatabases()
      if (response.data?.databases) {
        setAvailableDatabases(response.data.databases)
      }
    } catch (error) {
      console.error('Error loading databases:', error)
    }
  }

  const handleDatabaseSelect = async (dbKey) => {
    setSelectedDatabase(dbKey)
    setTestResults(prev => ({ ...prev, oracle: null }))

    if (!dbKey) return

    const db = availableDatabases.find(d => d.key === dbKey)
    if (db) {
      setConfig(prev => ({
        ...prev,
        oracle: {
          ...prev.oracle,
          user: db.user,
          dsn: db.dsn,
          schema: db.schema,
          database_key: db.key,
        }
      }))
    }
  }

  const loadConfig = async () => {
    try {
      const response = await api.getConfig()
      if (response.data) {
        const savedConfig = response.data
        setConfig({
          oracle: savedConfig.oracle || config.oracle,
          fabric: savedConfig.fabric || config.fabric,
          claudeApiKey: savedConfig.hasClaudeKey ? '••••••••' : ''
        })
      }
    } catch (error) {
      console.error('Error loading config:', error)
    }
  }

  const handleInputChange = (section, field, value) => {
    setConfig(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }))
  }

  const testConnection = async (type) => {
    setLoading(prev => ({ ...prev, [type]: true }))
    setTestResults(prev => ({ ...prev, [type]: null }))

    try {
      let response
      if (type === 'oracle') {
        if (usePreset && selectedDatabase) {
          response = await api.testOraclePreset(selectedDatabase)
        } else {
          response = await api.testOracleConnection({
            user: config.oracle.user,
            password: config.oracle.password,
            dsn: config.oracle.dsn
          })
        }
      } else if (type === 'fabric') {
        response = await api.testFabricConnection({
          server: config.fabric.server,
          database: config.fabric.database
        })
        // If connection is successful, load schemas
        if (response.data?.success) {
          loadFabricSchemas()
        }
      } else if (type === 'claude') {
        response = await api.testClaudeAPI(config.claudeApiKey)
      }

      setTestResults(prev => ({
        ...prev,
        [type]: { success: true, message: response.data.message }
      }))
    } catch (error) {
      setTestResults(prev => ({
        ...prev,
        [type]: {
          success: false,
          message: error.response?.data?.error || error.message
        }
      }))
    } finally {
      setLoading(prev => ({ ...prev, [type]: false }))
    }
  }

  const loadFabricSchemas = async () => {
    setLoadingSchemas(true)
    try {
      const response = await api.getFabricSchemas(
        config.fabric.server,
        config.fabric.database
      )
      if (response.data?.schemas) {
        setFabricSchemas(response.data.schemas)
        // If dbo exists in the list and current schema is empty, default to dbo
        if (!config.fabric.schema && response.data.schemas.includes('dbo')) {
          handleInputChange('fabric', 'schema', 'dbo')
        }
      }
    } catch (error) {
      console.error('Error loading Fabric schemas:', error)
    } finally {
      setLoadingSchemas(false)
    }
  }

  const handleSaveConfig = async () => {
    try {
      await api.saveConfig({
        oracle: config.oracle,
        fabric: config.fabric,
        claude: { api_key: config.claudeApiKey }
      })
      setSaveMessage('Configuration saved successfully!')
      setTimeout(() => setSaveMessage(''), 3000)
    } catch (error) {
      setSaveMessage('Error saving configuration')
    }
  }

  const canProceed = () => {
    return (
      testResults.oracle?.success &&
      testResults.fabric?.success &&
      testResults.claude?.success
    )
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Configure Connections
        </h2>
        <p className="text-gray-600">
          Set up your Oracle, Fabric, and Claude AI connections
        </p>
      </div>

      {/* Oracle Configuration */}
      <div className="border rounded-lg p-6 bg-gray-50">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <Database className="w-6 h-6 text-red-600 mr-2" />
            <h3 className="text-lg font-semibold">Oracle Database</h3>
          </div>
          <div className="flex items-center space-x-2">
            <label className="text-sm text-gray-600">
              <input
                type="checkbox"
                checked={usePreset}
                onChange={(e) => {
                  setUsePreset(e.target.checked)
                  setTestResults(prev => ({ ...prev, oracle: null }))
                }}
                className="mr-1"
              />
              Use preconfigured database
            </label>
          </div>
        </div>

        {usePreset ? (
          /* Preset Database Picker */
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Select Database
              </label>
              <div className="relative">
                <select
                  value={selectedDatabase}
                  onChange={(e) => handleDatabaseSelect(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white appearance-none pr-10"
                >
                  <option value="">-- Select a database --</option>
                  {availableDatabases.map(db => (
                    <option key={db.key} value={db.key}>{db.label}</option>
                  ))}
                </select>
                <ChevronDown className="w-4 h-4 text-gray-500 absolute right-3 top-3 pointer-events-none" />
              </div>
            </div>

            {selectedDatabase && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-white p-4 rounded-md border">
                <div>
                  <span className="text-xs font-medium text-gray-500 uppercase">User</span>
                  <p className="text-sm text-gray-900 mt-1">{config.oracle.user}</p>
                </div>
                <div>
                  <span className="text-xs font-medium text-gray-500 uppercase">DSN</span>
                  <p className="text-sm text-gray-900 mt-1 break-all">{config.oracle.dsn}</p>
                </div>
                <div>
                  <span className="text-xs font-medium text-gray-500 uppercase">Schema</span>
                  <input
                    type="text"
                    value={config.oracle.schema}
                    onChange={(e) => handleInputChange('oracle', 'schema', e.target.value)}
                    className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 mt-1"
                  />
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Manual Entry */
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Username
              </label>
              <input
                type="text"
                value={config.oracle.user}
                onChange={(e) => handleInputChange('oracle', 'user', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="APPL_DATA_ADMIN"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <input
                type="password"
                value={config.oracle.password}
                onChange={(e) => handleInputChange('oracle', 'password', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="••••••••"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                DSN (host:port/service)
              </label>
              <input
                type="text"
                value={config.oracle.dsn}
                onChange={(e) => handleInputChange('oracle', 'dsn', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="host:1521/service"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Schema
              </label>
              <input
                type="text"
                value={config.oracle.schema}
                onChange={(e) => handleInputChange('oracle', 'schema', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="APPL_DATA_ADMIN"
              />
            </div>
          </div>
        )}

        <div className="mt-4 flex items-center justify-between">
          <button
            onClick={() => testConnection('oracle')}
            disabled={loading.oracle}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center"
          >
            {loading.oracle ? (
              <>
                <Loader className="w-4 h-4 mr-2 animate-spin" />
                Testing...
              </>
            ) : (
              'Test Connection'
            )}
          </button>

          {testResults.oracle && (
            <div className={`flex items-center ${testResults.oracle.success ? 'text-green-600' : 'text-red-600'}`}>
              {testResults.oracle.success ? (
                <CheckCircle className="w-5 h-5 mr-2" />
              ) : (
                <XCircle className="w-5 h-5 mr-2" />
              )}
              <span className="text-sm">{testResults.oracle.message}</span>
            </div>
          )}
        </div>
      </div>

      {/* Fabric Configuration */}
      <div className="border rounded-lg p-6 bg-gray-50">
        <div className="flex items-center mb-4">
          <Cloud className="w-6 h-6 text-blue-600 mr-2" />
          <h3 className="text-lg font-semibold">Fabric Data Warehouse</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Server
            </label>
            <input
              type="text"
              value={config.fabric.server}
              onChange={(e) => handleInputChange('fabric', 'server', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="workspace.datawarehouse.fabric.microsoft.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Database
            </label>
            <input
              type="text"
              value={config.fabric.database}
              onChange={(e) => handleInputChange('fabric', 'database', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="EDW_warehouse_dev"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Target Schema
            </label>
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <select
                  value={config.fabric.schema}
                  onChange={(e) => handleInputChange('fabric', 'schema', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white appearance-none pr-10"
                >
                  <option value="">-- Select a schema --</option>
                  {fabricSchemas.map(schema => (
                    <option key={schema} value={schema}>{schema}</option>
                  ))}
                </select>
                <ChevronDown className="w-4 h-4 text-gray-500 absolute right-3 top-3 pointer-events-none" />
              </div>
              <button
                onClick={loadFabricSchemas}
                disabled={loadingSchemas || !config.fabric.server || !config.fabric.database}
                className="px-3 py-2 text-sm bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 disabled:opacity-50 flex items-center whitespace-nowrap"
                title="Load schemas from Fabric warehouse"
              >
                {loadingSchemas ? (
                  <Loader className="w-4 h-4 animate-spin" />
                ) : (
                  'Refresh'
                )}
              </button>
            </div>
          </div>
        </div>

        <div className="mt-4 flex items-center justify-between">
          <button
            onClick={() => testConnection('fabric')}
            disabled={loading.fabric}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center"
          >
            {loading.fabric ? (
              <>
                <Loader className="w-4 h-4 mr-2 animate-spin" />
                Testing...
              </>
            ) : (
              'Test Connection'
            )}
          </button>

          {testResults.fabric && (
            <div className={`flex items-center ${testResults.fabric.success ? 'text-green-600' : 'text-red-600'}`}>
              {testResults.fabric.success ? (
                <CheckCircle className="w-5 h-5 mr-2" />
              ) : (
                <XCircle className="w-5 h-5 mr-2" />
              )}
              <span className="text-sm">{testResults.fabric.message}</span>
            </div>
          )}
        </div>
      </div>

      {/* Claude API Configuration */}
      <div className="border rounded-lg p-6 bg-gray-50">
        <div className="flex items-center mb-4">
          <Bot className="w-6 h-6 text-purple-600 mr-2" />
          <h3 className="text-lg font-semibold">Claude API</h3>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            API Key
          </label>
          <input
            type="password"
            value={config.claudeApiKey}
            onChange={(e) => setConfig(prev => ({ ...prev, claudeApiKey: e.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="sk-ant-api03-..."
          />
          <p className="text-xs text-gray-500 mt-1">
            Get your API key from{' '}
            <a
              href="https://console.anthropic.com/settings/keys"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              console.anthropic.com
            </a>
          </p>
        </div>

        <div className="mt-4 flex items-center justify-between">
          <button
            onClick={() => testConnection('claude')}
            disabled={loading.claude}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center"
          >
            {loading.claude ? (
              <>
                <Loader className="w-4 h-4 mr-2 animate-spin" />
                Testing...
              </>
            ) : (
              'Test API Key'
            )}
          </button>

          {testResults.claude && (
            <div className={`flex items-center ${testResults.claude.success ? 'text-green-600' : 'text-red-600'}`}>
              {testResults.claude.success ? (
                <CheckCircle className="w-5 h-5 mr-2" />
              ) : (
                <XCircle className="w-5 h-5 mr-2" />
              )}
              <span className="text-sm">{testResults.claude.message}</span>
            </div>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-between pt-6 border-t">
        <button
          onClick={handleSaveConfig}
          className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
        >
          Save Configuration
        </button>

        {saveMessage && (
          <span className="text-sm text-green-600">{saveMessage}</span>
        )}

        <button
          onClick={onNext}
          disabled={!canProceed()}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
        >
          Next: Select Tables
          <ChevronRight className="w-4 h-4 ml-2" />
        </button>
      </div>
    </div>
  )
}

export default ConnectionConfig
