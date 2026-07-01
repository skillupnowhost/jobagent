import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Calendar, RefreshCw } from 'lucide-react';
import { reportsApi } from '../services/api';

export default function Reports() {
  const [daily, setDaily] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [dailyRes, historyRes] = await Promise.all([
        reportsApi.daily(),
        reportsApi.history(30),
      ]);
      setDaily(dailyRes.data);
      setHistory(historyRes.data || []);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  if (loading) return <div className="text-center py-10 text-gray-400">Loading reports...</div>;

  const chartData = history.map(r => ({
    date: new Date(r.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    applications: r.applications_sent,
    jobs: r.jobs_found,
    interviews: r.interviews_scheduled,
  })).reverse();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
        <button onClick={loadData} className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800">
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      {/* Today's Report */}
      {daily && (
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Calendar size={18} className="text-blue-500" /> Today's Report
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
            {[
              { label: 'Total', value: daily.statistics?.total || 0 },
              { label: 'Applied', value: daily.statistics?.applied || 0 },
              { label: 'Interviews', value: daily.statistics?.interviews || 0 },
              { label: 'Offers', value: daily.statistics?.offers || 0 },
            ].map(s => (
              <div key={s.label} className="bg-gray-50 rounded-lg p-3 text-center">
                <p className="text-xl font-bold text-gray-900">{s.value}</p>
                <p className="text-xs text-gray-500">{s.label}</p>
              </div>
            ))}
          </div>
          {daily.summary && (
            <pre className="bg-gray-50 rounded-lg p-4 text-sm text-gray-700 whitespace-pre-wrap font-sans">{daily.summary}</pre>
          )}
        </div>
      )}

      {/* Top Matches Today */}
      {daily?.top_matches?.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="font-semibold text-gray-800 mb-4">Top Matches Today</h3>
          <div className="space-y-2">
            {daily.top_matches.map((m, i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-sm text-gray-800">{m.job_title}</p>
                  <p className="text-xs text-gray-500">{m.company}</p>
                </div>
                <span className="font-bold text-blue-600">{m.match_score}%</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Skill Gaps */}
      {daily?.top_skill_gaps?.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="font-semibold text-gray-800 mb-4">Top Skill Gaps (from recent applications)</h3>
          <div className="flex flex-wrap gap-2">
            {daily.top_skill_gaps.map((g, i) => (
              <span key={i} className="bg-red-50 text-red-700 px-3 py-1 rounded-full text-sm">
                {g.skill} ({g.frequency})
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Historical Trend */}
      {chartData.length > 1 && (
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="font-semibold text-gray-800 mb-4">30-Day Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="applications" stroke="#3b82f6" strokeWidth={2} name="Applications" />
              <Line type="monotone" dataKey="jobs" stroke="#10b981" strokeWidth={2} name="Jobs Found" />
              <Line type="monotone" dataKey="interviews" stroke="#f59e0b" strokeWidth={2} name="Interviews" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Report History */}
      {history.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="font-semibold text-gray-800 mb-4">Report History</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-500">
                  <th className="pb-2 font-medium">Date</th>
                  <th className="pb-2 font-medium">Jobs Found</th>
                  <th className="pb-2 font-medium">Applied</th>
                  <th className="pb-2 font-medium">Responses</th>
                  <th className="pb-2 font-medium">Interviews</th>
                </tr>
              </thead>
              <tbody>
                {history.map((r, i) => (
                  <tr key={i} className="border-b last:border-0">
                    <td className="py-2">{new Date(r.date).toLocaleDateString()}</td>
                    <td className="py-2">{r.jobs_found}</td>
                    <td className="py-2">{r.applications_sent}</td>
                    <td className="py-2">{r.responses_received}</td>
                    <td className="py-2">{r.interviews_scheduled}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
