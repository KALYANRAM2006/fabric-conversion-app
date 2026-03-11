import React, { useState } from 'react'
import { ChevronLeft, PlayCircle, Loader, CheckCircle, XCircle, Database } from 'lucide-react'
import * as api from '../services/api'

function ExecutionPanel({ config, fabricDDL, onBack }) {
  const [executing, setExecuting] = useState(false)
  const [results, setResults] = useState({})
  const [error, setError] = useState('')

  const tables = Object.keys(fabricDDL)

  const executeTable = async (tableName) => {
    setResults(prev => ({
      ...prev,
      [tableName]: { status: 'executing', message: 'Creating table...' }
    }))

    try {
      const response = await api.createTable({
        fabric: {
          server: config.fabric.server,
          database: config.fabric.database
        },
        schema: config.fabric.schema,
        table_name: tableName,
        ddl: fabricDDL[tableName]
      })

      setResults(prev => ({
        ...prev,
        [tableName]: {
          status: 'success',
          message: response.data.message || 'Table created successfully'
        }
      }))
    } catch (err) {
      setResults(prev => ({
        ...prev,
        [tableName]: {
          status: 'error',
          message: err.response?.data?.error || err.message
        }
      }))
    }
  }

  const executeAll = async () => {
    setExecuting(true)
    setError('')

    try {
      const tablesObj = {}
      tables.forEach(tableName => {
        tablesObj[tableName] = fabricDDL[tableName]
      })

      const response = await api.createTablesBatch({
        fabric: {
          server: config.fabric.server,
          database: config.fabric.database
        },
        schema: config.fabric.schema,
        tables: tablesObj
      })

      // Process results
      const newResults = {}
      response.data.results.forEach(result => {
        newResults[result.table] = {
          status: result.success ? 'success' : 'error',
          message: result.message
        }
      })
      setResults(newResults)
    } catch (err) {
      setError(err.response?.data?.error || err.message)
    } finally {
      setExecuting(false)
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'executing':
        return <Loader className="w-5 h-5 text-blue-600 animate-spin" />
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'error':
        return <XCircle className="w-5 h-5 text-red-600" />
      default:
        return <Database className="w-5 h-5 text-gray-400" />
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'executing':
        return 'bg-blue-50 border-blue-200'
      case 'success':
        return 'bg-green-50 border-green-200'
      case 'error':
        return 'bg-red-50 border-red-200'
      default:
        return 'bg-white border-gray-200'
    }
  }

  const completedCount = Object.values(results).filter(r => r.status === 'success').length
  const errorCount = Object.values(results).filter(r => r.status === 'error').length
  const allCompleted = Object.keys(results).length === tables.length

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Create Tables in Fabric
        </h2>
        <p className="text-gray-600">
          Execute DDL to create {tables.length} table(s) in{' '}
          <span className="font-semibold">{config.fabric.schema}</span> schema
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 text-red-700">
          {error}
        </div>
      )}

      {/* Summary Stats */}
      {allCompleted && (
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="text-3xl font-bold text-blue-600">{tables.length}</div>
            <div className="text-sm text-blue-900 mt-1">Total Tables</div>
          </div>
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="text-3xl font-bold text-green-600">{completedCount}</div>
            <div className="text-sm text-green-900 mt-1">Successful</div>
          </div>
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="text-3xl font-bold text-red-600">{errorCount}</div>
            <div className="text-sm text-red-900 mt-1">Failed</div>
          </div>
        </div>
      )}

      {/* Tables List */}
      <div className="space-y-3">
        {tables.map((tableName) => {
          const result = results[tableName]

          return (
            <div
              key={tableName}
              className={`border rounded-lg p-4 transition-colors ${getStatusColor(result?.status)}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center flex-1">
                  {getStatusIcon(result?.status)}
                  <span className="ml-3 font-semibold text-gray-900">{tableName}</span>
                </div>

                <div className="flex items-center space-x-3">
                  {result?.status === 'success' && (
                    <span className="text-sm text-green-700">
                      {result.message}
                    </span>
                  )}
                  {result?.status === 'error' && (
                    <span className="text-sm text-red-700">
                      {result.message}
                    </span>
                  )}
                  {result?.status === 'executing' && (
                    <span className="text-sm text-blue-700">
                      Creating table...
                    </span>
                  )}
                  {!result && (
                    <button
                      onClick={() => executeTable(tableName)}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm flex items-center"
                    >
                      <PlayCircle className="w-4 h-4 mr-2" />
                      Create Table
                    </button>
                  )}
                </div>
              </div>

              {/* Show DDL preview */}
              {!result && (
                <details className="mt-3">
                  <summary className="text-sm text-gray-600 cursor-pointer hover:text-gray-900">
                    View DDL
                  </summary>
                  <div className="mt-2 bg-gray-900 rounded p-3 overflow-x-auto">
                    <pre className="text-xs text-gray-100 font-mono">
                      {fabricDDL[tableName]}
                    </pre>
                  </div>
                </details>
              )}
            </div>
          )
        })}
      </div>

      {/* Bulk Actions */}
      {!allCompleted && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
          <h3 className="font-semibold text-gray-900 mb-3">Bulk Actions</h3>
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-600">
              Create all {tables.length} tables in Fabric Data Warehouse
            </p>
            <button
              onClick={executeAll}
              disabled={executing}
              className="px-6 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 flex items-center font-semibold"
            >
              {executing ? (
                <>
                  <Loader className="w-5 h-5 mr-2 animate-spin" />
                  Creating Tables...
                </>
              ) : (
                <>
                  <PlayCircle className="w-5 h-5 mr-2" />
                  Create All Tables
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Success Message */}
      {allCompleted && completedCount === tables.length && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
          <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
          <h3 className="text-2xl font-bold text-green-900 mb-2">
            Migration Complete!
          </h3>
          <p className="text-green-700">
            Successfully created all {tables.length} tables in{' '}
            <span className="font-semibold">{config.fabric.database}</span>
          </p>
        </div>
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

        {allCompleted && (
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Start New Migration
          </button>
        )}
      </div>
    </div>
  )
}

export default ExecutionPanel
