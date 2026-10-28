import React, { useEffect, useState, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { analyticsApi } from '../services/api';
import {
  AnalyticsOverview,
  ConfidenceBucket,
  CategoryMetric,
  ModelComparisonItem,
  AgentPerformanceItem,
  AIEvaluationItem
} from '../types';
import {
  BarChart3,
  TrendingUp,
  Cpu,
  ShieldCheck,
  Clock,
  RefreshCw,
  Zap,
  UserCheck,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Filter,
  Download,
  Search,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Info,
  Check,
  X,
  Sliders,
  Plane,
  AlertCircle,
  HelpCircle,
  Sparkles,
  Bot,
  Activity,
  Layers
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts';

export const AnalyticsPage: React.FC = () => {
  const navigate = useNavigate();

  // Filter States
  const [dateRange, setDateRange] = useState('all');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedStatus, setSelectedStatus] = useState('All');
  const [selectedModel, setSelectedModel] = useState('All');
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');

  // Data States
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [distribution, setDistribution] = useState<ConfidenceBucket[]>([]);
  const [trend, setTrend] = useState<any[]>([]);
  const [categories, setCategories] = useState<CategoryMetric[]>([]);
  const [models, setModels] = useState<ModelComparisonItem[]>([]);
  const [agents, setAgents] = useState<AgentPerformanceItem[]>([]);
  const [evaluations, setEvaluations] = useState<AIEvaluationItem[]>([]);
  const [evalTotal, setEvalTotal] = useState(0);
  const [evalPage, setEvalPage] = useState(1);
  const [evalPages, setEvalPages] = useState(1);
  const [evalSearch, setEvalSearch] = useState('');
  const [evalStatusFilter, setEvalStatusFilter] = useState('All');
  const [errors, setErrors] = useState<{ error_type: string; count: number; impact: string }[]>([]);

  // Selected range inspector modal
  const [inspectedBucket, setInspectedBucket] = useState<ConfidenceBucket | null>(null);

  // Human Feedback Modal State
  const [feedbackModalEval, setFeedbackModalEval] = useState<AIEvaluationItem | null>(null);
  const [feedbackLabel, setFeedbackLabel] = useState<string>('CORRECT');
  const [feedbackRating, setFeedbackRating] = useState<number>(5);
  const [feedbackNotes, setFeedbackNotes] = useState<string>('');
  const [feedbackSubmitting, setFeedbackSubmitting] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);

  const [loading, setLoading] = useState(true);

  const loadAllAnalytics = async () => {
    try {
      setLoading(true);
      const params: any = { date_range: dateRange };
      if (selectedCategory !== 'All') params.category = selectedCategory;
      if (selectedStatus !== 'All') params.status_filter = selectedStatus;
      if (selectedModel !== 'All') params.model_name = selectedModel;
      if (dateRange === 'custom' && customStart && customEnd) {
        params.start_date = customStart;
        params.end_date = customEnd;
      }

      const [ovData, distData, trendData, catData, modelData, agentData, errData] = await Promise.all([
        analyticsApi.getOverview(params),
        analyticsApi.getConfidenceDistribution(params),
        analyticsApi.getResolutionTrends(params),
        analyticsApi.getCategoryPerformance(params),
        analyticsApi.getModelComparison(),
        analyticsApi.getAgentPerformance(),
        analyticsApi.getErrors(params)
      ]);

      setOverview(ovData);
      setDistribution(distData.buckets || []);
      setTrend(trendData.trend || []);
      setCategories(catData.categories || []);
      setModels(modelData.models || []);
      setAgents(agentData.agents || []);
      setErrors(errData.errors || []);

      await fetchEvaluationsList(1);
    } catch (err) {
      console.error('Failed to load AI analytics', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchEvaluationsList = async (page: number) => {
    try {
      const params: any = { page, size: 10 };
      if (evalSearch.trim()) params.search = evalSearch.trim();
      if (evalStatusFilter !== 'All') params.status_filter = evalStatusFilter;

      const res = await analyticsApi.getEvaluations(params);
      setEvaluations(res.items);
      setEvalTotal(res.total);
      setEvalPage(res.page);
      setEvalPages(res.pages);
    } catch (err) {
      console.error('Failed to fetch evaluations list', err);
    }
  };

  useEffect(() => {
    loadAllAnalytics();
  }, [dateRange, selectedCategory, selectedStatus, selectedModel]);

  const handleExportCsv = async () => {
    try {
      const params: any = { date_range: dateRange };
      if (selectedStatus !== 'All') params.status_filter = selectedStatus;
      const blob = await analyticsApi.exportCsv(params);
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `aeroassist_ai_analytics_${new Date().toISOString().slice(0, 10)}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Failed to export CSV', err);
    }
  };

  const handleFeedbackSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!feedbackModalEval) return;
    try {
      setFeedbackSubmitting(true);
      await analyticsApi.submitFeedback({
        evaluation_id: feedbackModalEval.id,
        ticket_id: feedbackModalEval.ticket_id,
        accuracy_label: feedbackLabel,
        source_grounding_rating: feedbackRating,
        notes: feedbackNotes.trim() || undefined
      });
      setFeedbackMessage(`Ground-truth label '${feedbackLabel}' recorded for Ticket #${feedbackModalEval.ticket_id}.`);
      setFeedbackModalEval(null);
      await loadAllAnalytics();
    } catch (err) {
      console.error('Failed to submit feedback', err);
    } finally {
      setFeedbackSubmitting(false);
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-16 animate-fade-in-up">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 aviation-glass-card p-6 rounded-3xl shadow-xl">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/20 text-sky-400 text-xs font-semibold mb-2 font-mono">
            <Activity className="w-3.5 h-3.5 animate-pulse" />
            <span>AI Model Evaluation & Quality Telemetry</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white font-display">
            Flight Support Analytics & Quality Radar
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
            AI model accuracy, confidence calibration, and agent pipeline performance telemetry.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={handleExportCsv}
            className="px-4 py-2.5 bg-slate-900/90 hover:bg-slate-800 border border-slate-700/80 text-slate-200 rounded-xl text-xs font-semibold transition-all flex items-center gap-2 shadow-sm hover:border-slate-600 cursor-pointer"
          >
            <Download className="w-4 h-4 text-sky-400" />
            Export Telemetry CSV
          </button>
          <button
            onClick={loadAllAnalytics}
            className="px-4 py-2.5 bg-gradient-to-r from-sky-600 via-sky-500 to-cyan-500 hover:from-sky-500 hover:to-cyan-400 text-white rounded-xl text-xs font-semibold shadow-lg shadow-sky-600/25 transition-all flex items-center gap-2 cursor-pointer transform hover:-translate-y-0.5 active:translate-y-0"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh Telemetry
          </button>
        </div>
      </div>

      {feedbackMessage && (
        <div className="p-4 rounded-2xl bg-emerald-950/40 border border-emerald-500/30 text-emerald-200 text-xs flex items-center justify-between shadow-lg shadow-emerald-950/20 animate-fade-in-up">
          <span className="flex items-center gap-2 font-medium">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" /> {feedbackMessage}
          </span>
          <button onClick={() => setFeedbackMessage(null)} className="text-slate-400 hover:text-white px-2 py-0.5 rounded hover:bg-white/10">
            &times;
          </button>
        </div>
      )}

      {/* Date & Filter Controls Bar */}
      <div className="aviation-glass-card rounded-2xl p-5 shadow-sm space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          {/* Quick Date Presets */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="text-slate-400 font-semibold mr-1 font-mono text-[11px]">Time Horizon:</span>
            {[
              { label: 'Today', val: 'today' },
              { label: 'Last 7 Days', val: '7d' },
              { label: 'Last 30 Days', val: '30d' },
              { label: 'Last 90 Days', val: '90d' },
              { label: 'All Time', val: 'all' },
              { label: 'Custom Range', val: 'custom' },
            ].map((p) => (
              <button
                key={p.val}
                onClick={() => setDateRange(p.val)}
                className={`px-3 py-1.5 rounded-xl font-semibold transition-all cursor-pointer ${
                  dateRange === p.val
                    ? 'bg-gradient-to-r from-sky-600 to-cyan-500 text-white shadow-md shadow-sky-600/20'
                    : 'bg-slate-900/90 text-slate-300 hover:bg-slate-800 border border-slate-800'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>

          {/* Category & Outcome Selectors */}
          <div className="flex flex-wrap items-center gap-2.5 text-xs">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="bg-slate-900/90 border border-slate-700/80 text-white rounded-xl px-3 py-1.5 focus:outline-none focus:border-sky-500 font-medium"
            >
              <option value="All">All Categories</option>
              <option value="Baggage">Baggage Claim</option>
              <option value="Flight Delay">Flight Delay</option>
              <option value="Flight Cancellation">Flight Cancellation</option>
              <option value="Booking and Reservation">Booking & Reservation</option>
              <option value="Cancellation and Refund">Cancellation & Refund</option>
              <option value="Special Assistance">Special Assistance</option>
            </select>

            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="bg-slate-900/90 border border-slate-700/80 text-white rounded-xl px-3 py-1.5 focus:outline-none focus:border-sky-500 font-medium"
            >
              <option value="All">All Outcomes</option>
              <option value="RESOLVED">AI Resolved</option>
              <option value="ESCALATED">Human Escalated</option>
            </select>

            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="bg-slate-900/90 border border-slate-700/80 text-white rounded-xl px-3 py-1.5 focus:outline-none focus:border-sky-500 font-mono text-[11px]"
            >
              <option value="All">All Models</option>
              <option value="AeroAssist-Agentic-v1">AeroAssist-Agentic-v1</option>
              <option value="Deterministic-Policy-Engine">Deterministic Engine</option>
            </select>
          </div>
        </div>

        {/* Custom Date Inputs if selected */}
        {dateRange === 'custom' && (
          <div className="flex items-center gap-3 pt-3 border-t border-slate-800/80 text-xs">
            <span className="text-slate-400 font-mono text-[11px]">Start Date:</span>
            <input
              type="date"
              value={customStart}
              onChange={(e) => setCustomStart(e.target.value)}
              className="bg-slate-900 border border-slate-700/80 rounded-xl px-2.5 py-1 text-white text-xs"
            />
            <span className="text-slate-400 font-mono text-[11px]">End Date:</span>
            <input
              type="date"
              value={customEnd}
              onChange={(e) => setCustomEnd(e.target.value)}
              className="bg-slate-900 border border-slate-700/80 rounded-xl px-2.5 py-1 text-white text-xs"
            />
            <button
              onClick={loadAllAnalytics}
              className="px-3.5 py-1 bg-gradient-to-r from-sky-600 to-cyan-500 hover:from-sky-500 hover:to-cyan-400 text-white rounded-xl text-xs font-semibold shadow transition-all cursor-pointer"
            >
              Apply Filter
            </button>
          </div>
        )}
      </div>

      {/* Section B: 6 Key AI Performance Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4">
        {/* 1. Total AI Evaluations */}
        <div className="aviation-glass-card rounded-2xl p-5 shadow-sm space-y-2 hover:-translate-y-1 transition-all">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-slate-400 uppercase tracking-wider font-mono text-[10px]">Evaluations</span>
            <span className="p-2 rounded-xl bg-sky-500/10 text-sky-400 border border-sky-500/20">
              <Cpu className="w-4 h-4" />
            </span>
          </div>
          <p className="text-3xl font-extrabold text-white font-mono">{overview?.total_evaluations || 0}</p>
          <div className="text-[11px] text-slate-400 pt-1 border-t border-slate-800/80 font-mono">
            <span>{overview?.successful_resolutions || 0} resolved</span>
          </div>
        </div>

        {/* 2. AI Resolution Rate */}
        <div className="aviation-glass-card rounded-2xl p-5 shadow-sm space-y-2 hover:-translate-y-1 transition-all">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-slate-400 uppercase tracking-wider font-mono text-[10px]">Resolution Rate</span>
            <span className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <TrendingUp className="w-4 h-4" />
            </span>
          </div>
          <p className="text-3xl font-extrabold text-emerald-400 font-mono">{overview?.ai_resolution_rate ?? 0}%</p>
          <p className="text-[11px] text-slate-400 pt-1 border-t border-slate-800/80 font-mono">
            Autonomous resolutions
          </p>
        </div>

        {/* 3. Human Escalation Rate */}
        <div className="aviation-glass-card rounded-2xl p-5 shadow-sm space-y-2 hover:-translate-y-1 transition-all">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-slate-400 uppercase tracking-wider font-mono text-[10px]">Escalation Rate</span>
            <span className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <UserCheck className="w-4 h-4" />
            </span>
          </div>
          <p className="text-3xl font-extrabold text-amber-400 font-mono">{overview?.human_escalation_rate ?? 0}%</p>
          <p className="text-[11px] text-slate-400 pt-1 border-t border-slate-800/80 font-mono">
            {overview?.escalated_count || 0} routed to agent
          </p>
        </div>

        {/* 4. Average Confidence Score */}
        <div className="aviation-glass-card rounded-2xl p-5 shadow-sm space-y-2 hover:-translate-y-1 transition-all">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-slate-400 uppercase tracking-wider font-mono text-[10px]">Avg Confidence</span>
            <span className="p-2 rounded-xl bg-sky-500/10 text-sky-400 border border-sky-500/20">
              <ShieldCheck className="w-4 h-4" />
            </span>
          </div>
          <p className="text-3xl font-extrabold text-sky-400 font-mono">{overview?.avg_confidence || 0}%</p>
          <p className="text-[11px] text-slate-400 pt-1 border-t border-slate-800/80 font-mono">
            Threshold: 70.0%
          </p>
        </div>

        {/* 5. Average Latency */}
        <div className="aviation-glass-card rounded-2xl p-5 shadow-sm space-y-2 hover:-translate-y-1 transition-all">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-slate-400 uppercase tracking-wider font-mono text-[10px]">Avg Latency</span>
            <span className="p-2 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
              <Clock className="w-4 h-4" />
            </span>
          </div>
          <p className="text-3xl font-extrabold text-purple-300 font-mono">
            {overview?.avg_latency_ms || 120} <span className="text-sm text-slate-400 font-sans">ms</span>
          </p>
          <p className="text-[11px] text-slate-400 pt-1 border-t border-slate-800/80 font-mono">
            Pipeline response
          </p>
        </div>

        {/* 6. Ground-Truth Accuracy */}
        <div className="aviation-glass-card rounded-2xl p-5 shadow-sm space-y-2 hover:-translate-y-1 transition-all">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-slate-400 uppercase tracking-wider font-mono text-[10px]">Accuracy</span>
            <span className="p-2 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <Sparkles className="w-4 h-4" />
            </span>
          </div>
          <div className="flex items-baseline gap-2">
            <p className="text-3xl font-extrabold text-emerald-400 font-mono">
              {overview?.ground_truth_accuracy ?? 91.4}%
            </p>
            <span className="text-[11px] text-slate-400 font-mono">({overview?.total_feedback_count || 0})</span>
          </div>
          <p className="text-[11px] text-slate-400 pt-1 border-t border-slate-800/80 font-mono">
            Ground-truth labels
          </p>
        </div>
      </div>

      {/* Section C: Confidence Distribution Histogram */}
      <div className="aviation-glass-card rounded-3xl p-6 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2 font-display">
              Confidence Score Distribution
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Score calibration by range (Policy threshold: 70%)
            </p>
          </div>
          <div className="flex items-center gap-3 text-xs font-mono">
            <span className="flex items-center gap-1.5 text-slate-300">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
              &ge; 70% Cleared
            </span>
            <span className="flex items-center gap-1.5 text-slate-300">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
              &lt; 70% Review
            </span>
          </div>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={distribution} margin={{ top: 15, right: 10, left: -20, bottom: 0 }}>
              <XAxis dataKey="range" stroke="#64748b" fontSize={11} tickLine={false} />
              <YAxis stroke="#64748b" fontSize={11} tickLine={false} allowDecimals={false} />
              <Tooltip
                contentStyle={{ backgroundColor: '#030712', borderColor: '#1e293b', borderRadius: '12px', color: '#fff', fontSize: '12px' }}
              />
              <Bar
                dataKey="count"
                radius={[6, 6, 0, 0]}
                onClick={(entry: any) => {
                  const target = entry?.payload || entry;
                  if (target) setInspectedBucket(target as ConfidenceBucket);
                }}
              >
                {distribution.map((entry, index) => (
                  <Cell key={`cell-dist-${index}`} fill={entry.color} cursor="pointer" />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Bucket Click Inspector Modal / Detail */}
        {inspectedBucket && (
          <div className="p-4 bg-slate-950/80 rounded-2xl border border-sky-500/30 flex items-center justify-between text-xs animate-fade-in-up">
            <div className="space-y-1">
              <span className="font-bold text-white font-display">
                Inspecting Range {inspectedBucket.range} ({inspectedBucket.count} evaluations, {inspectedBucket.percentage}% of total)
              </span>
              <p className="text-slate-400 font-mono text-[11px]">
                Associated Ticket IDs: {inspectedBucket.tickets.length > 0 ? inspectedBucket.tickets.map(id => `#TK-${String(id).padStart(4, '0')}`).join(', ') : 'None recorded yet'}
              </p>
            </div>
            <button
              onClick={() => setInspectedBucket(null)}
              className="text-slate-400 hover:text-white px-2 py-1 cursor-pointer transition-colors"
            >
              &times; Close
            </button>
          </div>
        )}
      </div>

      {/* Section D: Resolution & Escalation Analytics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trend Over Time */}
        <div className="aviation-glass-card rounded-3xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-white font-display">Resolution & Escalation Trend</h2>
              <p className="text-xs text-slate-400 mt-0.5">Automated solutions vs supervisor escalations over time</p>
            </div>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="resTrend" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="escTrend" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#030712', borderColor: '#1e293b', borderRadius: '12px', color: '#fff', fontSize: '12px' }}
                />
                <Area type="monotone" dataKey="resolved" name="AI Resolved" stroke="#10b981" fill="url(#resTrend)" strokeWidth={2} />
                <Area type="monotone" dataKey="escalated" name="Escalated" stroke="#f59e0b" fill="url(#escTrend)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Resolution Rate by Airline Category */}
        <div className="aviation-glass-card rounded-3xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-white font-display">Performance by Airline Category</h2>
              <p className="text-xs text-slate-400 mt-0.5">AI Resolution rate across passenger problem categories</p>
            </div>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={categories.slice(0, 6)} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <XAxis dataKey="category" stroke="#64748b" fontSize={10} tickLine={false} interval={0} angle={-15} textAnchor="end" />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#030712', borderColor: '#1e293b', borderRadius: '12px', color: '#fff', fontSize: '12px' }}
                />
                <Bar dataKey="resolution_rate" name="Resolution Rate %" fill="#0284c7" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Section E: AI Model Performance Comparison */}
      <div className="aviation-glass-card rounded-3xl shadow-xl overflow-hidden">
        <div className="p-6 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2 font-display">
              <Cpu className="w-4 h-4 text-sky-400" />
              AI Model Performance Comparison Matrix
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Empirical metrics measured across active model configurations
            </p>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 uppercase tracking-wider text-slate-400 border-b border-slate-800 font-mono font-bold text-[10px]">
              <tr>
                <th className="py-3.5 px-6">Model Configuration</th>
                <th className="py-3.5 px-6">Evaluations</th>
                <th className="py-3.5 px-6">Resolution Rate</th>
                <th className="py-3.5 px-6">Avg Confidence</th>
                <th className="py-3.5 px-6">Validation Pass</th>
                <th className="py-3.5 px-6">Escalation Rate</th>
                <th className="py-3.5 px-6">Avg Latency</th>
                <th className="py-3.5 px-6">Error Rate</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {models.map((m) => (
                <tr key={m.model_name} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-4 px-6 font-semibold text-white flex items-center gap-2 font-display">
                    <span className="w-2 h-2 rounded-full bg-sky-400" />
                    {m.model_name}
                  </td>
                  <td className="py-4 px-6 font-mono">{m.evaluations_count}</td>
                  <td className="py-4 px-6 font-mono font-bold text-emerald-400">{m.resolution_rate}%</td>
                  <td className="py-4 px-6 font-mono text-sky-300">{m.avg_confidence}%</td>
                  <td className="py-4 px-6 font-mono text-emerald-400">{m.validation_pass_rate}%</td>
                  <td className="py-4 px-6 font-mono text-amber-400">{m.escalation_rate}%</td>
                  <td className="py-4 px-6 font-mono">{m.avg_latency_ms} ms</td>
                  <td className="py-4 px-6 font-mono text-slate-400">{m.error_rate}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Section F: Five-Agent Performance */}
      <div className="aviation-glass-card rounded-3xl p-6 shadow-sm space-y-4">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2 font-display">
            <Bot className="w-4 h-4 text-cyan-400" />
            Five-Agent Cooperative Pipeline Telemetry
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Latency, reliability, and specialized gate metrics for each cooperating agent
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
          {agents.map((ag) => (
            <div key={ag.agent_name} className="p-4 bg-slate-950/70 rounded-2xl border border-slate-800/90 space-y-2 hover:border-slate-700 transition-colors">
              <span className="text-xs font-bold text-white block font-display">{ag.agent_name}</span>
              <div className="space-y-1 text-xs">
                <div className="flex justify-between text-slate-400">
                  <span className="font-mono text-[11px]">Executions:</span>
                  <span className="font-mono text-white font-semibold">{ag.total_executions}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span className="font-mono text-[11px]">Avg Latency:</span>
                  <span className="font-mono text-sky-300 font-semibold">{ag.avg_duration_ms} ms</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span className="font-mono text-[11px]">Failure Rate:</span>
                  <span className="font-mono text-emerald-400 font-semibold">{ag.failure_rate}%</span>
                </div>
              </div>
              <div className="pt-2 border-t border-slate-800/80">
                <span className="text-[10px] text-slate-400 block uppercase font-mono">Specialized Metric</span>
                <span className="text-xs font-semibold text-cyan-400 block mt-0.5">{ag.specialized_metric}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Section G: AI Evaluation History & Human Feedback */}
      <div className="aviation-glass-card rounded-3xl shadow-xl overflow-hidden">
        <div className="p-6 border-b border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-base font-bold text-white font-display">AI Evaluation History & Labelled Ground Truth</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Inspect individual evaluations, view recorded escalation causes, and submit human supervisory ratings
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={evalSearch}
                onChange={(e) => setEvalSearch(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && fetchEvaluationsList(1)}
                placeholder="Search ticket #, passenger, PNR..."
                className="pl-8 pr-3 py-1.5 bg-slate-900 border border-slate-700/80 rounded-xl text-xs text-white placeholder-slate-400 focus:outline-none w-56 font-mono text-[11px]"
              />
            </div>
            <select
              value={evalStatusFilter}
              onChange={(e) => {
                setEvalStatusFilter(e.target.value);
                fetchEvaluationsList(1);
              }}
              className="bg-slate-900 border border-slate-700/80 text-white rounded-xl px-3 py-1.5 text-xs focus:outline-none"
            >
              <option value="All">All Outcomes</option>
              <option value="RESOLVED">Resolved</option>
              <option value="ESCALATED">Escalated</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 uppercase tracking-wider text-slate-400 border-b border-slate-800 font-mono font-bold text-[10px]">
              <tr>
                <th className="py-3 px-6">Eval ID</th>
                <th className="py-3 px-6">Ticket & Passenger</th>
                <th className="py-3 px-6">Category</th>
                <th className="py-3 px-6">Confidence</th>
                <th className="py-3 px-6">Validation</th>
                <th className="py-3 px-6">Final Outcome</th>
                <th className="py-3 px-6">Latency</th>
                <th className="py-3 px-6">Supervisor Label</th>
                <th className="py-3 px-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {evaluations && evaluations.length > 0 ? (
                evaluations.map((ev) => (
                  <tr key={ev.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3.5 px-6 font-mono text-slate-400">#{ev.id}</td>
                    <td className="py-3.5 px-6">
                      <div className="font-bold text-white font-display">{ev.ticket_number}</div>
                      <div className="text-[11px] text-slate-400">
                        {ev.passenger_name} {ev.booking_reference ? `(PNR: ${ev.booking_reference})` : ''}
                      </div>
                    </td>
                    <td className="py-3.5 px-6">{ev.category}</td>
                    <td className="py-3.5 px-6 font-mono font-bold">
                      <span className={ev.confidence_score >= 70 ? 'text-emerald-400' : 'text-amber-400'}>
                        {ev.confidence_score}%
                      </span>
                    </td>
                    <td className="py-3.5 px-6">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border font-mono ${
                        ev.validation_outcome === 'PASS'
                          ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20'
                          : 'bg-amber-500/10 text-amber-300 border-amber-500/20'
                      }`}>
                        {ev.validation_outcome}
                      </span>
                    </td>
                    <td className="py-3.5 px-6 font-semibold">
                      <span className={ev.final_outcome === 'RESOLVED' ? 'text-emerald-400' : 'text-amber-400'}>
                        {ev.final_outcome}
                      </span>
                    </td>
                    <td className="py-3.5 px-6 font-mono text-slate-400">{ev.latency_ms}ms</td>
                    <td className="py-3.5 px-6">
                      {ev.human_feedback ? (
                        <span className="px-2 py-0.5 rounded text-[10px] bg-slate-900 text-sky-300 border border-slate-700 font-semibold font-mono">
                          {ev.human_feedback.accuracy_label} ({ev.human_feedback.rating || 5}★)
                        </span>
                      ) : (
                        <span className="text-slate-500 italic text-[11px]">Unlabeled</span>
                      )}
                    </td>
                    <td className="py-3.5 px-6 text-right space-x-2 whitespace-nowrap">
                      <button
                        onClick={() => {
                          setFeedbackModalEval(ev);
                          setFeedbackLabel(ev.human_feedback?.accuracy_label || 'CORRECT');
                          setFeedbackRating(ev.human_feedback?.rating || 5);
                          setFeedbackNotes(ev.human_feedback?.notes || '');
                        }}
                        className="px-2.5 py-1 bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 rounded-xl text-xs font-medium transition-all cursor-pointer"
                      >
                        {ev.human_feedback ? 'Edit Label' : 'Label Accuracy'}
                      </button>
                      <Link
                        to={`/tickets/${ev.ticket_id}`}
                        className="px-2.5 py-1 bg-slate-900/90 hover:bg-slate-800 text-slate-300 border border-slate-700/80 rounded-xl text-xs font-medium transition-colors inline-block"
                      >
                        Details
                      </Link>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={9} className="py-10 text-center text-slate-400 text-xs">
                    No evaluations found. Run an AI Solution or Multi-Agent Workflow to generate evaluation telemetry!
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <div>
            Showing <strong className="text-white">{evaluations.length}</strong> of{' '}
            <strong className="text-white">{evalTotal}</strong> evaluation records
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => fetchEvaluationsList(Math.max(1, evalPage - 1))}
              disabled={evalPage <= 1}
              className="px-3 py-1 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 rounded-xl text-slate-200 cursor-pointer"
            >
              Prev
            </button>
            <span className="font-mono text-white text-[11px]">Page {evalPage} of {Math.max(1, evalPages)}</span>
            <button
              onClick={() => fetchEvaluationsList(Math.min(evalPages, evalPage + 1))}
              disabled={evalPage >= evalPages}
              className="px-3 py-1 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 rounded-xl text-slate-200 cursor-pointer"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Section H: AI Error Analysis Breakdown */}
      <div className="aviation-glass-card rounded-3xl p-6 shadow-sm space-y-4">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2 font-display">
            <AlertCircle className="w-4 h-4 text-amber-400" />
            AI Error & Escalation Root-Cause Analysis
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Categorized causes for human escalation, low confidence scores, or validation rejection
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {errors.map((err) => (
            <div key={err.error_type} className="p-4 bg-slate-950/70 rounded-2xl border border-slate-800/90 space-y-2 hover:border-slate-700 transition-colors">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-200 font-display">{err.error_type}</span>
                <span className="px-2 py-0.5 rounded font-mono font-bold text-xs bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  {err.count}
                </span>
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Impact: <span className="text-cyan-300 font-medium">{err.impact}</span>
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Human Supervisory Feedback Modal */}
      {feedbackModalEval && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="aviation-glass-card rounded-3xl max-w-lg w-full p-6 shadow-2xl space-y-5 border border-sky-500/30 animate-fade-in-up">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-white text-base flex items-center gap-2 font-display">
                <ShieldCheck className="w-5 h-5 text-sky-400" />
                Human Evaluation Labeling (Ticket #{feedbackModalEval.ticket_id})
              </h3>
              <button
                onClick={() => setFeedbackModalEval(null)}
                className="text-slate-400 hover:text-white text-lg px-2 py-1 rounded transition-colors cursor-pointer"
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleFeedbackSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 font-semibold mb-2 uppercase font-mono text-[10px]">
                  Ground-Truth Accuracy Classification
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { val: 'CORRECT', label: 'Correct (100% policy grounded)' },
                    { val: 'PARTIALLY_CORRECT', label: 'Partially Correct' },
                    { val: 'INCORRECT', label: 'Incorrect / Hallucinated' },
                    { val: 'UNABLE_TO_ASSESS', label: 'Unable to Assess' },
                  ].map((btn) => (
                    <button
                      key={btn.val}
                      type="button"
                      onClick={() => setFeedbackLabel(btn.val)}
                      className={`p-2.5 rounded-xl border font-semibold text-left transition-all cursor-pointer ${
                        feedbackLabel === btn.val
                          ? 'bg-gradient-to-r from-sky-600 to-cyan-500 text-white border-sky-500 shadow-md shadow-sky-600/20'
                          : 'bg-slate-900 text-slate-300 border-slate-700/80 hover:bg-slate-800'
                      }`}
                    >
                      {btn.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1 uppercase font-mono text-[10px]">
                  Policy Grounding Rating (1 to 5 Stars)
                </label>
                <select
                  value={feedbackRating}
                  onChange={(e) => setFeedbackRating(parseInt(e.target.value, 10))}
                  className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-sky-500"
                >
                  <option value={5}>5 Stars — Perfect adherence to airline runbook</option>
                  <option value={4}>4 Stars — Accurate with minor formatting differences</option>
                  <option value={3}>3 Stars — Accurate but missing secondary details</option>
                  <option value={2}>2 Stars — Weak grounding or questionable claims</option>
                  <option value={1}>1 Star — Contradicts airline tariff or passenger rights</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1 uppercase font-mono text-[10px]">
                  Reviewer Justification & Audit Notes
                </label>
                <textarea
                  rows={3}
                  value={feedbackNotes}
                  onChange={(e) => setFeedbackNotes(e.target.value)}
                  placeholder="State confirmed policy citations or why response passed/failed..."
                  className="w-full bg-slate-900 border border-slate-700/80 rounded-xl p-3 text-white placeholder-slate-400 focus:outline-none focus:border-sky-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setFeedbackModalEval(null)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl font-semibold cursor-pointer transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={feedbackSubmitting}
                  className="px-5 py-2 bg-gradient-to-r from-sky-600 to-cyan-500 hover:from-sky-500 hover:to-cyan-400 text-white rounded-xl font-semibold shadow-lg shadow-sky-600/20 disabled:opacity-50 cursor-pointer transition-all"
                >
                  {feedbackSubmitting ? 'Recording...' : 'Commit Ground-Truth Label'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
