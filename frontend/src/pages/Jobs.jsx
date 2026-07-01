import React, { useEffect, useState } from 'react';
import { Search, Zap, ExternalLink, Building2, MapPin, IndianRupee } from 'lucide-react';
import { jobsApi } from '../services/api';

export default function Jobs() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('QA Engineer');
  const [location, setLocation] = useState('India');
  const [filters, setFilters] = useState({ min_score: 0, is_mnc: null });
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    loadSavedJobs();
  }, [filters]);

  const loadSavedJobs = async () => {
    setLoading(true);
    try {
      const res = await jobsApi.list(filters);
      setJobs(res.data.jobs || []);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const searchNewJobs = async () => {
    setSearching(true);
    try {
      const res = await jobsApi.search(searchQuery, location);
      setJobs(res.data.jobs || []);
    } catch (e) {
      console.error(e);
    }
    setSearching(false);
  };

  const triggerAutoSearch = async () => {
    try {
      await jobsApi.triggerSearch();
      alert('Background job search triggered! Results will appear shortly.');
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <h1 className="text-2xl font-bold text-gray-900">Job Search</h1>
        <button
          onClick={triggerAutoSearch}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition"
        >
          <Zap size={16} /> Run Auto Search
        </button>
      </div>

      {/* Search bar */}
      <div className="bg-white rounded-xl shadow-sm border p-4">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Job title, skills, or keywords..."
              className="w-full pl-9 pr-4 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && searchNewJobs()}
            />
          </div>
          <div className="relative flex-1 sm:max-w-[200px]">
            <MapPin size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Location"
              className="w-full pl-9 pr-4 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
              value={location}
              onChange={e => setLocation(e.target.value)}
            />
          </div>
          <button
            onClick={searchNewJobs}
            disabled={searching}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition"
          >
            {searching ? 'Searching...' : 'Search'}
          </button>
        </div>
        <div className="flex gap-3 mt-3 flex-wrap">
          <select
            className="border rounded-lg px-3 py-1.5 text-sm"
            value={filters.min_score}
            onChange={e => setFilters({ ...filters, min_score: Number(e.target.value) })}
          >
            <option value={0}>All Scores</option>
            <option value={25}>25%+ Match</option>
            <option value={50}>50%+ Match</option>
            <option value={70}>70%+ Match</option>
          </select>
          <select
            className="border rounded-lg px-3 py-1.5 text-sm"
            value={filters.is_mnc === null ? '' : filters.is_mnc}
            onChange={e => setFilters({ ...filters, is_mnc: e.target.value === '' ? null : e.target.value === 'true' })}
          >
            <option value="">All Companies</option>
            <option value="true">MNCs Only</option>
            <option value="false">Non-MNC</option>
          </select>
        </div>
      </div>

      {/* Job listings */}
      <div className="space-y-4">
        {loading || searching ? (
          <div className="bg-white rounded-xl border p-8 text-center text-gray-400">Loading jobs...</div>
        ) : jobs.length === 0 ? (
          <div className="bg-white rounded-xl border p-8 text-center text-gray-400">
            No jobs found. Click "Run Auto Search" to find jobs across all portals.
          </div>
        ) : (
          jobs.map((job, i) => (
            <div key={job.id || job.external_id || i} className="bg-white rounded-xl shadow-sm border p-5 hover:shadow-md transition">
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-gray-900">{job.title}</h3>
                    {job.is_mnc && (
                      <span className="bg-purple-100 text-purple-700 text-xs px-2 py-0.5 rounded-full font-medium">MNC</span>
                    )}
                  </div>
                  <div className="flex flex-wrap items-center gap-3 text-sm text-gray-500 mb-2">
                    <span className="flex items-center gap-1"><Building2 size={14} /> {job.company}</span>
                    <span className="flex items-center gap-1"><MapPin size={14} /> {job.location || 'Not specified'}</span>
                    {(job.salary_min || job.salary_max) && (
                      <span className="flex items-center gap-1">
                        <IndianRupee size={14} />
                        {job.salary_min && job.salary_max
                          ? `${(job.salary_min/100000).toFixed(1)}L - ${(job.salary_max/100000).toFixed(1)}L`
                          : job.salary_disclosed ? 'Disclosed' : 'Not disclosed'}
                      </span>
                    )}
                  </div>
                  {job.description && (
                    <p className="text-sm text-gray-600 line-clamp-2">{job.description.replace(/<[^>]*>/g, '').substring(0, 200)}...</p>
                  )}
                  {job.match_details?.matched_skills?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {job.match_details.matched_skills.slice(0, 6).map((s, j) => (
                        <span key={j} className="bg-green-50 text-green-700 text-xs px-2 py-0.5 rounded">{s}</span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex flex-row sm:flex-col items-center sm:items-end gap-2">
                  <div className={`text-lg font-bold ${
                    (job.match_score || 0) >= 70 ? 'text-green-600' :
                    (job.match_score || 0) >= 40 ? 'text-yellow-600' : 'text-gray-400'
                  }`}>
                    {Math.round(job.match_score || 0)}%
                  </div>
                  <span className="text-xs text-gray-400">{job.source}</span>
                  {(job.apply_url || job.source_url) && (
                    <a href={job.apply_url || job.source_url} target="_blank" rel="noreferrer"
                      className="flex items-center gap-1 text-blue-600 text-sm hover:underline">
                      Apply <ExternalLink size={14} />
                    </a>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
