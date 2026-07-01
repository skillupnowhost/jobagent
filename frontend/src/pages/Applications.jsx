import React, { useEffect, useState } from 'react';
import { Search, Filter, Download, Eye, RefreshCw } from 'lucide-react';
import { applicationsApi, resumeApi } from '../services/api';

const STATUS_OPTIONS = ['all', 'pending', 'applied', 'email_sent', 'follow_up_sent', 'interview_scheduled', 'offer_received', 'rejected'];
const STATUS_COLORS = {
  pending: 'bg-gray-100 text-gray-700',
  applied: 'bg-blue-100 text-blue-700',
  email_sent: 'bg-indigo-100 text-indigo-700',
  follow_up_sent: 'bg-purple-100 text-purple-700',
  interview_scheduled: 'bg-green-100 text-green-700',
  offer_received: 'bg-emerald-100 text-emerald-800',
  rejected: 'bg-red-100 text-red-700',
};

export default function Applications() {
  const [apps, setApps] = useState([]);
  const [stats, setStats] = useState({});
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedApp, setSelectedApp] = useState(null);

  useEffect(() => {
    loadData();
  }, [filter]);

  const loadData = async () => {
    setLoading(true);
    try {
      const params = filter !== 'all' ? { status: filter } : {};
      const [appsRes, statsRes] = await Promise.all([
        applicationsApi.list(params),
        applicationsApi.stats(),
      ]);
      setApps(appsRes.data.applications || []);
      setStats(statsRes.data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const updateStatus = async (id, status) => {
    try {
      await applicationsApi.updateStatus(id, { status });
      loadData();
    } catch (e) {
      console.error(e);
    }
  };

  const filtered = apps.filter(a =>
    a.job_title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    a.company.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <h1 className="text-2xl font-bold text-gray-900">Applications</h1>
        <button onClick={loadData} className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800">
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
        {[
          { label: 'Total', value: stats.total || 0 },
          { label: 'Applied', value: stats.applied || 0 },
          { label: 'Interviews', value: stats.interviews || 0 },
          { label: 'Offers', value: stats.offers || 0 },
          { label: 'Today', value: stats.today_applications || 0 },
          { label: 'Response %', value: `${stats.response_rate || 0}%` },
        ].map(s => (
          <div key={s.label} className="bg-white rounded-lg border p-3 text-center">
            <p className="text-lg font-bold text-gray-900">{s.value}</p>
            <p className="text-xs text-gray-500">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search by job title or company..."
            className="w-full pl-9 pr-4 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="flex gap-2 overflow-x-auto pb-1">
          {STATUS_OPTIONS.map(s => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition ${
                filter === s ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {s === 'all' ? 'All' : s.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Applications table */}
      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-400">Loading...</div>
        ) : filtered.length === 0 ? (
          <div className="p-8 text-center text-gray-400">No applications found</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr className="text-left text-gray-500">
                  <th className="px-4 py-3 font-medium">Position</th>
                  <th className="px-4 py-3 font-medium">Company</th>
                  <th className="px-4 py-3 font-medium">Score</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Quality</th>
                  <th className="px-4 py-3 font-medium">Date</th>
                  <th className="px-4 py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(app => (
                  <tr key={app.id} className="border-b last:border-0 hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-800">{app.job_title}</td>
                    <td className="px-4 py-3 text-gray-600">{app.company}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-gray-200 rounded-full">
                          <div
                            className={`h-full rounded-full ${app.match_score >= 70 ? 'bg-green-500' : app.match_score >= 40 ? 'bg-yellow-500' : 'bg-red-400'}`}
                            style={{ width: `${app.match_score}%` }}
                          />
                        </div>
                        <span className="text-xs font-medium">{app.match_score}%</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[app.status] || 'bg-gray-100'}`}>
                        {app.status.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {app.error_free ? (
                        <span className="text-green-600 text-xs">✓ Clean</span>
                      ) : (
                        <span className="text-red-500 text-xs">⚠ Errors</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {app.applied_at ? new Date(app.applied_at).toLocaleDateString() : '-'}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        <button onClick={() => setSelectedApp(app)} className="text-blue-600 hover:text-blue-800" title="View Details">
                          <Eye size={16} />
                        </button>
                        {app.resume_path && (
                          <a href={resumeApi.download(app.resume_path.split('/').pop())} target="_blank" rel="noreferrer" className="text-green-600 hover:text-green-800" title="Download Resume">
                            <Download size={16} />
                          </a>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Detail modal */}
      {selectedApp && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={() => setSelectedApp(null)}>
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full max-h-[80vh] overflow-y-auto p-6" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold mb-1">{selectedApp.job_title}</h3>
            <p className="text-gray-500 mb-4">{selectedApp.company} • {selectedApp.location}</p>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Match Score</span>
                <span className="font-bold">{selectedApp.match_score}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Status</span>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[selectedApp.status]}`}>{selectedApp.status.replace(/_/g, ' ')}</span>
              </div>
              {selectedApp.next_follow_up && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Next Follow-up</span>
                  <span>{new Date(selectedApp.next_follow_up).toLocaleDateString()}</span>
                </div>
              )}
              {selectedApp.skill_gaps?.length > 0 && (
                <div>
                  <span className="text-gray-500">Skill Gaps</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {selectedApp.skill_gaps.map((s, i) => (
                      <span key={i} className="bg-red-50 text-red-600 text-xs px-2 py-0.5 rounded">{s}</span>
                    ))}
                  </div>
                </div>
              )}
              {selectedApp.errors?.length > 0 && (
                <div>
                  <span className="text-gray-500">Errors Detected</span>
                  <ul className="mt-1 list-disc list-inside text-red-600 text-xs">
                    {selectedApp.errors.map((e, i) => <li key={i}>{e}</li>)}
                  </ul>
                </div>
              )}
            </div>
            <div className="mt-6 flex gap-2">
              <select
                className="border rounded px-3 py-1.5 text-sm flex-1"
                defaultValue={selectedApp.status}
                onChange={e => { updateStatus(selectedApp.id, e.target.value); setSelectedApp(null); }}
              >
                {STATUS_OPTIONS.filter(s => s !== 'all').map(s => (
                  <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>
                ))}
              </select>
              <button onClick={() => setSelectedApp(null)} className="px-4 py-1.5 bg-gray-100 rounded text-sm hover:bg-gray-200">Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
