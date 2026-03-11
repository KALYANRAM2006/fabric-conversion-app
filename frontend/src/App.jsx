import React, { useState } from 'react'
import ConnectionConfig from './components/ConnectionConfig'
import TableBrowser from './components/TableBrowser'
import DDLViewer from './components/DDLViewer'
import ExecutionPanel from './components/ExecutionPanel'
import { Database, Workflow, FileCode, PlayCircle } from 'lucide-react'

function App() {
  const [currentStep, setCurrentStep] = useState(1)
  const [config, setConfig] = useState({
    oracle: { user: '', password: '', dsn: '', schema: '' },
    fabric: { server: '', database: '', schema: 'dbo' },
    claudeApiKey: ''
  })
  const [selectedTables, setSelectedTables] = useState([])
  const [oracleDDL, setOracleDDL] = useState({})
  const [fabricDDL, setFabricDDL] = useState({})

  const steps = [
    { id: 1, name: 'Configuration', icon: Database },
    { id: 2, name: 'Select Tables', icon: Workflow },
    { id: 3, name: 'Review DDL', icon: FileCode },
    { id: 4, name: 'Execute', icon: PlayCircle }
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Oracle → Fabric DDL Converter
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                AI-Powered Database Migration Tool
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                Powered by Claude AI
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Progress Steps */}
      <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
        <nav aria-label="Progress">
          <ol className="flex items-center justify-between">
            {steps.map((step, index) => (
              <li key={step.id} className="relative flex-1">
                <div className="flex items-center">
                  <button
                    onClick={() => setCurrentStep(step.id)}
                    className={`group flex items-center ${
                      index !== steps.length - 1 ? 'w-full' : ''
                    }`}
                  >
                    <span className={`flex items-center px-4 py-3 text-sm font-medium ${
                      currentStep === step.id
                        ? 'bg-blue-600 text-white'
                        : currentStep > step.id
                        ? 'bg-green-600 text-white'
                        : 'bg-gray-200 text-gray-600'
                    } rounded-lg transition-colors hover:opacity-90`}>
                      <step.icon className="w-5 h-5 mr-2" />
                      {step.name}
                    </span>
                  </button>
                  {index !== steps.length - 1 && (
                    <div className={`hidden sm:block flex-1 h-1 mx-2 ${
                      currentStep > step.id ? 'bg-green-600' : 'bg-gray-200'
                    }`} />
                  )}
                </div>
              </li>
            ))}
          </ol>
        </nav>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 pb-12 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          {currentStep === 1 && (
            <ConnectionConfig
              config={config}
              setConfig={setConfig}
              onNext={() => setCurrentStep(2)}
            />
          )}

          {currentStep === 2 && (
            <TableBrowser
              config={config}
              selectedTables={selectedTables}
              setSelectedTables={setSelectedTables}
              oracleDDL={oracleDDL}
              setOracleDDL={setOracleDDL}
              onNext={() => setCurrentStep(3)}
              onBack={() => setCurrentStep(1)}
            />
          )}

          {currentStep === 3 && (
            <DDLViewer
              config={config}
              oracleDDL={oracleDDL}
              fabricDDL={fabricDDL}
              setFabricDDL={setFabricDDL}
              onNext={() => setCurrentStep(4)}
              onBack={() => setCurrentStep(2)}
            />
          )}

          {currentStep === 4 && (
            <ExecutionPanel
              config={config}
              fabricDDL={fabricDDL}
              onBack={() => setCurrentStep(3)}
            />
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-gray-500">
            Cedars-Sinai Health System - Data Engineering Team
          </p>
        </div>
      </footer>
    </div>
  )
}

export default App
