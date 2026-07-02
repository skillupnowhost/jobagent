import React from 'react';
import { Routes, Route, Navigate, NavLink } from 'react-router-dom';
import {
  LayoutDashboard, FileText, Search, Send, Brain, BarChart3, User, Menu, X, LogOut
} from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Applications from './pages/Applications';
import Jobs from './pages/Jobs';
import Resume from './pages/Resume';
import Skills from './pages/Skills';
import Reports from './pages/Reports';
import Profile from './pages/Profile';
import Login from './pages/Login';
import Register from './pages/Register';
import { useAuth } from './context/AuthContext';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/applications', icon: Send, label: 'Applications' },
  { to: '/jobs', icon: Search, label: 'Jobs' },
  { to: '/resume', icon: FileText, label: 'Resume' },
  { to: '/skills', icon: Brain, label: 'Skills' },
  { to: '/reports', icon: BarChart3, label: 'Reports' },
  { to: '/profile', icon: User, label: 'Profile' },
];

function RequireAuth({ children }) {
  const { isAuthenticated, loading } = useAuth();
  if (loading) {
    return <div className="min-h-screen flex items-center justify-center text-gray-400 text-sm">Loading...</div>;
  }
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export default function App() {
  const { isAuthenticated, loading } = useAuth();

  if (!loading && !isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <RequireAuth>
      <Routes>
        <Route path="/login" element={<Navigate to="/" replace />} />
        <Route path="/register" element={<Navigate to="/" replace />} />
        <Route path="*" element={<AppShell />} />
      </Routes>
    </RequireAuth>
  );
}

function AppShell() {
  const [sidebarOpen, setSidebarOpen] = React.useState(false);
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen flex bg-gray-50">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 bg-black/50 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed lg:static inset-y-0 left-0 z-50 w-64 bg-slate-900 text-white
        transform transition-transform lg:transform-none
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="p-5 border-b border-slate-700 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold">Job Agent</h1>
            <p className="text-xs text-slate-400">AI-Powered • 24/7 Active</p>
          </div>
          <button className="lg:hidden text-slate-400" onClick={() => setSidebarOpen(false)}>
            <X size={20} />
          </button>
        </div>
        <nav className="p-3 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors
                ${isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'}`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-700 space-y-3">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
            <span className="text-xs text-slate-400">Agent Active</span>
          </div>
          <button
            onClick={logout}
            className="flex items-center gap-2 text-xs text-slate-300 hover:text-white transition"
          >
            <LogOut size={14} /> Sign out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-h-screen">
        <header className="bg-white border-b px-4 py-3 flex items-center gap-4 lg:px-6 sticky top-0 z-30">
          <button className="lg:hidden text-gray-600" onClick={() => setSidebarOpen(true)}>
            <Menu size={24} />
          </button>
          <h2 className="text-lg font-semibold text-gray-800 flex-1">AI Job Application Agent</h2>
          {user?.name && <span className="text-sm text-gray-500 hidden sm:inline">{user.name}</span>}
        </header>
        <main className="flex-1 p-4 lg:p-6 overflow-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/applications" element={<Applications />} />
            <Route path="/jobs" element={<Jobs />} />
            <Route path="/resume" element={<Resume />} />
            <Route path="/skills" element={<Skills />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/profile" element={<Profile />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
