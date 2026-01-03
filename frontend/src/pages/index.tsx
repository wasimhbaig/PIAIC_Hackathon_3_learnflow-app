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
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [loginUsername, setLoginUsername] = useState<string>('student-123');
  const [loginPassword, setLoginPassword] = useState<string>('demo123');
  const [loginError, setLoginError] = useState<string>('');

  // Demo user database
  const demoUsers = {
    'student-123': { password: 'demo123', name: 'Muhammad Ali', email: 'student@learnflow.com' },
    'student-456': { password: 'demo456', name: 'Fatima Khan', email: 'fatima@learnflow.com' },
    'student-789': { password: 'demo789', name: 'Ahmed Hassan', email: 'ahmed@learnflow.com' },
    'student@learnflow.com': { password: 'demo123', name: 'Muhammad Ali', email: 'student@learnflow.com', id: 'student-123' },
  };

  // Get current user info
  const getCurrentUser = () => {
    const user = demoUsers[studentId as keyof typeof demoUsers];
    return user || { name: 'Student', email: 'student@learnflow.com' };
  };

  // Handle login
  const handleLogin = () => {
    setLoginError('');

    // Check if username exists
    const user = demoUsers[loginUsername as keyof typeof demoUsers];

    if (!user) {
      setLoginError('Invalid username or email');
      return;
    }

    // Check password
    if (user.password !== loginPassword) {
      setLoginError('Invalid password');
      return;
    }

    // Login successful
    const actualStudentId = (user as any).id || loginUsername;
    setStudentId(actualStudentId);
    setToken(`token-${actualStudentId}-${Date.now()}`);
    setIsAuthenticated(true);
    setLoginError('');
  };

  // Close profile menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (showProfileMenu && !target.closest('.profile-menu-container')) {
        setShowProfileMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showProfileMenu]);

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full">
          <div className="text-center">
            <h1 className="text-4xl font-bold text-gray-800 mb-2">LearnFlow</h1>
            <p className="text-gray-600 mb-8">AI-Powered Python Tutoring Platform</p>

            {/* Login Form */}
            <div className="space-y-4">
              {loginError && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                  {loginError}
                </div>
              )}

              <div>
                <label className="block text-left text-sm font-medium text-gray-700 mb-2">
                  Student ID or Email
                </label>
                <input
                  type="text"
                  placeholder="student-123 or student@learnflow.com"
                  value={loginUsername}
                  onChange={(e) => setLoginUsername(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-left text-sm font-medium text-gray-700 mb-2">
                  Password
                </label>
                <input
                  type="password"
                  placeholder="Enter password"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <button
                onClick={handleLogin}
                className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition font-medium"
              >
                🚀 Login to LearnFlow
              </button>

              <div className="text-xs text-gray-500 mt-4 space-y-2">
                <p className="font-semibold">Demo Accounts:</p>
                <div className="grid grid-cols-2 gap-2 text-left">
                  <div className="bg-gray-50 p-2 rounded">
                    <div className="font-medium">student-123</div>
                    <div className="text-gray-400">demo123</div>
                  </div>
                  <div className="bg-gray-50 p-2 rounded">
                    <div className="font-medium">student-456</div>
                    <div className="text-gray-400">demo456</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="mt-8 pt-6 border-t border-gray-200">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold text-blue-600">1,234</div>
                  <div className="text-xs text-gray-600">Students</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-green-600">8</div>
                  <div className="text-xs text-gray-600">Modules</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-purple-600">95%</div>
                  <div className="text-xs text-gray-600">Success Rate</div>
                </div>
              </div>
            </div>
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

              {/* Profile Menu */}
              <div className="relative profile-menu-container">
                <button
                  onClick={() => setShowProfileMenu(!showProfileMenu)}
                  className="h-10 w-10 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold hover:bg-blue-700 transition cursor-pointer"
                >
                  {getCurrentUser().name.charAt(0).toUpperCase()}
                </button>

                {/* Dropdown Menu */}
                {showProfileMenu && (
                  <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg py-2 z-50 border border-gray-200">
                    {/* Student Info */}
                    <div className="px-4 py-3 border-b border-gray-100">
                      <p className="font-semibold text-gray-900">{getCurrentUser().name}</p>
                      <p className="text-sm text-gray-600">{studentId}</p>
                      <p className="text-xs text-gray-500 mt-1">{getCurrentUser().email}</p>
                    </div>

                    {/* Progress Summary */}
                    <div className="px-4 py-3 border-b border-gray-100">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm text-gray-600">Overall Mastery</span>
                        <span className="text-sm font-bold text-blue-600">68%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div className="bg-blue-600 h-2 rounded-full" style={{ width: '68%' }}></div>
                      </div>
                      <div className="mt-2 text-xs text-gray-500">
                        🔥 5 day streak • 📚 Module 2 of 8
                      </div>
                    </div>

                    {/* Menu Items */}
                    <div className="py-1">
                      <button className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition">
                        👤 View Full Profile
                      </button>
                      <button className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition">
                        📊 Progress Report
                      </button>
                      <button className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition">
                        🎯 Learning Goals
                      </button>
                      <button className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition">
                        ⚙️ Settings
                      </button>
                    </div>

                    {/* Logout */}
                    <div className="border-t border-gray-100 pt-1">
                      <button
                        onClick={() => {
                          setIsAuthenticated(false);
                          setShowProfileMenu(false);
                        }}
                        className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition"
                      >
                        🚪 Logout
                      </button>
                    </div>
                  </div>
                )}
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
