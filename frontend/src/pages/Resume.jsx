import React, { useState } from 'react';
import { FileText, Download, Eye, CheckCircle, AlertTriangle, Loader } from 'lucide-react';
import { resumeApi } from '../services/api';

export default function Resume() {
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState(null);
  const [coverLetter, setCoverLetter] = useState(null);
  const [jobId, setJobId] = useState('');

  const generateResume = async () => {
    setGenerating(true);
    try {
      const res = await resumeApi.generate(jobId || null);
      setResult(res.data);
    } catch (e) {
      alert(e.response?.data?.detail || 'Error generating resume. Make sure your profile is set up.');
    }
    setGenerating(false);
  };

  const generateCoverLetter = async () => {
    if (!jobId) {
      alert('Enter a Job ID to generate a cover letter');
      return;
    }
    try {
      const res = await resumeApi.coverLetter(jobId);
      setCoverLetter(res.data.cover_letter);
    } catch (e) {
      alert(e.response?.data?.detail || 'Error generating cover letter');
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Resume Builder</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Generate Section */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <FileText size={20} className="text-blue-500" />
            Generate Resume
          </h3>
          <p className="text-sm text-gray-500 mb-4">
            Generate an ATS-friendly, perfectly aligned PDF resume. Optionally tailor it for a specific job.
          </p>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Job ID (optional)</label>
              <input
                type="number"
                placeholder="Enter job ID to tailor resume"
                className="w-full border rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                value={jobId}
                onChange={e => setJobId(e.target.value)}
              />
              <p className="text-xs text-gray-400 mt-1">Leave empty for a general resume</p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={generateResume}
                disabled={generating}
                className="flex-1 bg-blue-600 text-white py-2.5 rounded-lg font-medium text-sm hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2 transition"
              >
                {generating ? <><Loader size={16} className="animate-spin" /> Generating...</> : 'Generate Resume'}
              </button>
              <button
                onClick={generateCoverLetter}
                className="flex-1 bg-indigo-600 text-white py-2.5 rounded-lg font-medium text-sm hover:bg-indigo-700 flex items-center justify-center gap-2 transition"
              >
                Cover Letter
              </button>
            </div>
          </div>
        </div>

        {/* Result Section */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="font-semibold text-gray-800 mb-4">Generated Output</h3>
          {result ? (
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                {result.error_free ? (
                  <div className="flex items-center gap-2 text-green-600">
                    <CheckCircle size={20} />
                    <span className="font-medium">No errors detected</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-amber-600">
                    <AlertTriangle size={20} />
                    <span className="font-medium">{result.errors.length} issue(s) found</span>
                  </div>
                )}
              </div>

              <div className="bg-gray-50 rounded-lg p-4 space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Filename</span>
                  <span className="font-medium">{result.filename}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Pages</span>
                  <span className="font-medium">{result.page_count}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Quality</span>
                  <span className={`font-medium ${result.error_free ? 'text-green-600' : 'text-amber-600'}`}>
                    {result.error_free ? 'Flawless' : 'Needs Review'}
                  </span>
                </div>
              </div>

              {result.errors?.length > 0 && (
                <div className="bg-amber-50 rounded-lg p-3">
                  <p className="text-sm font-medium text-amber-800 mb-2">Issues Found:</p>
                  <ul className="text-xs text-amber-700 space-y-1">
                    {result.errors.map((e, i) => <li key={i}>• {e}</li>)}
                  </ul>
                </div>
              )}

              <a
                href={resumeApi.download(result.filename)}
                target="_blank"
                rel="noreferrer"
                className="w-full bg-green-600 text-white py-2.5 rounded-lg font-medium text-sm hover:bg-green-700 flex items-center justify-center gap-2 transition"
              >
                <Download size={16} /> Download PDF
              </a>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-400">
              <FileText size={40} className="mx-auto mb-3 opacity-50" />
              <p>Click "Generate Resume" to create your ATS-optimized PDF</p>
            </div>
          )}
        </div>
      </div>

      {/* Cover Letter Preview */}
      {coverLetter && (
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="font-semibold text-gray-800 mb-4">Cover Letter Preview</h3>
          <pre className="bg-gray-50 rounded-lg p-4 text-sm text-gray-700 whitespace-pre-wrap font-sans leading-relaxed">
            {coverLetter}
          </pre>
        </div>
      )}

      {/* Features */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h3 className="font-semibold text-gray-800 mb-4">Resume Features</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            { title: 'ATS Optimized', desc: 'Parsed perfectly by applicant tracking systems' },
            { title: 'Perfect Alignment', desc: 'Balanced layout with no spacing gaps' },
            { title: 'Spell Checked', desc: 'Auto-detects common spelling errors' },
            { title: 'Tailored Content', desc: 'Summary and skills matched to job requirements' },
            { title: 'Professional Format', desc: 'Clean 1-2 page layout with consistent styling' },
            { title: 'Keyword Optimized', desc: 'Highlights matching skills in bold' },
          ].map((f, i) => (
            <div key={i} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
              <CheckCircle size={18} className="text-green-500 mt-0.5 shrink-0" />
              <div>
                <p className="font-medium text-sm text-gray-800">{f.title}</p>
                <p className="text-xs text-gray-500">{f.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
