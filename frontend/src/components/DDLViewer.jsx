import React, { useState } from 'react'
import { ChevronLeft, ChevronRight, Loader, FileCode, Sparkles, Edit, Save, MessageSquare, ChevronDown, ChevronUp } from 'lucide-react'
import * as api from '../services/api'

const DEFAULT_INSTRUCTIONS = `- No DEFAULT keyword in CREATE TABLE (Fabric does not support column defaults)
- PRIMARY KEY must NOT be inside CREATE TABLE. Generate a SEPARATE ALTER TABLE after each CREATE TABLE:
    ALTER TABLE schema.table ADD CONSTRAINT PK_table PRIMARY KEY NONCLUSTERED (col) NOT ENFORCED;
- NONCLUSTERED and NOT ENFORCED are both REQUIRED on every PRIMARY KEY
- DATETIME2 must ALWAYS have explicit precision 0-6. Use DATETIME2(6) as default. Never use bare DATETIME2 or DATETIME2(7)+
- Oracle TIMESTAMP or TIMESTAMP(n) → DATETIME2(6)
- No FOREIGN KEY constraints
- No CHECK constraints
- No SEQUENCE or IDENTITY unless explicitly needed
- No computed columns
- Use VARCHAR(n) instead of NVARCHAR(n) — Fabric only supports NVARCHAR(MAX), not sized NVARCHAR
- NVARCHAR(MAX) is allowed, but NVARCHAR(30) etc. is NOT`

function DDLViewer({ config, oracleDDL, fabricDDL, setFabricDDL, onNext, onBack }) {
  const [converting, setConverting] = useState(false)
  const [error, setError] = useState('')
  const [selectedTable, setSelectedTable] = useState(Object.keys(oracleDDL)[0] || '')
  const [editMode, setEditMode] = useState({})
  const [editedDDL, setEditedDDL] = useState({})
  const [customInstructions, setCustomInstructions] = useState(DEFAULT_INSTRUCTIONS)
  const [showInstructions, setShowInstructions] = useState(false)

  const tables = Object.keys(oracleDDL)

  const handleConvert = async () => {
    setConverting(true)
    setError('')

    try {
      const response = await api.convertDDL(oracleDDL, config.claudeApiKey, customInstructions)
      setFabricDDL(response.data.fabric_ddl || {})
    } catch (err) {
      setError(err.response?.data?.error || err.message)
    } finally {
      setConverting(false)
    }
  }

  const toggleEditMode = (tableName) => {
    setEditMode(prev => ({ ...prev, [tableName]: !prev[tableName] }))
    if (!editedDDL[tableName]) {
      setEditedDDL(prev => ({ ...prev, [tableName]: fabricDDL[tableName] }))
    }
  }

  const saveEdit = (tableName) => {
    setFabricDDL(prev => ({ ...prev, [tableName]: editedDDL[tableName] }))
    setEditMode(prev => ({ ...prev, [tableName]: false }))
  }

  const hasFabricDDL = Object.keys(fabricDDL).length > 0

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Review and Convert DDL
        </h2>
        <p className="text-gray-600">
          Review Oracle DDL and convert to Fabric using Claude AI
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 text-red-700">
          {error}
        </div>
      )}

      {/* Table Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-2 overflow-x-auto">
          {tables.map((tableName) => (
            <button
              key={tableName}
              onClick={() => setSelectedTable(tableName)}
              className={`px-4 py-2 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                selectedTable === tableName
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              {tableName}
            </button>
          ))}
        </nav>
      </div>

      {selectedTable && (
        <div className="space-y-4">
          {/* Oracle DDL */}
          <div className="border rounded-lg overflow-hidden">
            <div className="bg-red-50 px-4 py-3 border-b flex items-center justify-between">
              <div className="flex items-center">
                <FileCode className="w-5 h-5 mr-2 text-red-600" />
                <h3 className="font-semibold text-red-900">Oracle DDL</h3>
              </div>
            </div>
            <div className="bg-gray-900 p-4 overflow-x-auto">
              <pre className="text-sm text-gray-100 font-mono">
                {oracleDDL[selectedTable]}
              </pre>
            </div>
          </div>

          {/* Fabric DDL */}
          {fabricDDL[selectedTable] ? (
            <div className="border rounded-lg overflow-hidden">
              <div className="bg-blue-50 px-4 py-3 border-b flex items-center justify-between">
                <div className="flex items-center">
                  <Sparkles className="w-5 h-5 mr-2 text-blue-600" />
                  <h3 className="font-semibold text-blue-900">Fabric DDL</h3>
                </div>
                <button
                  onClick={() => toggleEditMode(selectedTable)}
                  className="flex items-center text-sm text-blue-600 hover:text-blue-700"
                >
                  {editMode[selectedTable] ? (
                    <>
                      <Save className="w-4 h-4 mr-1" />
                      Save Changes
                    </>
                  ) : (
                    <>
                      <Edit className="w-4 h-4 mr-1" />
                      Edit DDL
                    </>
                  )}
                </button>
              </div>
              <div className="bg-gray-900 p-4 overflow-x-auto">
                {editMode[selectedTable] ? (
                  <textarea
                    value={editedDDL[selectedTable] || fabricDDL[selectedTable]}
                    onChange={(e) => setEditedDDL(prev => ({
                      ...prev,
                      [selectedTable]: e.target.value
                    }))}
                    className="w-full h-64 bg-gray-800 text-gray-100 font-mono text-sm p-2 border border-gray-700 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                ) : (
                  <pre className="text-sm text-gray-100 font-mono">
                    {fabricDDL[selectedTable]}
                  </pre>
                )}
              </div>
              {editMode[selectedTable] && (
                <div className="bg-gray-50 px-4 py-3 border-t flex justify-end space-x-2">
                  <button
                    onClick={() => setEditMode(prev => ({ ...prev, [selectedTable]: false }))}
                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => saveEdit(selectedTable)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center"
                  >
                    <Save className="w-4 h-4 mr-2" />
                    Save Changes
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="border rounded-lg border-dashed border-gray-300 bg-gray-50 p-12 text-center">
              <Sparkles className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 mb-4">
                Click "Convert with Claude AI" to generate Fabric DDL
              </p>
            </div>
          )}
        </div>
      )}

      {/* Custom Instructions for Claude */}
      <div className="border rounded-lg overflow-hidden">
        <button
          onClick={() => setShowInstructions(!showInstructions)}
          className="w-full px-4 py-3 bg-amber-50 border-b flex items-center justify-between hover:bg-amber-100 transition-colors"
        >
          <div className="flex items-center">
            <MessageSquare className="w-5 h-5 mr-2 text-amber-600" />
            <h3 className="font-semibold text-amber-900">Custom Instructions for Claude</h3>
          </div>
          {showInstructions ? (
            <ChevronUp className="w-5 h-5 text-amber-600" />
          ) : (
            <ChevronDown className="w-5 h-5 text-amber-600" />
          )}
        </button>
        {showInstructions && (
          <div className="p-4 bg-white">
            <p className="text-sm text-gray-600 mb-2">
              Add specific rules or constraints for Claude to follow when converting DDL.
              These will be included in the conversion prompt.
            </p>
            <textarea
              value={customInstructions}
              onChange={(e) => setCustomInstructions(e.target.value)}
              placeholder="e.g., No DEFAULT keyword, use NVARCHAR instead of VARCHAR..."
              className="w-full h-40 border border-gray-300 rounded-md p-3 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
            <div className="mt-2 flex justify-end">
              <button
                onClick={() => setCustomInstructions(DEFAULT_INSTRUCTIONS)}
                className="text-xs text-amber-600 hover:text-amber-700"
              >
                Reset to Defaults
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Convert / Re-convert Button */}
      <div className="flex justify-center py-4">
        <button
          onClick={handleConvert}
          disabled={converting}
          className="px-8 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center text-lg font-semibold shadow-lg"
        >
          {converting ? (
            <>
              <Loader className="w-5 h-5 mr-3 animate-spin" />
              Converting with Claude AI...
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5 mr-3" />
              {hasFabricDDL ? 'Re-convert with Claude AI' : 'Convert with Claude AI'}
            </>
          )}
        </button>
      </div>

      {/* Conversion Stats */}
      {hasFabricDDL && (
        <div className="bg-green-50 border border-green-200 rounded-md p-4">
          <div className="flex items-center">
            <Sparkles className="w-5 h-5 text-green-600 mr-2" />
            <span className="font-semibold text-green-900">
              Successfully converted {Object.keys(fabricDDL).length} table(s) to Fabric DDL
            </span>
          </div>
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

        <button
          onClick={onNext}
          disabled={!hasFabricDDL}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
        >
          Next: Create Tables
          <ChevronRight className="w-4 h-4 ml-2" />
        </button>
      </div>
    </div>
  )
}

export default DDLViewer
