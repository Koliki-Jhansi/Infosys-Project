import React, { useEffect, useState, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { dashboardApi, workflowApi } from '../services/api';
import { DashboardSummary, Ticket, WorkflowExecutionRecord } from '../types';
import {
  Plane,
  PlusCircle,
  Sparkles,
  GitBranch,
  BarChart3,
  BookOpen,
  Inbox,
  Clock,
  CheckCircle2,
  AlertTriangle,
  UserCheck,
  TrendingUp,
  RefreshCw,
  Search,
  Filter,
  ArrowRight,
  ArrowUpRight,
  ShieldCheck,
  Activity,
  Bot
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

export const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [recentWorkflows, setRecentWorkflows] = useState<WorkflowExecutionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  const loadData = async () => {
    try {
      setLoading(true);
      const summaryRes = await dashboardApi.getSummary();
      setData(summaryRes);

      // Load recent workflow executions if possible
      try {
        const wfRes = await workflowApi.getTicketWorkflows(1);
        if (Array.isArray(wfRes)) {
          setRecentWorkflows(wfRes.slice(0, 5));
        }
      } catch (err) {
        // Fallback gracefully
      }
    } catch (err) {
      console.error('Failed to load home page telemetry', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'NEEDS_REVIEW':
        return 'bg-amber-500/15 text-amber-300 border-amber-500/30';
      case 'CLASSIFIED':
        return 'bg-sky-500/15 text-sky-300 border-sky-500/30';
      case 'IN_PROGRESS':
        return 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30';
      case 'RESOLVED':
        return 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30';
      case 'CLOSED':
        return 'bg-slate-500/15 text-slate-400 border-slate-500/30';
      case 'SUBMITTED':
      default:
        return 'bg-blue-500/15 text-blue-300 border-blue-500/30';
    }
  };

  const getPriorityBadge = (priority?: string) => {
    switch (priority) {
      case 'Urgent':
      case 'P1 Critical':
        return 'bg-rose-500/15 text-rose-300 border-rose-500/30';
      case 'High':
      case 'P2 High':
        return 'bg-orange-500/15 text-orange-300 border-orange-500/30';
      case 'Medium':
      case 'P3 Medium':
        return 'bg-sky-500/15 text-sky-300 border-sky-500/30';
      case 'Low':
      case 'P4 Low':
      default:
        return 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30';
    }
  };

  // Filtered recent tickets
  const filteredTickets = useMemo(() => {
    if (!data?.recent_activity) return [];
    return data.recent_activity.filter((t: Ticket) => {
      const matchSearch =
        searchTerm === '' ||
        (t.passenger_name && t.passenger_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (t.booking_reference && t.booking_reference.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (t.ticket_number && t.ticket_number.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (t.flight_number && t.flight_number.toLowerCase().includes(searchTerm.toLowerCase())) ||
        t.title.toLowerCase().includes(searchTerm.toLowerCase());

      const matchStatus =
        statusFilter === 'ALL' ||
        (statusFilter === 'OPEN' && (t.status === 'SUBMITTED' || t.status === 'IN_PROGRESS' || t.status === 'CLASSIFIED')) ||
        t.status === statusFilter;

      return matchSearch && matchStatus;
    });
  }, [data?.recent_activity, searchTerm, statusFilter]);

  const resolutionPieData = useMemo(() => {
    if (!data) return [];
    return [
      { name: 'AI Resolved', value: data.ai_resolved_tickets || 0, color: '#10b981' },
      { name: 'Escalated / Needs Review', value: data.escalated_tickets || 0, color: '#f59e0b' },
      { name: 'Open / In Queue', value: data.open_tickets || 0, color: '#0284c7' },
    ];
  }, [data]);

  if (loading && !data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[450px] space-y-4">
        <RefreshCw className="w-9 h-9 text-sky-400 animate-spin" />
        <p className="text-slate-400 text-sm">Loading AeroAssist AI operational telemetry...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12 animate-fade-in-up">
      {/* Welcome Operations Banner */}
      <div className="relative overflow-hidden rounded-3xl aviation-glass-card border border-sky-500/20 bg-gradient-to-r from-slate-900/95 via-sky-950/40 to-slate-900/95 p-6 sm:p-8 shadow-2xl backdrop-blur-xl">
        {/* Subtle decorative aviation radar sweep ambient glow */}
        <div className="absolute -right-20 -top-20 w-80 h-80 bg-sky-500/10 rounded-full blur-3xl pointer-events-none animate-pulse-glow" />
        <div className="absolute right-1/4 -bottom-24 w-60 h-60 bg-cyan-500/10 rounded-full blur-2xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2.5">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/30 text-sky-300 text-xs font-semibold backdrop-blur-md">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <Plane className="w-3.5 h-3.5 -rotate-45 text-sky-400" />
              <span className="font-mono tracking-wider text-[11px] uppercase">COMMERCIAL FLIGHT OPS DISPATCH • PORT 8081</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight font-display">
              AeroAssist <span className="bg-gradient-to-r from-sky-400 via-cyan-300 to-blue-500 bg-clip-text text-transparent">AI Operations Command</span>
            </h1>
            <p className="text-slate-300 text-sm max-w-2xl leading-relaxed">
              Real-time airline telemetry, automated triage, and RAG-grounded passenger assistance engine.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={loadData}
              className="px-4 py-2.5 bg-slate-800/80 hover:bg-slate-700/80 hover:border-sky-500/40 border border-slate-700 text-slate-200 rounded-xl text-xs font-semibold transition-all flex items-center gap-2 active:scale-95 shadow-sm"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-sky-400' : 'text-slate-400'}`} />
              Refresh Telemetry
            </button>
            <Link
              to="/tickets/new"
              className="btn-aviation px-5 py-2.5 bg-gradient-to-r from-sky-600 via-sky-500 to-blue-600 hover:from-sky-500 hover:to-blue-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-sky-500/25 transition-all flex items-center gap-2 active:scale-95"
            >
              <PlusCircle className="w-4 h-4" />
              Create New Ticket
            </Link>
          </div>
        </div>
      </div>

      {/* Quick Action Area */}
      <div>
        <div className="flex items-center justify-between mb-3 px-1">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
            <Activity className="w-3.5 h-3.5 text-sky-400" />
            Operations Quick Actions
          </p>
          <span className="text-[11px] font-mono text-slate-400">Milestones 1–4 Fast Ingest</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
          {/* Action 1: Create New Ticket */}
          <Link
            to="/tickets/new"
            className="p-4 rounded-2xl aviation-glass-card border border-slate-800/80 hover:border-sky-500/60 bg-slate-900/60 hover:bg-slate-800/60 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-sky-500/10 group flex flex-col justify-between"
          >
            <div className="w-10 h-10 rounded-xl bg-sky-500/15 text-sky-400 border border-sky-500/30 flex items-center justify-center mb-3 group-hover:scale-110 group-hover:bg-sky-500/25 transition-all duration-300">
              <PlusCircle className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white group-hover:text-sky-300 transition-colors">
                Create New Ticket
              </h3>
              <p className="text-xs text-slate-400 mt-1 leading-snug">Ingest passenger inquiries, PNR, and bag claims</p>
            </div>
            <span className="text-xs text-sky-400 font-semibold mt-3 flex items-center gap-1 group-hover:translate-x-1 transition-transform">
              Open Form &rarr;
            </span>
          </Link>

          {/* Action 2: Test AI Resolution */}
          <Link
            to="/ai-solution"
            className="p-4 rounded-2xl aviation-glass-card border border-slate-800/80 hover:border-cyan-500/60 bg-slate-900/60 hover:bg-slate-800/60 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-cyan-500/10 group flex flex-col justify-between"
          >
            <div className="w-10 h-10 rounded-xl bg-cyan-500/15 text-cyan-400 border border-cyan-500/30 flex items-center justify-center mb-3 group-hover:scale-110 group-hover:bg-cyan-500/25 transition-all duration-300">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white group-hover:text-cyan-300 transition-colors">
                Test AI Resolution
              </h3>
              <p className="text-xs text-slate-400 mt-1 leading-snug">Generate & validate answers with airline runbooks</p>
            </div>
            <span className="text-xs text-cyan-400 font-semibold mt-3 flex items-center gap-1 group-hover:translate-x-1 transition-transform">
              Launch Workspace &rarr;
            </span>
          </Link>

          {/* Action 3: Run Multi-Agent Workflow */}
          <Link
            to="/multi-agent-workflow"
            className="p-4 rounded-2xl aviation-glass-card border border-slate-800/80 hover:border-indigo-500/60 bg-slate-900/60 hover:bg-slate-800/60 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-indigo-500/10 group flex flex-col justify-between"
          >
            <div className="w-10 h-10 rounded-xl bg-indigo-500/15 text-indigo-400 border border-indigo-500/30 flex items-center justify-center mb-3 group-hover:scale-110 group-hover:bg-indigo-500/25 transition-all duration-300">
              <GitBranch className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white group-hover:text-indigo-300 transition-colors">
                Run 5-Agent Workflow
              </h3>
              <p className="text-xs text-slate-400 mt-1 leading-snug">Orchestrate Diagnosis, RAG, Resolution & Escalation</p>
            </div>
            <span className="text-xs text-indigo-400 font-semibold mt-3 flex items-center gap-1 group-hover:translate-x-1 transition-transform">
              View Agents &rarr;
            </span>
          </Link>

          {/* Action 4: View AI Analytics */}
          <Link
            to="/analytics"
            className="p-4 rounded-2xl aviation-glass-card border border-slate-800/80 hover:border-emerald-500/60 bg-slate-900/60 hover:bg-slate-800/60 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-emerald-500/10 group flex flex-col justify-between"
          >
            <div className="w-10 h-10 rounded-xl bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center justify-center mb-3 group-hover:scale-110 group-hover:bg-emerald-500/25 transition-all duration-300">
              <BarChart3 className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white group-hover:text-emerald-300 transition-colors">
                View AI Analytics
              </h3>
              <p className="text-xs text-slate-400 mt-1 leading-snug">Examine model accuracy, confidence, and errors</p>
            </div>
            <span className="text-xs text-emerald-400 font-semibold mt-3 flex items-center gap-1 group-hover:translate-x-1 transition-transform">
              Open Analytics &rarr;
            </span>
          </Link>

          {/* Action 5: Manage Knowledge Base */}
          <Link
            to="/knowledge-base"
            className="p-4 rounded-2xl aviation-glass-card border border-slate-800/80 hover:border-amber-500/60 bg-slate-900/60 hover:bg-slate-800/60 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-amber-500/10 group flex flex-col justify-between"
          >
            <div className="w-10 h-10 rounded-xl bg-amber-500/15 text-amber-400 border border-amber-500/30 flex items-center justify-center mb-3 group-hover:scale-110 group-hover:bg-amber-500/25 transition-all duration-300">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white group-hover:text-amber-300 transition-colors">
                Knowledge Base
              </h3>
              <p className="text-xs text-slate-400 mt-1 leading-snug">Upload & re-index airline policies and runbooks</p>
            </div>
            <span className="text-xs text-amber-400 font-semibold mt-3 flex items-center gap-1 group-hover:translate-x-1 transition-transform">
              Browse Policies &rarr;
            </span>
          </Link>
        </div>
      </div>

      {/* 6 Operational Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4">
        {/* Total Tickets */}
        <div
          onClick={() => navigate('/tickets')}
          className="aviation-glass-card bg-slate-900/70 border border-slate-800/90 rounded-2xl p-5 shadow-lg hover:border-sky-500/60 hover:-translate-y-1 transition-all duration-300 cursor-pointer group relative overflow-hidden"
        >
          <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-sky-500/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          <div className="flex items-center justify-between mb-3">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider font-mono">Total Tickets</span>
            <div className="p-2 bg-slate-800/80 group-hover:bg-sky-500/20 text-sky-400 rounded-xl transition-colors border border-slate-700/60 group-hover:border-sky-500/30">
              <Inbox className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-white font-display tracking-tight">{data?.total_tickets || 0}</p>
          <div className="flex items-center justify-between mt-2.5 text-xs text-slate-400">
            <span>In database</span>
            <ArrowUpRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-sky-400 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
          </div>
        </div>

        {/* Open Tickets */}
        <div
          onClick={() => navigate('/tickets?status=OPEN')}
          className="aviation-glass-card bg-slate-900/70 border border-slate-800/90 rounded-2xl p-5 shadow-lg hover:border-blue-500/60 hover:-translate-y-1 transition-all duration-300 cursor-pointer group relative overflow-hidden"
        >
          <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-blue-500/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          <div className="flex items-center justify-between mb-3">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider font-mono">Open Tickets</span>
            <div className="p-2 bg-blue-500/10 group-hover:bg-blue-500/20 text-blue-400 rounded-xl transition-colors border border-blue-500/20">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-blue-400 font-display tracking-tight">{data?.open_tickets || 0}</p>
          <div className="flex items-center justify-between mt-2.5 text-xs text-slate-400">
            <span>Queued cases</span>
            <ArrowUpRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-blue-400 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
          </div>
        </div>

        {/* AI Resolved */}
        <div
          onClick={() => navigate('/tickets?status=RESOLVED')}
          className="aviation-glass-card bg-slate-900/70 border border-slate-800/90 rounded-2xl p-5 shadow-lg hover:border-emerald-500/60 hover:-translate-y-1 transition-all duration-300 cursor-pointer group relative overflow-hidden"
        >
          <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-emerald-500/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          <div className="flex items-center justify-between mb-3">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider font-mono">AI Resolved</span>
            <div className="p-2 bg-emerald-500/10 group-hover:bg-emerald-500/20 text-emerald-400 rounded-xl transition-colors border border-emerald-500/20">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-emerald-400 font-display tracking-tight">{data?.ai_resolved_tickets || 0}</p>
          <div className="flex items-center justify-between mt-2.5 text-xs text-slate-400">
            <span>Validated &ge; 70%</span>
            <ArrowUpRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-emerald-400 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
          </div>
        </div>

        {/* Escalated */}
        <div
          onClick={() => navigate('/tickets?status=NEEDS_REVIEW')}
          className="aviation-glass-card bg-slate-900/70 border border-slate-800/90 rounded-2xl p-5 shadow-lg hover:border-amber-500/60 hover:-translate-y-1 transition-all duration-300 cursor-pointer group relative overflow-hidden"
        >
          <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-amber-500/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          <div className="flex items-center justify-between mb-3">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider font-mono">Escalated</span>
            <div className="p-2 bg-amber-500/10 group-hover:bg-amber-500/20 text-amber-400 rounded-xl transition-colors border border-amber-500/20">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-amber-400 font-display tracking-tight">{data?.escalated_tickets || 0}</p>
          <div className="flex items-center justify-between mt-2.5 text-xs text-slate-400">
            <span>Human supervisor</span>
            <ArrowUpRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-amber-400 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
          </div>
        </div>

        {/* Pending Human Review */}
        <div
          onClick={() => navigate('/tickets?status=NEEDS_REVIEW')}
          className="aviation-glass-card bg-slate-900/70 border border-slate-800/90 rounded-2xl p-5 shadow-lg hover:border-purple-500/60 hover:-translate-y-1 transition-all duration-300 cursor-pointer group relative overflow-hidden"
        >
          <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-purple-500/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          <div className="flex items-center justify-between mb-3">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider font-mono">Pending Review</span>
            <div className="p-2 bg-purple-500/10 group-hover:bg-purple-500/20 text-purple-400 rounded-xl transition-colors border border-purple-500/20">
              <UserCheck className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-purple-300 font-display tracking-tight">
            {data?.awaiting_review_tickets || data?.escalated_tickets || 0}
          </p>
          <div className="flex items-center justify-between mt-2.5 text-xs text-slate-400">
            <span>Agent signoff</span>
            <ArrowUpRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-purple-400 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
          </div>
        </div>

        {/* AI Resolution Rate */}
        <div
          onClick={() => navigate('/analytics')}
          className="aviation-glass-card bg-slate-900/70 border border-slate-800/90 rounded-2xl p-5 shadow-lg hover:border-cyan-500/60 hover:-translate-y-1 transition-all duration-300 cursor-pointer group relative overflow-hidden"
        >
          <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          <div className="flex items-center justify-between mb-3">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider font-mono">Resolution Rate</span>
            <div className="p-2 bg-cyan-500/10 group-hover:bg-cyan-500/20 text-cyan-400 rounded-xl transition-colors border border-cyan-500/20">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-cyan-400 font-display tracking-tight">
            {data?.ai_resolution_rate ?? 78.4}%
          </p>
          <div className="w-full bg-slate-800/80 rounded-full h-1.5 mt-2.5 overflow-hidden border border-slate-700/50">
            <div
              className="bg-gradient-to-r from-sky-400 to-cyan-300 h-full rounded-full transition-all duration-1000"
              style={{ width: `${Math.min(100, data?.ai_resolution_rate ?? 78.4)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Operational Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trend Area Chart */}
        <div className="lg:col-span-2 aviation-glass-card bg-slate-900/70 border border-slate-800/80 rounded-2xl p-6 shadow-xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-sky-500/5 rounded-full blur-2xl pointer-events-none" />
          <div className="flex items-center justify-between mb-6 relative z-10">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2 font-display">
                <Activity className="w-4 h-4 text-sky-400" />
                Operational Ticket Volume Trend
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">Live ingestion activity across commercial airline support channels</p>
            </div>
            <Link
              to="/analytics"
              className="text-xs font-semibold text-sky-400 hover:text-sky-300 flex items-center gap-1 transition-colors"
            >
              Full AI Analytics &rarr;
            </Link>
          </div>
          <div className="h-60 w-full relative z-10">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data?.volume_trend || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="homeSkyGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0284c7" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#0284c7" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.95)', borderColor: '#334155', borderRadius: '12px', color: '#fff', boxShadow: '0 10px 25px -5px rgba(0,0,0,0.5)' }}
                />
                <Area type="monotone" dataKey="count" stroke="#38bdf8" strokeWidth={2.5} fillOpacity={1} fill="url(#homeSkyGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Resolution Pie Chart */}
        <div className="aviation-glass-card bg-slate-900/70 border border-slate-800/80 rounded-2xl p-6 shadow-xl flex flex-col justify-between relative overflow-hidden">
          <div className="relative z-10">
            <h2 className="text-base font-bold text-white font-display">Resolution Ratio</h2>
            <p className="text-xs text-slate-400 mt-0.5">Automated AI vs human supervisory queues</p>
          </div>
          <div className="h-48 w-full my-auto relative z-10">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={resolutionPieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={70}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {resolutionPieData.map((entry, index) => (
                    <Cell key={`home-pie-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.95)', borderColor: '#334155', borderRadius: '12px', color: '#fff' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="space-y-2 pt-3 border-t border-slate-800 text-xs relative z-10">
            {resolutionPieData.map((item) => (
              <div key={item.name} className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-slate-300">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                  {item.name}
                </span>
                <span className="font-mono font-bold text-white">{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Tickets Table Section */}
      <div className="aviation-glass-card bg-slate-900/75 border border-slate-800/80 rounded-2xl shadow-xl overflow-hidden backdrop-blur-xl">
        <div className="p-6 border-b border-slate-800/80 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2 font-display">
              <span className="w-2 h-2 rounded-full bg-sky-400 animate-ping inline-block"></span>
              Recent Passenger Tickets
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Live database records evaluated by AeroAssist AI multi-agent pipeline
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Search Input */}
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search passenger, PNR, flight #..."
                className="pl-9 pr-3.5 py-2 bg-slate-800/90 border border-slate-700/80 rounded-xl text-xs text-white placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500/30 w-56 transition-all"
              />
            </div>

            {/* Status Filter */}
            <div className="flex items-center gap-1.5 bg-slate-800/90 border border-slate-700/80 rounded-xl px-2.5 py-1.5 text-xs text-slate-300">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-transparent text-white focus:outline-none text-xs cursor-pointer"
              >
                <option value="ALL" className="bg-slate-900 text-slate-200">All Statuses</option>
                <option value="OPEN" className="bg-slate-900 text-slate-200">Open</option>
                <option value="RESOLVED" className="bg-slate-900 text-slate-200">Resolved</option>
                <option value="NEEDS_REVIEW" className="bg-slate-900 text-slate-200">Escalated</option>
                <option value="CLOSED" className="bg-slate-900 text-slate-200">Closed</option>
              </select>
            </div>

            <Link
              to="/tickets"
              className="text-xs font-semibold text-sky-400 hover:text-sky-300 flex items-center gap-1 ml-1 transition-colors group"
            >
              All Tickets <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-800/60 text-[11px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-800/80 font-mono">
              <tr>
                <th className="py-3.5 px-6">Ticket ID</th>
                <th className="py-3.5 px-6">Passenger / PNR</th>
                <th className="py-3.5 px-6">Subject & Flight</th>
                <th className="py-3.5 px-6">Category</th>
                <th className="py-3.5 px-6">Priority</th>
                <th className="py-3.5 px-6">AI Confidence</th>
                <th className="py-3.5 px-6">Status</th>
                <th className="py-3.5 px-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {filteredTickets && filteredTickets.length > 0 ? (
                filteredTickets.slice(0, 8).map((t) => (
                  <tr key={t.id} className="hover:bg-slate-800/50 transition-colors group">
                    {/* Ticket ID */}
                    <td className="py-4 px-6 font-mono text-xs font-bold text-sky-400 group-hover:text-cyan-300 transition-colors">
                      {t.ticket_number || `#TK-${String(t.id).padStart(4, '0')}`}
                    </td>

                    {/* Passenger & PNR */}
                    <td className="py-4 px-6">
                      <div className="font-semibold text-white text-xs">
                        {t.passenger_name || t.reporter?.full_name || 'Passenger'}
                      </div>
                      <div className="text-[11px] font-mono text-slate-400 flex items-center gap-1.5 mt-0.5">
                        {t.booking_reference ? (
                          <span className="bg-sky-500/10 px-1.5 py-0.5 rounded border border-sky-500/25 text-sky-300 font-bold">
                            PNR: {t.booking_reference}
                          </span>
                        ) : (
                          <span>{t.passenger_email || t.reporter?.email}</span>
                        )}
                      </div>
                    </td>

                    {/* Subject & Flight */}
                    <td className="py-4 px-6 max-w-xs">
                      <div className="font-medium text-white text-xs truncate">{t.title}</div>
                      <div className="text-[11px] text-slate-400 flex items-center gap-2 mt-0.5">
                        {t.flight_number && (
                          <span className="text-slate-300 font-mono">Flight {t.flight_number}</span>
                        )}
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3 text-slate-500" />
                          {new Date(t.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </td>

                    {/* Category */}
                    <td className="py-4 px-6 text-xs text-slate-300">
                      <span className="bg-slate-800/80 px-2 py-1 rounded-md border border-slate-700/80 text-[11px]">
                        {t.category}
                      </span>
                    </td>

                    {/* Priority */}
                    <td className="py-4 px-6">
                      <span className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border backdrop-blur-sm ${getPriorityBadge(t.classification?.priority)}`}>
                        {t.classification?.priority || 'Medium'}
                      </span>
                    </td>

                    {/* AI Confidence */}
                    <td className="py-4 px-6">
                      {t.ai_confidence !== undefined || t.classification?.confidence_score !== undefined ? (
                        <div className="flex items-center gap-2">
                          <div className="w-14 bg-slate-800 rounded-full h-1.5 overflow-hidden border border-slate-700">
                            <div
                              className={`h-full rounded-full transition-all duration-700 ${
                                (t.ai_confidence ?? t.classification?.confidence_score ?? 0) >= 70
                                  ? 'bg-emerald-500'
                                  : 'bg-amber-500'
                              }`}
                              style={{ width: `${t.ai_confidence ?? t.classification?.confidence_score ?? 0}%` }}
                            />
                          </div>
                          <span
                            className={`text-xs font-mono font-bold ${
                              (t.ai_confidence ?? t.classification?.confidence_score ?? 0) >= 70
                                ? 'text-emerald-400'
                                : 'text-amber-400'
                            }`}
                          >
                            {t.ai_confidence ?? t.classification?.confidence_score}%
                          </span>
                        </div>
                      ) : (
                        <span className="text-xs text-slate-500">Pending</span>
                      )}
                    </td>

                    {/* Status */}
                    <td className="py-4 px-6">
                      <span className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border backdrop-blur-sm ${getStatusBadge(t.status)}`}>
                        {t.status === 'NEEDS_REVIEW' ? 'ESCALATED' : t.status}
                      </span>
                    </td>

                    {/* Actions */}
                    <td className="py-4 px-6 text-right space-x-1.5">
                      <Link
                        to={`/ai-solution?ticketId=${t.id}`}
                        className="px-2.5 py-1.5 bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 hover:text-sky-300 border border-sky-500/30 rounded-lg text-xs font-medium transition-all inline-flex items-center gap-1 active:scale-95 shadow-sm"
                        title="Open in AI Solution"
                      >
                        <Sparkles className="w-3 h-3 text-sky-400" />
                        AI Sol
                      </Link>
                      <Link
                        to={`/tickets/${t.id}`}
                        className="px-2.5 py-1.5 bg-slate-800/80 hover:bg-slate-700/80 text-slate-200 border border-slate-700 rounded-lg text-xs font-medium transition-all inline-flex items-center gap-1 active:scale-95"
                      >
                        Details
                      </Link>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400 text-sm">
                    No tickets found matching the search criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
