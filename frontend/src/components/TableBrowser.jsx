import React, { useState, useEffect } from 'react'
import { Search, ChevronLeft, ChevronRight, Loader, Database, CheckSquare, Square } from 'lucide-react'
import * as api from '../services/api'

function TableBrowser({ config, selectedTables, setSelectedTables, oracleDDL, setOracleDDL, onNext, onBack }) {
  const [tables, setTables] = useState([])
  const [loading, setLoading] = useState(false)
  const [extracting, setExtracting] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    loadTables()
  }, [])

  const loadTables = async () => {
    setLoading(true)
    setError('')

    try {
      let response
      if (config.oracle.database_key) {
        response = await api.getTablesPreset(config.oracle.schema, config.oracle.database_key)
      } else {
        response = await api.getTables(config.oracle.schema, {
          user: config.oracle.user,
          password: config.oracle.password,
          dsn: config.oracle.dsn
        })
      }

      setTables(response.data.tables || [])
    } catch (err) {
      setError(err.response?.data?.error || err.message)
    } finally {
      setLoading(false)
    }
  }

  const filteredTables = tables.filter(table =>
    table.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const toggleTable = (tableName) => {
    if (selectedTables.includes(tableName)) {
      setSelectedTables(selectedTables.filter(t => t !== tableName))
    } else {
      setSelectedTables([...selectedTables, tableName])
    }
  }

  const toggleAll = () => {
    if (selectedTables.length === filteredTables.length) {
      setSelectedTables([])
    } else {
      setSelectedTables(filteredTables.map(t => t.name))
    }
  }

  const handleExtractDDL = async () => {
    if (selectedTables.length === 0) {
      setError('Please select at least one table')
      return
    }

    setExtracting(true)
    setError('')

    try {
      const payload = {
        schema: config.oracle.schema,
        tables: selectedTables
      }
      if (config.oracle.database_key) {
        payload.database_key = config.oracle.database_key
      } else {
        payload.oracle = {
          user: config.oracle.user,
          password: config.oracle.password,
          dsn: config.oracle.dsn
        }
      }
      const response = await api.extractDDL(payload)

      setOracleDDL(response.data.ddl || {})
      onNext()
    } catch (err) {
      setError(err.response?.data?.error || err.message)
    } finally {
      setExtracting(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Select Tables to Convert
        </h2>
        <p className="text-gray-600">
          Choose tables from <span className="font-semibold">{config.oracle.schema}</span> schema
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader className="w-8 h-8 animate-spin text-blue-600" />
          <span className="ml-3 text-gray-600">Loading tables...</span>
        </div>
      ) : (
        <>
          {/* Search and Stats */}
          <div className="flex items-center justify-between">
            <div className="flex-1 max-w-md">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search tables..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="text-sm text-gray-600">
              <span className="font-semibold">{selectedTables.length}</span> of{' '}
              <span className="font-semibold">{filteredTables.length}</span> tables selected
            </div>
          </div>

          {/* Table List */}
          <div className="border rounded-lg overflow-hidden">
            <div className="bg-gray-50 px-4 py-3 border-b flex items-center">
              <button
                onClick={toggleAll}
                className="flex items-center text-sm font-medium text-gray-700 hover:text-gray-900"
              >
                {selectedTables.length === filteredTables.length ? (
                  <CheckSquare className="w-5 h-5 mr-2 text-blue-600" />
                ) : (
                  <Square className="w-5 h-5 mr-2" />
                )}
                Select All
              </button>
            </div>

            <div className="max-h-96 overflow-y-auto">
              {filteredTables.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  No tables found
                </div>
              ) : (
                <div className="divide-y">
                  {filteredTables.map((table) => (
                    <div
                      key={table.name}
                      onClick={() => toggleTable(table.name)}
                      className="px-4 py-3 hover:bg-gray-50 cursor-pointer flex items-center justify-between"
                    >
                      <div className="flex items-center flex-1">
                        {selectedTables.includes(table.name) ? (
                          <CheckSquare className="w-5 h-5 mr-3 text-blue-600" />
                        ) : (
                          <Square className="w-5 h-5 mr-3 text-gray-400" />
                        )}
                        <div className="flex items-center">
                          <Database className="w-4 h-4 mr-2 text-gray-400" />
                          <span className="font-medium text-gray-900">{table.name}</span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-4 text-sm text-gray-500">
                        <span>{table.rows?.toLocaleString() || 0} rows</span>
                        <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                          {table.tablespace}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Selected Tables Summary */}
          {selectedTables.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <h3 className="font-semibold text-blue-900 mb-2">
                Selected Tables ({selectedTables.length})
              </h3>
              <div className="flex flex-wrap gap-2">
                {selectedTables.map((tableName) => (
                  <span
                    key={tableName}
                    className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800"
                  >
                    {tableName}
                  </span>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* Action Buttons */}
      <div className="flex items-center justify-between pt-6 border-t">
        <button
          onClick={onBack}
          className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 flex items-center"
        >
          <ChevronLeft className="w-4 h-4 mr-2" />
          Back
        </button>

        <button
          onClick={handleExtractDDL}
          disabled={selectedTables.length === 0 || extracting}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
        >
          {extracting ? (
            <>
              <Loader className="w-4 h-4 mr-2 animate-spin" />
              Extracting DDL...
            </>
          ) : (
            <>
              Extract DDL & Continue
              <ChevronRight className="w-4 h-4 ml-2" />
            </>
          )}
        </button>
      </div>
    </div>
  )
}

export default TableBrowser
