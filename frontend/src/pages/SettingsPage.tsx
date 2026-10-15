import React, { useEffect, useState } from 'react';
import { settingsApi } from '../services/api';
import { AppSetting } from '../types';
import { Sliders, Save, CheckCircle2, Shield, RefreshCw, Cpu, Layers, Activity } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const [settingsList, setSettingsList] = useState<AppSetting[]>([]);
  const [loading, setLoading] = useState(true);
  const [savingKey, setSavingKey] = useState<string | null>(null);
  const [message, setMessage] = useState('');

  // Local state map for editing
  const [formValues, setFormValues] = useState<Record<string, string>>({});

  const loadSettings = async () => {
    try {
      setLoading(true);
      const data = await settingsApi.getAll();
      setSettingsList(data);
      const values: Record<string, string> = {};
      data.forEach((s) => {
        values[s.key] = s.value;
      });
      setFormValues(values);
    } catch (err) {
      console.error('Failed to load settings', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  const handleSave = async (key: string) => {
    try {
      setSavingKey(key);
      const val = formValues[key];
      await settingsApi.update(key, val);
      setMessage(`Configuration '${key}' successfully updated in database.`);
      await loadSettings();
    } catch (err) {
      console.error(`Failed to update ${key}`, err);
    } finally {
      setSavingKey(null);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto animate-fade-in-up">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-sky-950/60 pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sky-500/20 to-cyan-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400 shadow-lg shadow-sky-950/50">
              <Sliders className="w-5 h-5 text-sky-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white font-display">
                Platform Policies & Dispatch Guardrails
              </h1>
              <p className="text-xs text-slate-400 mt-0.5">
                Dynamically adjust confidence gates, autonomous thresholds, simulator modes, and multi-agent revision limits.
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={loadSettings}
          className="p-2.5 rounded-xl bg-slate-900/90 border border-slate-700/80 text-slate-300 hover:text-white transition-colors self-start cursor-pointer"
          title="Reload configurations"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-sky-400' : ''}`} />
        </button>
      </div>

      {message && (
        <div className="p-4 rounded-2xl bg-emerald-950/40 border border-emerald-500/30 text-emerald-200 text-xs flex items-center justify-between shadow-lg shadow-emerald-950/20 animate-fade-in-up">
          <span className="flex items-center gap-2 font-medium">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            {message}
          </span>
          <button onClick={() => setMessage('')} className="text-slate-400 hover:text-white px-2 py-0.5 rounded hover:bg-white/10">
            &times;
          </button>
        </div>
      )}

      <div className="space-y-4">
        {/* Confidence Threshold Card */}
        <div className="aviation-glass-card rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
            <div className="space-y-1">
              <span className="text-sm font-bold text-white flex items-center gap-2 font-display">
                <Shield className="w-4 h-4 text-sky-400" />
                Confidence Policy Threshold (%)
              </span>
              <p className="text-xs text-slate-400 max-w-lg leading-relaxed">
                Tickets with estimated confidence below this score are automatically halted for human supervisor review.
                Tickets meeting or exceeding this threshold proceed to automated RAG synthesis and resolution.
              </p>
            </div>
            <span className="px-3 py-1 rounded-full bg-sky-500/10 text-cyan-300 border border-sky-500/20 text-xs font-mono font-bold self-start">
              Current: {formValues['CONFIDENCE_THRESHOLD'] || '70.0'}%
            </span>
          </div>

          <div className="flex items-center gap-4 pt-2">
            <input
              type="range"
              min="50"
              max="95"
              step="1"
              value={parseFloat(formValues['CONFIDENCE_THRESHOLD'] || '70.0')}
              onChange={(e) =>
                setFormValues({ ...formValues, CONFIDENCE_THRESHOLD: String(e.target.value) })
              }
              className="flex-1 accent-sky-500 cursor-pointer"
            />
            <input
              type="number"
              min="0"
              max="100"
              step="0.5"
              value={formValues['CONFIDENCE_THRESHOLD'] || '70.0'}
              onChange={(e) =>
                setFormValues({ ...formValues, CONFIDENCE_THRESHOLD: e.target.value })
              }
              className="w-20 bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-white text-center font-mono focus:outline-none focus:border-sky-500"
            />
            <button
              onClick={() => handleSave('CONFIDENCE_THRESHOLD')}
              disabled={savingKey === 'CONFIDENCE_THRESHOLD'}
              className="px-4 py-2 bg-gradient-to-r from-sky-600 to-cyan-500 hover:from-sky-500 hover:to-cyan-400 text-white rounded-xl text-xs font-semibold shadow-md shadow-sky-600/20 transition-all flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
            >
              <Save className="w-3.5 h-3.5" />
              {savingKey === 'CONFIDENCE_THRESHOLD' ? 'Saving...' : 'Update'}
            </button>
          </div>
        </div>

        {/* AI Mock Mode Card */}
        <div className="aviation-glass-card rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <span className="text-sm font-bold text-white flex items-center gap-2 font-display">
                <Cpu className="w-4 h-4 text-purple-400" />
                AI Provider Simulator Mode (Deterministic Execution)
              </span>
              <p className="text-xs text-slate-400 max-w-lg leading-relaxed">
                When enabled, classification and multi-agent generation operate deterministically via calibrated rule engines and embedded models without requiring paid external API credentials.
              </p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 pt-1">
            <select
              value={formValues['AI_MOCK_MODE'] || 'true'}
              onChange={(e) =>
                setFormValues({ ...formValues, AI_MOCK_MODE: e.target.value })
              }
              className="flex-1 bg-slate-900 border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-sky-500 font-medium"
            >
              <option value="true">ENABLED (Offline / Calibrated Deterministic Engine)</option>
              <option value="false">DISABLED (Use External LLM / OpenAI API Key)</option>
            </select>
            <button
              onClick={() => handleSave('AI_MOCK_MODE')}
              disabled={savingKey === 'AI_MOCK_MODE'}
              className="px-4 py-2.5 bg-slate-900/90 hover:bg-slate-800 text-slate-200 border border-slate-700/80 rounded-xl text-xs font-semibold transition-all flex items-center justify-center gap-1.5 cursor-pointer"
            >
              <Save className="w-3.5 h-3.5 text-sky-400" /> Save
            </button>
          </div>
        </div>

        {/* Jira Mock Mode Card */}
        <div className="aviation-glass-card rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <span className="text-sm font-bold text-white flex items-center gap-2 font-display">
                <Layers className="w-4 h-4 text-emerald-400" />
                Jira Cloud Integration Simulator
              </span>
              <p className="text-xs text-slate-400 max-w-lg leading-relaxed">
                Simulates real Jira Cloud REST issues, transitions, and idempotent webhook syncing without requiring external Atlassian credentials.
              </p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 pt-1">
            <select
              value={formValues['JIRA_MOCK_MODE'] || 'true'}
              onChange={(e) =>
                setFormValues({ ...formValues, JIRA_MOCK_MODE: e.target.value })
              }
              className="flex-1 bg-slate-900 border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-sky-500 font-medium"
            >
              <option value="true">ENABLED (Simulated Jira Cloud)</option>
              <option value="false">DISABLED (Real Jira Cloud REST API)</option>
            </select>
            <button
              onClick={() => handleSave('JIRA_MOCK_MODE')}
              disabled={savingKey === 'JIRA_MOCK_MODE'}
              className="px-4 py-2.5 bg-slate-900/90 hover:bg-slate-800 text-slate-200 border border-slate-700/80 rounded-xl text-xs font-semibold transition-all flex items-center justify-center gap-1.5 cursor-pointer"
            >
              <Save className="w-3.5 h-3.5 text-sky-400" /> Save
            </button>
          </div>
        </div>

        {/* Max Revision Cycles */}
        <div className="aviation-glass-card rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <span className="text-sm font-bold text-white font-display">
                Max Multi-Agent Revision Cycles
              </span>
              <p className="text-xs text-slate-400 max-w-lg leading-relaxed">
                Maximum number of times the Solution Verification Agent can request revisions before escalating to human support.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 pt-1">
            <input
              type="number"
              min="1"
              max="5"
              value={formValues['MAX_AGENT_REVISION_CYCLES'] || '2'}
              onChange={(e) =>
                setFormValues({ ...formValues, MAX_AGENT_REVISION_CYCLES: e.target.value })
              }
              className="w-24 bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-sky-500"
            />
            <button
              onClick={() => handleSave('MAX_AGENT_REVISION_CYCLES')}
              disabled={savingKey === 'MAX_AGENT_REVISION_CYCLES'}
              className="px-4 py-2 bg-slate-900/90 hover:bg-slate-800 text-slate-200 border border-slate-700/80 rounded-xl text-xs font-semibold transition-all flex items-center gap-1.5 cursor-pointer"
            >
              <Save className="w-3.5 h-3.5 text-sky-400" /> Save
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
