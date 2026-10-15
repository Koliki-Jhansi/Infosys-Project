import React, { useEffect, useState, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { dashboardApi } from '../services/api';
import { DashboardSummary, Ticket } from '../types';
import {
  Inbox,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  ArrowRight,
  RefreshCw,
  PlusCircle,
  Clock,
  Plane,
  ShieldCheck,
  Search,
  Filter,
  Zap,
  Luggage,
  Sparkles,
  ArrowUpRight,
  ExternalLink
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

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const res = await dashboardApi.getSummary();
      setData(res);
    } catch (err) {
      console.error('Failed to load airline dashboard summary', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
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

  const getPriorityBadge = (priority: string) => {
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

  // Chart data for AI vs Escalated
  const resolutionRatioData = useMemo(() => {
    if (!data) return [];
    return [
      { name: 'AI Resolved', value: data.ai_resolved_tickets || 0, color: '#10b981' },
      { name: 'Escalated / Review', value: data.escalated_tickets || 0, color: '#f59e0b' },
      { name: 'Open / In-Queue', value: data.open_tickets || 0, color: '#0284c7' },
    ];
  }, [data]);

  const CATEGORY_COLORS = ['#38bdf8', '#0284c7', '#6366f1', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'];

  if (loading && !data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[450px] space-y-4">
        <RefreshCw className="w-9 h-9 text-sky-400 animate-spin" />
        <p className="text-slate-400 text-sm">Loading airline passenger support telemetry...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Flight Operations Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/60 p-6 rounded-2xl border border-slate-800 backdrop-blur-sm">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="p-2 rounded-xl bg-sky-500/10 text-sky-400 border border-sky-500/20">
              <Plane className="w-5 h-5 -rotate-45" />
            </span>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
              Airline Support Operations Dashboard
            </h1>
          </div>
          <p className="text-sm text-slate-400 mt-2">
            Real-time passenger support ticket analytics, AI resolution rates, and multi-agent queue telemetry.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={loadDashboard}
            className="px-3.5 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 rounded-xl text-sm font-medium transition-colors flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <Link
            to="/tickets/new"
            className="px-4 py-2.5 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-sm font-semibold shadow-lg shadow-sky-500/20 transition-all flex items-center gap-2"
          >
            <PlusCircle className="w-4 h-4" />
            New Passenger Ticket
          </Link>
        </div>
      </div>

      {/* 6 Key Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4">
        {/* Total Tickets */}
        <div
          onClick={() => navigate('/tickets')}
          className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-sky-500/50 hover:bg-slate-800/50 transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Total Tickets</span>
            <div className="p-2 bg-slate-800 group-hover:bg-sky-500/20 text-sky-400 rounded-lg transition-colors">
              <Inbox className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-white font-mono">{data?.total_tickets || 0}</p>
          <div className="flex items-center justify-between mt-2 text-xs text-slate-400">
            <span>All records</span>
            <ArrowUpRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-sky-400 transition-colors" />
          </div>
        </div>

        {/* Open Tickets */}
        <div
          onClick={() => navigate('/tickets?status=OPEN')}
          className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-blue-500/50 hover:bg-slate-800/50 transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Open Tickets</span>
            <div className="p-2 bg-blue-500/10 group-hover:bg-blue-500/20 text-blue-400 rounded-lg transition-colors">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-blue-400 font-mono">{data?.open_tickets || 0}</p>
          <div className="flex items-center justify-between mt-2 text-xs text-slate-400">
            <span>In queue</span>
            <ArrowUpRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-blue-400 transition-colors" />
          </div>
        </div>

        {/* AI Resolved */}
        <div
          onClick={() => navigate('/tickets?status=RESOLVED')}
          className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-emerald-500/50 hover:bg-slate-800/50 transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">AI Resolved</span>
            <div className="p-2 bg-emerald-500/10 group-hover:bg-emerald-500/20 text-emerald-400 rounded-lg transition-colors">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-emerald-400 font-mono">{data?.ai_resolved_tickets || 0}</p>
          <div className="flex items-center justify-between mt-2 text-xs text-slate-400">
            <span>Validated &ge; 70%</span>
            <ArrowUpRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-emerald-400 transition-colors" />
          </div>
        </div>

        {/* Escalated Tickets */}
        <div
          onClick={() => navigate('/tickets?status=NEEDS_REVIEW')}
          className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-amber-500/50 hover:bg-slate-800/50 transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Escalated</span>
            <div className="p-2 bg-amber-500/10 group-hover:bg-amber-500/20 text-amber-400 rounded-lg transition-colors">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-amber-400 font-mono">{data?.escalated_tickets || 0}</p>
          <div className="flex items-center justify-between mt-2 text-xs text-slate-400">
            <span>Human review</span>
            <ArrowUpRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-amber-400 transition-colors" />
          </div>
        </div>

        {/* Avg Resolution Time */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Avg Resolution</span>
            <div className="p-2 bg-purple-500/10 text-purple-400 rounded-lg">
              <Zap className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-extrabold text-purple-300 font-mono mt-1">
            {data?.avg_resolution_time || '18 mins'}
          </p>
          <div className="flex items-center justify-between mt-2 text-xs text-slate-400">
            <span className="text-purple-400 font-medium">92% faster</span>
            <span>AI powered</span>
          </div>
        </div>

        {/* AI Resolution Rate */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Resolution Rate</span>
            <div className="p-2 bg-cyan-500/10 text-cyan-400 rounded-lg">
              <Sparkles className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-1">
            <p className="text-3xl font-extrabold text-cyan-400 font-mono">
              {data?.ai_resolution_rate ?? 78.4}%
            </p>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 mt-3 overflow-hidden">
            <div
              className="bg-cyan-400 h-full rounded-full transition-all duration-500"
              style={{ width: `${Math.min(100, data?.ai_resolution_rate ?? 78.4)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Analytics Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Ticket Volume Trend */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                Passenger Support Ticket Volume Over Time
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">Ingested passenger inquiries and disruption surges</p>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-sky-400 bg-sky-500/10 px-2.5 py-1 rounded-lg border border-sky-500/20">
              <TrendingUp className="w-3.5 h-3.5" />
              <span>Live Synced</span>
            </div>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data?.volume_trend || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0284c7" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#0284c7" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff' }}
                />
                <Area type="monotone" dataKey="count" stroke="#38bdf8" strokeWidth={2} fillOpacity={1} fill="url(#skyGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* AI-Resolved vs Escalated */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm flex flex-col justify-between">
          <div>
            <h2 className="text-base font-bold text-white">Resolution Distribution</h2>
            <p className="text-xs text-slate-400 mt-0.5">Automated solutions vs human escalation</p>
          </div>
          <div className="h-52 w-full my-auto">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={resolutionRatioData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={75}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {resolutionRatioData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="space-y-2 pt-3 border-t border-slate-800 text-xs">
            {resolutionRatioData.map((item) => (
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

      {/* Ticket Categories Bar Chart */}
      {data?.category_distribution && data.category_distribution.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-white">Inquiries by Airline Category</h2>
              <p className="text-xs text-slate-400 mt-0.5">Classification volume across baggage, flight delays, refunds, and bookings</p>
            </div>
          </div>
          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.category_distribution} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <XAxis dataKey="name" stroke="#64748b" fontSize={10} tickLine={false} interval={0} angle={-15} textAnchor="end" />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff' }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {data.category_distribution.map((_, index) => (
                    <Cell key={`cat-${index}`} fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Recent Tickets Table Section */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              Recent Passenger Tickets
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Live database records processed by AeroAssist AI orchestration engine
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
                className="pl-9 pr-3.5 py-2 bg-slate-800/80 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-400 focus:outline-none focus:border-sky-500 w-56 transition-all"
              />
            </div>

            {/* Status Filter */}
            <div className="flex items-center gap-1.5 bg-slate-800/80 border border-slate-700 rounded-xl px-2.5 py-1.5 text-xs text-slate-300">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-transparent text-white focus:outline-none text-xs"
              >
                <option value="ALL" className="bg-slate-900">All Statuses</option>
                <option value="OPEN" className="bg-slate-900">Open</option>
                <option value="RESOLVED" className="bg-slate-900">Resolved</option>
                <option value="NEEDS_REVIEW" className="bg-slate-900">Escalated</option>
                <option value="CLOSED" className="bg-slate-900">Closed</option>
              </select>
            </div>

            <Link
              to="/tickets"
              className="text-xs font-semibold text-sky-400 hover:text-sky-300 flex items-center gap-1 ml-1"
            >
              All Tickets <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-800/50 text-[11px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-3 px-6">Ticket ID</th>
                <th className="py-3 px-6">Passenger / PNR</th>
                <th className="py-3 px-6">Subject & Flight</th>
                <th className="py-3 px-6">Category</th>
                <th className="py-3 px-6">Priority</th>
                <th className="py-3 px-6">AI Confidence</th>
                <th className="py-3 px-6">Status</th>
                <th className="py-3 px-6 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {filteredTickets && filteredTickets.length > 0 ? (
                filteredTickets.slice(0, 10).map((t) => (
                  <tr key={t.id} className="hover:bg-slate-800/40 transition-colors">
                    {/* Ticket ID */}
                    <td className="py-4 px-6 font-mono text-xs font-bold text-sky-400">
                      {t.ticket_number || `#TK-${String(t.id).padStart(4, '0')}`}
                    </td>

                    {/* Passenger & PNR */}
                    <td className="py-4 px-6">
                      <div className="font-semibold text-white text-xs">
                        {t.passenger_name || t.reporter?.full_name || 'Passenger'}
                      </div>
                      <div className="text-[11px] font-mono text-slate-400 flex items-center gap-1.5 mt-0.5">
                        {t.booking_reference ? (
                          <span className="bg-slate-800 px-1.5 py-0.5 rounded border border-slate-700 text-sky-300 font-bold">
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
                      <span className="bg-slate-800/80 px-2 py-1 rounded-md border border-slate-700 text-[11px]">
                        {t.category}
                      </span>
                    </td>

                    {/* Priority */}
                    <td className="py-4 px-6">
                      <span className={`text-[11px] font-bold px-2 py-0.5 rounded border ${getPriorityBadge(t.classification?.priority || t.affected_service || 'Medium')}`}>
                        {t.classification?.priority || 'Medium'}
                      </span>
                    </td>

                    {/* AI Confidence */}
                    <td className="py-4 px-6">
                      {t.classification?.confidence_score !== undefined || t.ai_confidence !== undefined ? (
                        <div className="flex items-center gap-2">
                          <div className="w-14 bg-slate-800 rounded-full h-1.5 overflow-hidden border border-slate-700">
                            <div
                              className={`h-full rounded-full ${
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
                      <span className={`text-[11px] font-bold px-2 py-0.5 rounded border ${getStatusBadge(t.status)}`}>
                        {t.status === 'NEEDS_REVIEW' ? 'ESCALATED' : t.status}
                      </span>
                    </td>

                    {/* Action */}
                    <td className="py-4 px-6 text-right space-x-2">
                      <Link
                        to={`/ai-solution?ticketId=${t.id}`}
                        className="px-2.5 py-1.5 bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 rounded-lg text-xs font-medium transition-colors inline-flex items-center gap-1"
                        title="Open in AI Solution"
                      >
                        <Sparkles className="w-3 h-3" />
                        AI Sol
                      </Link>
                      <Link
                        to={`/tickets/${t.id}`}
                        className="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-xs font-medium transition-colors inline-flex items-center gap-1"
                      >
                        Details
                      </Link>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400 text-sm">
                    No tickets found matching your search.
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
