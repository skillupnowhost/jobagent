import React, { useEffect, useState } from 'react';
import { Save, Plus, Trash2, Loader } from 'lucide-react';
import { profileApi } from '../services/api';

const DEFAULT_PROFILE = {
  name: '', email: '', phone: '', location: '',
  linkedin_url: '', github_url: '', portfolio_url: '',
  professional_summary: '', experience_years: 2.6, min_salary_lpa: 10.0,
  skills: [],
  experience: [],
  education: [],
  certifications: [],
  projects: [],
  preferred_roles: ['QA Engineer', 'Automation Test Engineer', 'SDET', 'Software Test Engineer'],
  preferred_locations: ['Bangalore', 'Hyderabad', 'Chennai', 'Pune', 'Mumbai', 'Remote'],
  preferred_companies: [],
};

export default function Profile() {
  const [profile, setProfile] = useState(DEFAULT_PROFILE);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [tab, setTab] = useState('basic');
  const [newSkill, setNewSkill] = useState('');
  const [newCert, setNewCert] = useState('');

  useEffect(() => {
    profileApi.get()
      .then(res => {
        if (res.data) setProfile({ ...DEFAULT_PROFILE, ...res.data });
      })
      .catch(() => {});
  }, []);

  const save = async () => {
    setSaving(true);
    try {
      await profileApi.save(profile);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e) {
      alert('Error saving profile');
    }
    setSaving(false);
  };

  const update = (field, value) => setProfile(p => ({ ...p, [field]: value }));

  const addSkill = () => {
    if (!newSkill.trim()) return;
    const skills = [...(profile.skills || []), newSkill.trim()];
    update('skills', skills);
    setNewSkill('');
  };

  const removeSkill = (i) => {
    const skills = [...profile.skills];
    skills.splice(i, 1);
    update('skills', skills);
  };

  const addExperience = () => {
    update('experience', [...(profile.experience || []), {
      title: '', company: '', duration: '', location: '', bullets: [''],
    }]);
  };

  const updateExperience = (i, field, value) => {
    const exp = [...profile.experience];
    exp[i] = { ...exp[i], [field]: value };
    update('experience', exp);
  };

  const removeExperience = (i) => {
    const exp = [...profile.experience];
    exp.splice(i, 1);
    update('experience', exp);
  };

  const addEducation = () => {
    update('education', [...(profile.education || []), {
      degree: '', institution: '', year: '', gpa: '',
    }]);
  };

  const updateEducation = (i, field, value) => {
    const edu = [...profile.education];
    edu[i] = { ...edu[i], [field]: value };
    update('education', edu);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Profile</h1>
        <button
          onClick={save}
          disabled={saving}
          className={`flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-medium transition ${
            saved ? 'bg-green-600 text-white' : 'bg-blue-600 text-white hover:bg-blue-700'
          } disabled:opacity-50`}
        >
          {saving ? <><Loader size={16} className="animate-spin" /> Saving...</>
           : saved ? <><Save size={16} /> Saved!</>
           : <><Save size={16} /> Save Profile</>}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b overflow-x-auto">
        {['basic', 'skills', 'experience', 'education', 'preferences'].map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px whitespace-nowrap transition ${
              tab === t ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {tab === 'basic' && (
        <div className="bg-white rounded-xl shadow-sm border p-6 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="Full Name" value={profile.name} onChange={v => update('name', v)} />
            <Input label="Email" value={profile.email} onChange={v => update('email', v)} type="email" />
            <Input label="Phone" value={profile.phone} onChange={v => update('phone', v)} />
            <Input label="Location" value={profile.location} onChange={v => update('location', v)} />
            <Input label="LinkedIn URL" value={profile.linkedin_url} onChange={v => update('linkedin_url', v)} />
            <Input label="GitHub URL" value={profile.github_url} onChange={v => update('github_url', v)} />
            <Input label="Portfolio URL" value={profile.portfolio_url} onChange={v => update('portfolio_url', v)} />
            <Input label="Experience (years)" value={profile.experience_years} onChange={v => update('experience_years', parseFloat(v) || 0)} type="number" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Professional Summary</label>
            <textarea
              className="w-full border rounded-lg px-4 py-2 text-sm h-28 focus:ring-2 focus:ring-blue-500 outline-none resize-none"
              value={profile.professional_summary}
              onChange={e => update('professional_summary', e.target.value)}
              placeholder="Write a compelling professional summary..."
            />
          </div>
        </div>
      )}

      {tab === 'skills' && (
        <div className="bg-white rounded-xl shadow-sm border p-6 space-y-4">
          <div className="flex gap-3">
            <input
              type="text"
              placeholder="Add a skill (e.g., Selenium, Python, API Testing)"
              className="flex-1 border rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
              value={newSkill}
              onChange={e => setNewSkill(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && addSkill()}
            />
            <button onClick={addSkill} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700">
              <Plus size={16} />
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {(profile.skills || []).map((skill, i) => (
              <span key={i} className="flex items-center gap-1 bg-blue-50 text-blue-700 px-3 py-1 rounded-full text-sm">
                {typeof skill === 'string' ? skill : skill.name || JSON.stringify(skill)}
                <button onClick={() => removeSkill(i)} className="hover:text-red-500 ml-1">
                  <Trash2 size={12} />
                </button>
              </span>
            ))}
          </div>
          {(!profile.skills || profile.skills.length === 0) && (
            <p className="text-sm text-gray-400">No skills added yet. Start adding your technical skills above.</p>
          )}
        </div>
      )}

      {tab === 'experience' && (
        <div className="space-y-4">
          {(profile.experience || []).map((exp, i) => (
            <div key={i} className="bg-white rounded-xl shadow-sm border p-5 space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="font-medium text-gray-700">Experience #{i + 1}</h4>
                <button onClick={() => removeExperience(i)} className="text-red-500 hover:text-red-700">
                  <Trash2 size={16} />
                </button>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <Input label="Job Title" value={exp.title} onChange={v => updateExperience(i, 'title', v)} />
                <Input label="Company" value={exp.company} onChange={v => updateExperience(i, 'company', v)} />
                <Input label="Duration" value={exp.duration} onChange={v => updateExperience(i, 'duration', v)} placeholder="e.g., Jan 2022 - Present" />
                <Input label="Location" value={exp.location} onChange={v => updateExperience(i, 'location', v)} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Bullet Points</label>
                {(exp.bullets || []).map((b, j) => (
                  <div key={j} className="flex gap-2 mb-2">
                    <input
                      type="text"
                      className="flex-1 border rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                      value={b}
                      onChange={e => {
                        const bullets = [...exp.bullets];
                        bullets[j] = e.target.value;
                        updateExperience(i, 'bullets', bullets);
                      }}
                      placeholder="Describe an achievement or responsibility"
                    />
                    <button onClick={() => {
                      const bullets = [...exp.bullets];
                      bullets.splice(j, 1);
                      updateExperience(i, 'bullets', bullets);
                    }} className="text-red-400 hover:text-red-600">
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))}
                <button onClick={() => {
                  const bullets = [...(exp.bullets || []), ''];
                  updateExperience(i, 'bullets', bullets);
                }} className="text-blue-600 text-sm hover:underline flex items-center gap-1">
                  <Plus size={14} /> Add bullet
                </button>
              </div>
            </div>
          ))}
          <button onClick={addExperience} className="w-full border-2 border-dashed border-gray-300 rounded-xl p-4 text-gray-500 hover:border-blue-400 hover:text-blue-600 transition flex items-center justify-center gap-2">
            <Plus size={18} /> Add Experience
          </button>
        </div>
      )}

      {tab === 'education' && (
        <div className="space-y-4">
          {(profile.education || []).map((edu, i) => (
            <div key={i} className="bg-white rounded-xl shadow-sm border p-5">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <Input label="Degree" value={edu.degree} onChange={v => updateEducation(i, 'degree', v)} />
                <Input label="Institution" value={edu.institution} onChange={v => updateEducation(i, 'institution', v)} />
                <Input label="Year" value={edu.year} onChange={v => updateEducation(i, 'year', v)} />
                <Input label="GPA (optional)" value={edu.gpa} onChange={v => updateEducation(i, 'gpa', v)} />
              </div>
            </div>
          ))}
          <button onClick={addEducation} className="w-full border-2 border-dashed border-gray-300 rounded-xl p-4 text-gray-500 hover:border-blue-400 hover:text-blue-600 transition flex items-center justify-center gap-2">
            <Plus size={18} /> Add Education
          </button>
        </div>
      )}

      {tab === 'preferences' && (
        <div className="bg-white rounded-xl shadow-sm border p-6 space-y-4">
          <Input label="Minimum Salary (LPA)" value={profile.min_salary_lpa} onChange={v => update('min_salary_lpa', parseFloat(v) || 0)} type="number" />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Preferred Roles (comma-separated)</label>
            <input
              className="w-full border rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
              value={(profile.preferred_roles || []).join(', ')}
              onChange={e => update('preferred_roles', e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Preferred Locations (comma-separated)</label>
            <input
              className="w-full border rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
              value={(profile.preferred_locations || []).join(', ')}
              onChange={e => update('preferred_locations', e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
            />
          </div>
        </div>
      )}
    </div>
  );
}

function Input({ label, value, onChange, type = 'text', placeholder = '' }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input
        type={type}
        className="w-full border rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
        value={value || ''}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder || label}
      />
    </div>
  );
}
