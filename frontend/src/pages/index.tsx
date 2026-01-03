/**
 * LearnFlow Student Dashboard
 * Main page with chat and code editor
 */
import React, { useState, useEffect } from 'react';
import { ChatInterface } from '../components/ChatInterface';
import { CodeEditor } from '../components/CodeEditor';

export default function Home() {
  const [token, setToken] = useState<string>('');
  const [studentId, setStudentId] = useState<string>('student-123');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [activeTab, setActiveTab] = useState<'chat' | 'code'>('chat');

  // Mock authentication for demo
  useEffect(() => {
    // In production, this would check for stored token
    const mockToken = 'demo-token-123';
    setToken(mockToken);
    setIsAuthenticated(true);
  }, []);

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-800 mb-4">LearnFlow</h1>
          <p className="text-gray-600">AI-Powered Python Tutoring</p>
          <div className="mt-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-sm text-gray-500">Connecting...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">LearnFlow</h1>
              <p className="text-sm text-gray-600">AI-Powered Python Tutoring Platform</p>
            </div>

            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">Student Dashboard</p>
                <p className="text-xs text-gray-500">Module 2: Control Flow - 68%</p>
              </div>

              <div className="h-10 w-10 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold">
                M
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tab Navigation */}
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setActiveTab('chat')}
            className={`px-6 py-3 rounded-lg font-medium transition ${
              activeTab === 'chat'
                ? 'bg-white text-blue-600 shadow'
                : 'bg-white/50 text-gray-600 hover:bg-white/70'
            }`}
          >
            💬 Chat with AI Tutor
          </button>

          <button
            onClick={() => setActiveTab('code')}
            className={`px-6 py-3 rounded-lg font-medium transition ${
              activeTab === 'code'
                ? 'bg-white text-blue-600 shadow'
                : 'bg-white/50 text-gray-600 hover:bg-white/70'
            }`}
          >
            💻 Code Editor
          </button>
        </div>

        {/* Content Area */}
        <div className="h-[calc(100vh-220px)]">
          {activeTab === 'chat' && (
            <ChatInterface studentId={studentId} token={token} />
          )}

          {activeTab === 'code' && (
            <CodeEditor token={token} />
          )}
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-4 gap-4 mt-8">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600">Current Streak</div>
            <div className="text-2xl font-bold text-blue-600">5 days 🔥</div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600">Exercises Completed</div>
            <div className="text-2xl font-bold text-green-600">23/30</div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600">Overall Mastery</div>
            <div className="text-2xl font-bold text-purple-600">68%</div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600">Next Module</div>
            <div className="text-2xl font-bold text-orange-600">Module 3</div>
          </div>
        </div>
      </main>
    </div>
  );
}
