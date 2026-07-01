import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Brain, TrendingUp, BookOpen, Award, Plus, Loader } from 'lucide-react';
import { skillsApi } from '../services/api';

export default function Skills() {
  const [gaps, setGaps] = useState(null);
  const [progress, setProgress] = useState([]);
  const [recommendations, setRecommendations] = useState(null);
  const [loading, setLoading] = useState(true);
  const [skillName, setSkillName] = useState('');
  const [hours, setHours] = useState('');
  const [tab, setTab] = useState('gaps');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [gapsRes, progressRes, recsRes] = await Promise.all([
        skillsApi.gaps(),
        skillsApi.progress(),
        skillsApi.recommendations(),
      ]);
      setGaps(gapsRes.data);
      setProgress(progressRes.data || []);
      setRecommendations(recsRes.data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const addProgress = async () => {
    if (!skillName || !hours) return;
    try {
      await skillsApi.updateProgress({ skill_name: skillName, hours: parseFloat(hours) });
      setSkillName('');
      setHours('');
      loadData();
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) return <div className="text-center py-10 text-gray-400">Loading skill data...</div>;

  const chartData = (gaps?.all_gaps || []).slice(0, 10).map(g => ({
    name: g.skill,
    demand: g.demand_count,
  }));

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Skill Gap Analysis</h1>

      {/* Tabs */}
      <div className="flex gap-2 border-b">
        {['gaps', 'progress', 'learning', 'targeting'].map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition ${
              tab === t ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {tab === 'gaps' && (
        <div className="space-y-6">
          {/* Demand chart */}
          {chartData.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border p-5">
              <h3 className="font-semibold text-gray-800 mb-4">Most In-Demand Skills You're Missing</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} angle={-30} textAnchor="end" height={60} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="demand" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Gap lists */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {['critical', 'high', 'medium', 'low'].map(severity => {
              const items = gaps?.[`${severity}_gaps`] || [];
              if (items.length === 0) return null;
              const colorMap = { critical: 'red', high: 'orange', medium: 'yellow', low: 'blue' };
              const c = colorMap[severity];
              return (
                <div key={severity} className="bg-white rounded-xl shadow-sm border p-5">
                  <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                    <span className={`w-3 h-3 rounded-full bg-${c}-500`} />
                    {severity.charAt(0).toUpperCase() + severity.slice(1)} Priority ({items.length})
                  </h3>
                  <div className="space-y-2">
                    {items.map((g, i) => (
                      <div key={i} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                        <div>
                          <p className="font-medium text-sm text-gray-800">{g.skill}</p>
                          <p className="text-xs text-gray-500">{g.category}</p>
                        </div>
                        <span className="text-xs bg-gray-200 px-2 py-0.5 rounded">{g.demand_count} jobs</span>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {tab === 'progress' && (
        <div className="space-y-6">
          {/* Log progress */}
          <div className="bg-white rounded-xl shadow-sm border p-5">
            <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <Plus size={18} className="text-blue-500" /> Log Learning Progress
            </h3>
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                type="text"
                placeholder="Skill name (e.g., Cypress)"
                className="flex-1 border rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                value={skillName}
                onChange={e => setSkillName(e.target.value)}
              />
              <input
                type="number"
                placeholder="Hours spent"
                className="w-32 border rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                value={hours}
                onChange={e => setHours(e.target.value)}
              />
              <button onClick={addProgress} className="bg-blue-600 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition">
                Log
              </button>
            </div>
          </div>

          {/* Progress list */}
          {progress.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {progress.map((p, i) => (
                <div key={i} className="bg-white rounded-xl shadow-sm border p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-gray-800 capitalize">{p.skill}</h4>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                      p.current_level === 'advanced' ? 'bg-green-100 text-green-700' :
                      p.current_level === 'intermediate' ? 'bg-blue-100 text-blue-700' :
                      'bg-gray-100 text-gray-600'
                    }`}>
                      {p.current_level}
                    </span>
                  </div>
                  <div className="mb-2">
                    <div className="flex justify-between text-xs text-gray-500 mb-1">
                      <span>Proficiency</span>
                      <span>{p.proficiency}%</span>
                    </div>
                    <div className="w-full h-2 bg-gray-200 rounded-full">
                      <div className="h-full bg-blue-500 rounded-full transition-all" style={{ width: `${p.proficiency}%` }} />
                    </div>
                  </div>
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>{p.hours_invested}h invested</span>
                    <span>{p.last_studied ? new Date(p.last_studied).toLocaleDateString() : '-'}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-white rounded-xl border p-8 text-center text-gray-400">
              No progress logged yet. Start learning and track your progress above.
            </div>
          )}
        </div>
      )}

      {tab === 'learning' && (
        <div className="space-y-4">
          <h3 className="font-semibold text-gray-800">Recommended Learning Path</h3>
          {(gaps?.learning_path || []).map((step, i) => (
            <div key={i} className="bg-white rounded-xl shadow-sm border p-5">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-bold text-sm">
                  {step.order}
                </div>
                <div>
                  <h4 className="font-semibold text-gray-800 capitalize">{step.skill}</h4>
                  <p className="text-xs text-gray-500">~{step.estimated_hours}h to reach {step.target_level}</p>
                </div>
              </div>
              <div className="ml-11 space-y-2">
                {step.milestones?.map((m, j) => (
                  <div key={j} className="flex items-center gap-2 text-sm text-gray-600">
                    <div className="w-1.5 h-1.5 bg-blue-400 rounded-full shrink-0" />
                    {m}
                  </div>
                ))}
                {step.resources?.length > 0 && (
                  <div className="mt-2">
                    <p className="text-xs font-medium text-gray-500 mb-1">Resources:</p>
                    {step.resources.map((r, k) => (
                      <div key={k} className="flex items-center gap-2 text-xs text-blue-600">
                        <BookOpen size={12} />
                        <span>{r.title} ({r.platform})</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          {(!gaps?.learning_path || gaps.learning_path.length === 0) && (
            <div className="bg-white rounded-xl border p-8 text-center text-gray-400">
              Apply to more jobs to generate a personalized learning path.
            </div>
          )}
        </div>
      )}

      {tab === 'targeting' && recommendations && (
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm border p-5">
            <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <TrendingUp size={18} className="text-green-500" /> Recommended Roles Based on Your Skills
            </h3>
            {(recommendations.recommended_roles || []).length > 0 ? (
              <div className="space-y-3">
                {recommendations.recommended_roles.map((r, i) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <p className="font-medium text-gray-800">{r.role}</p>
                      {r.missing?.length > 0 && (
                        <p className="text-xs text-gray-500">Missing: {r.missing.join(', ')}</p>
                      )}
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-lg text-blue-600">{r.readiness}%</p>
                      <p className="text-xs text-gray-500">ready</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-400 text-center py-4">Build skills to unlock new role recommendations.</p>
            )}
          </div>

          {recommendations.upskill_impact && (
            <div className="bg-white rounded-xl shadow-sm border p-5">
              <h3 className="font-semibold text-gray-800 mb-3">Upskill Impact</h3>
              <div className="grid grid-cols-2 gap-4 text-center">
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-2xl font-bold text-gray-800">{recommendations.upskill_impact.current_average_score}%</p>
                  <p className="text-xs text-gray-500">Current Avg Score</p>
                </div>
                <div className="bg-green-50 rounded-lg p-4">
                  <p className="text-2xl font-bold text-green-600">{recommendations.upskill_impact.potential_improvement}%</p>
                  <p className="text-xs text-green-600">After Upskilling</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
