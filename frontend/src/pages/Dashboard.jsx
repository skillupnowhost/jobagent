import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Send, CheckCircle, Clock, AlertCircle, TrendingUp, Briefcase, Star, ArrowRight } from 'lucide-react';
import { dashboardApi } from '../services/api';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

const STATUS_LABELS = {
  pending: 'Pending',
  applied: 'Applied',
  interview_scheduled: 'Interview',
  offer_received: 'Offer',
  rejected: 'Rejected',
};

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dashboardApi.get()
      .then(res => setData(res.data))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSkeleton />;
  if (!data?.profile_exists) return <SetupPrompt />;

  const stats = data.statistics || {};
  const pieData = [
    { name: 'Applied', value: stats.applied || 0 },
    { name: 'Interviews', value: stats.interviews || 0 },
    { name: 'Offers', value: stats.offers || 0 },
    { name: 'Rejected', value: stats.rejected || 0 },
    { name: 'Pending', value: stats.pending || 0 },
  ].filter(d => d.value > 0);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Welcome back, {data.user_name}!</h1>
          <p className="text-gray-500 text-sm">Your AI agent is working 24/7 to find your next role.</p>
        </div>
        <div className="flex items-center gap-2 bg-green-50 text-green-700 px-4 py-2 rounded-full text-sm font-medium">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          Agent Active
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Send} label="Total Applied" value={stats.total || 0} color="blue" />
        <StatCard icon={Clock} label="Today" value={stats.today_applications || 0} color="purple" />
        <StatCard icon={CheckCircle} label="Interviews" value={stats.interviews || 0} color="green" />
        <StatCard icon={Star} label="Avg Match" value={`${stats.average_match_score || 0}%`} color="amber" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Status Distribution */}
        <div className="bg-white rounded-xl shadow-sm border p-5">
          <h3 className="font-semibold text-gray-800 mb-4">Application Status</h3>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                  {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-400 text-center py-10">No applications yet</p>
          )}
        </div>

        {/* Top Matching Jobs */}
        <div className="bg-white rounded-xl shadow-sm border p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-800">Top Matches</h3>
            <Link to="/jobs" className="text-blue-600 text-sm flex items-center gap-1 hover:underline">
              View all <ArrowRight size={14} />
            </Link>
          </div>
          {data.top_matching_jobs?.length > 0 ? (
            <div className="space-y-3">
              {data.top_matching_jobs.map((job, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-800 text-sm">{job.title}</p>
                    <p className="text-xs text-gray-500">{job.company} {job.is_mnc && '• MNC'}</p>
                  </div>
                  <span className={`text-xs font-bold px-2 py-1 rounded-full ${
                    job.match_score >= 70 ? 'bg-green-100 text-green-700' :
                    job.match_score >= 40 ? 'bg-yellow-100 text-yellow-700' :
                    'bg-gray-100 text-gray-600'
                  }`}>
                    {job.match_score}%
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-center py-10">No jobs found yet — search will run shortly</p>
          )}
        </div>
      </div>

      {/* Recent Applications */}
      <div className="bg-white rounded-xl shadow-sm border p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-800">Recent Applications</h3>
          <Link to="/applications" className="text-blue-600 text-sm flex items-center gap-1 hover:underline">
            View all <ArrowRight size={14} />
          </Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-gray-500">
                <th className="pb-2 font-medium">Position</th>
                <th className="pb-2 font-medium">Company</th>
                <th className="pb-2 font-medium">Score</th>
                <th className="pb-2 font-medium">Status</th>
                <th className="pb-2 font-medium">Date</th>
              </tr>
            </thead>
            <tbody>
              {(data.recent_applications || []).map(app => (
                <tr key={app.id} className="border-b last:border-0">
                  <td className="py-2.5 font-medium text-gray-800">{app.job_title}</td>
                  <td className="py-2.5 text-gray-600">{app.company}</td>
                  <td className="py-2.5">
                    <span className={`font-bold ${app.match_score >= 70 ? 'text-green-600' : app.match_score >= 40 ? 'text-yellow-600' : 'text-gray-500'}`}>
                      {app.match_score}%
                    </span>
                  </td>
                  <td className="py-2.5">
                    <StatusBadge status={app.status} />
                  </td>
                  <td className="py-2.5 text-gray-500">{app.applied_at ? new Date(app.applied_at).toLocaleDateString() : '-'}</td>
                </tr>
              ))}
              {(!data.recent_applications || data.recent_applications.length === 0) && (
                <tr><td colSpan={5} className="py-6 text-center text-gray-400">No applications yet</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, color }) {
  const colorMap = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    purple: 'bg-purple-50 text-purple-600',
    amber: 'bg-amber-50 text-amber-600',
  };
  return (
    <div className="bg-white rounded-xl shadow-sm border p-4">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${colorMap[color]}`}>
          <Icon size={20} />
        </div>
        <div>
          <p className="text-xs text-gray-500">{label}</p>
          <p className="text-xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status }) {
  const map = {
    pending: 'bg-gray-100 text-gray-600',
    applied: 'bg-blue-100 text-blue-700',
    email_sent: 'bg-indigo-100 text-indigo-700',
    follow_up_sent: 'bg-purple-100 text-purple-700',
    interview_scheduled: 'bg-green-100 text-green-700',
    offer_received: 'bg-emerald-100 text-emerald-800',
    rejected: 'bg-red-100 text-red-700',
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${map[status] || 'bg-gray-100 text-gray-600'}`}>
      {STATUS_LABELS[status] || status}
    </span>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-8 bg-gray-200 rounded w-64" />
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => <div key={i} className="h-20 bg-gray-200 rounded-xl" />)}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="h-64 bg-gray-200 rounded-xl" />
        <div className="h-64 bg-gray-200 rounded-xl" />
      </div>
    </div>
  );
}

function SetupPrompt() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="text-center bg-white rounded-2xl shadow-lg p-10 max-w-md">
        <Briefcase size={48} className="mx-auto text-blue-500 mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Get Started</h2>
        <p className="text-gray-500 mb-6">Create your profile to activate the AI Job Agent.</p>
        <Link to="/profile" className="inline-flex items-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition">
          Create Profile <ArrowRight size={18} />
        </Link>
      </div>
    </div>
  );
}
