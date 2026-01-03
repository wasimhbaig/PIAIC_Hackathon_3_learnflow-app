/**
 * Code Editor Component
 * Monaco-based Python code editor with execution
 */
import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import { apiClient } from '../services/api';

interface CodeEditorProps {
  token: string;
}

interface ExecutionResult {
  status: string;
  stdout: string;
  stderr: string;
  execution_time_ms: number;
  score?: number;
}

export const CodeEditor: React.FC<CodeEditorProps> = ({ token }) => {
  const [code, setCode] = useState<string>('# Write your Python code here\nfor i in range(5):\n    print(i)');
  const [output, setOutput] = useState<ExecutionResult | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  const handleRunCode = async () => {
    setIsRunning(true);
    setOutput(null);

    try {
      const response = await apiClient.post(
        '/api/v1/code/execute',
        {
          code,
          language: 'python'
        },
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      setOutput(response.data);
    } catch (error: any) {
      setOutput({
        status: 'error',
        stdout: '',
        stderr: error.response?.data?.detail || 'Failed to execute code',
        execution_time_ms: 0
      });
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <h2 className="text-xl font-bold text-gray-800">Python Code Editor</h2>

        <button
          onClick={handleRunCode}
          disabled={isRunning}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400 font-medium transition"
        >
          {isRunning ? '⏳ Running...' : '▶ Run Code'}
        </button>
      </div>

      {/* Editor */}
      <div className="flex-1">
        <Editor
          height="100%"
          defaultLanguage="python"
          value={code}
          onChange={(value) => setCode(value || '')}
          theme="vs-dark"
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            automaticLayout: true,
          }}
        />
      </div>

      {/* Output */}
      {output && (
        <div className="border-t p-4 bg-gray-50">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold text-gray-700">Output:</h3>
            <div className="flex items-center gap-4 text-sm">
              <span className={`px-2 py-1 rounded ${
                output.status === 'passed' ? 'bg-green-100 text-green-800' :
                output.status === 'error' ? 'bg-red-100 text-red-800' :
                'bg-yellow-100 text-yellow-800'
              }`}>
                {output.status.toUpperCase()}
              </span>

              <span className="text-gray-600">
                ⚡ {output.execution_time_ms}ms
              </span>

              {output.score !== undefined && (
                <span className="text-gray-600">
                  📊 Score: {output.score}/100
                </span>
              )}
            </div>
          </div>

          <div className="bg-black text-green-400 p-4 rounded font-mono text-sm overflow-auto max-h-64">
            {output.stdout && (
              <div className="whitespace-pre-wrap mb-2">
                {output.stdout}
              </div>
            )}

            {output.stderr && (
              <div className="text-red-400 whitespace-pre-wrap">
                {output.stderr}
              </div>
            )}

            {!output.stdout && !output.stderr && (
              <div className="text-gray-500">No output</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
