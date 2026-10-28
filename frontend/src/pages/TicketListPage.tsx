import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { ticketsApi } from '../services/api';
import { Ticket } from '../types';
import {
  Inbox,
  Search,
  Filter,
  PlusCircle,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Clock,
  ArrowUpDown,
  Download,
  Plane,
  Sparkles,
  Bot,
  ExternalLink,
  Luggage,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react';

const AIRLINE_CATEGORIES = [
  'All',
  'Booking and Reservation',
  'Cancellation and Refund',
  'Flight Delay',
  'Flight Cancellation',
  'Baggage',
  'Check-in and Boarding',
  'Seat Selection',
  'Payment',
  'Special Assistance',
  'Other',
];

const STATUS_TABS = [
  { label: 'All Tickets', value: 'All' },
  { label: 'Open', value: 'OPEN' },
  { label: 'In Progress', value: 'IN_PROGRESS' },
  { label: 'AI Resolved', value: 'RESOLVED' },
  { label: 'Escalated', value: 'NEEDS_REVIEW' },
  { label: 'Closed', value: 'CLOSED' },
];

const PRIORITIES = ['All', 'Low', 'Medium', 'High', 'Urgent'];

export const TicketListPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [size] = useState(10);
  const [pages, setPages] = useState(1);

  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [category, setCategory] = useState(searchParams.get('category') || 'All');
  const [priorityFilter, setPriorityFilter] = useState('All');
  const [statusTab, setStatusTab] = useState(searchParams.get('status') || 'All');
  const [sortBy, setSortBy] = useState('created_at');
  const [order, setOrder] = useState<'asc' | 'desc'>('desc');
  const [loading, setLoading] = useState(true);

  const fetchTickets = async () => {
    try {
      setLoading(true);
      const params: any = {
        page,
        size,
        sort_by: sortBy,
        order,
      };
      if (search.trim()) params.search = search.trim();
      if (category !== 'All') params.category = category;
      
      // Handle OPEN tab which aggregates SUBMITTED and CLASSIFIED
      if (statusTab !== 'All') {
        if (statusTab === 'OPEN') {
          // fetch submitted or we can pass status=SUBMITTED
          params.status = 'SUBMITTED';
        } else {
          params.status = statusTab;
        }
      }

      const data = await ticketsApi.list(params);
      let items = data.items;

      // In-memory filter for priority if backend doesn't filter priority directly
      if (priorityFilter !== 'All') {
        items = items.filter(
          (t) =>
            t.classification?.priority === priorityFilter ||
            (priorityFilter === 'Urgent' && t.classification?.priority === 'P1 Critical') ||
            (priorityFilter === 'High' && t.classification?.priority === 'P2 High') ||
            (priorityFilter === 'Medium' && t.classification?.priority === 'P3 Medium') ||
            (priorityFilter === 'Low' && t.classification?.priority === 'P4 Low')
        );
      }

      setTickets(items);
      setTotal(data.total);
      setPages(data.pages);
    } catch (err) {
      console.error('Failed to list passenger tickets', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, [page, category, statusTab, priorityFilter, sortBy, order]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchTickets();
  };

  const handleTabChange = (val: string) => {
    setStatusTab(val);
    setPage(1);
    if (val === 'All') {
      searchParams.delete('status');
    } else {
      searchParams.set('status', val);
    }
    setSearchParams(searchParams);
  };

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

  // Export tickets as CSV
  const handleExportCSV = () => {
    if (!tickets || tickets.length === 0) return;
    const headers = ['ID', 'TicketNumber', 'Passenger', 'Email', 'PNR', 'Flight', 'Category', 'Priority', 'Status', 'Confidence', 'CreatedAt'];
    const rows = tickets.map((t) => [
      t.id,
      t.ticket_number || `TK-${t.id}`,
      `"${t.passenger_name || ''}"`,
      `"${t.passenger_email || ''}"`,
      `"${t.booking_reference || ''}"`,
      `"${t.flight_number || ''}"`,
      `"${t.category || ''}"`,
      `"${t.classification?.priority || 'Medium'}"`,
      `"${t.status}"`,
      t.ai_confidence ?? t.classification?.confidence_score ?? 'N/A',
      `"${t.created_at}"`,
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `AeroAssist_Tickets_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-fade-in-up">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="p-2.5 rounded-2xl bg-sky-500/10 text-sky-400 border border-sky-500/30 shadow-md shadow-sky-500/10">
              <Plane className="w-5 h-5 -rotate-45" />
            </span>
            <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white font-display">
              Ticket Management
            </h1>
          </div>
          <p className="text-sm text-slate-300 mt-1">
            Search and manage passenger inquiries, priority, confidence scores, and status.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleExportCSV}
            className="px-3.5 py-2.5 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700/80 text-slate-200 rounded-xl text-sm font-medium transition-all flex items-center gap-2 active:scale-95 shadow-sm"
            title="Export filtered tickets to CSV"
          >
            <Download className="w-4 h-4 text-sky-400" />
            Export CSV
          </button>
          <Link
            to="/tickets/new"
            className="btn-aviation px-4 py-2.5 bg-gradient-to-r from-sky-600 via-sky-500 to-blue-600 hover:from-sky-500 hover:to-blue-500 text-white rounded-xl text-sm font-semibold shadow-lg shadow-sky-500/25 transition-all flex items-center gap-2 active:scale-95"
          >
            <PlusCircle className="w-4 h-4" />
            New Ticket
          </Link>
        </div>
      </div>

      {/* Status Filter Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-slate-800/90 pb-3">
        {STATUS_TABS.map((tab) => {
          const isActive = statusTab === tab.value;
          return (
            <button
              key={tab.value}
              onClick={() => handleTabChange(tab.value)}
              className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all duration-200 ${
                isActive
                  ? 'bg-gradient-to-r from-sky-600 to-blue-600 text-white shadow-lg shadow-sky-500/25 border border-sky-400/30'
                  : 'aviation-glass-card bg-slate-900/60 border border-slate-800/80 text-slate-300 hover:bg-slate-800/80 hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Filter & Search Bar */}
      <div className="aviation-glass-card bg-slate-900/80 border border-slate-800/90 rounded-2xl p-4 shadow-xl backdrop-blur-xl space-y-4">
        <form onSubmit={handleSearchSubmit} className="flex flex-col lg:flex-row gap-3">
          {/* Search Box */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by ticket #, passenger name, PNR, flight #, or subject..."
              className="w-full pl-9 pr-4 py-2 bg-slate-800/80 border border-slate-700/80 rounded-xl text-sm text-white placeholder-slate-400 focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-500/30 transition-all"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* Category Filter */}
            <select
              value={category}
              onChange={(e) => {
                setCategory(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 bg-slate-800/80 border border-slate-700/80 rounded-xl text-xs text-white focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-500/30 transition-all cursor-pointer"
            >
              {AIRLINE_CATEGORIES.map((c) => (
                <option key={c} value={c} className="bg-slate-900 text-slate-200">
                  {c === 'All' ? 'All Categories' : c}
                </option>
              ))}
            </select>

            {/* Priority Filter */}
            <select
              value={priorityFilter}
              onChange={(e) => {
                setPriorityFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 bg-slate-800/80 border border-slate-700/80 rounded-xl text-xs text-white focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-500/30 transition-all cursor-pointer"
            >
              {PRIORITIES.map((p) => (
                <option key={p} value={p} className="bg-slate-900 text-slate-200">
                  {p === 'All' ? 'All Priorities' : `${p} Priority`}
                </option>
              ))}
            </select>

            {/* Sort Options */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3 py-2 bg-slate-800/80 border border-slate-700/80 rounded-xl text-xs text-white focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-500/30 transition-all cursor-pointer"
            >
              <option value="created_at" className="bg-slate-900 text-slate-200">Sort: Date</option>
              <option value="id" className="bg-slate-900 text-slate-200">Sort: Ticket ID</option>
            </select>

            <button
              type="button"
              onClick={() => setOrder(order === 'asc' ? 'desc' : 'asc')}
              className="p-2 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700/80 rounded-xl text-slate-300 text-xs flex items-center gap-1 active:scale-95 transition-all"
              title="Toggle Asc/Desc"
            >
              <ArrowUpDown className="w-3.5 h-3.5" />
              <span className="uppercase font-mono text-[11px]">{order}</span>
            </button>

            <button
              type="submit"
              className="btn-aviation px-4 py-2 bg-gradient-to-r from-sky-600 to-blue-600 hover:from-sky-500 hover:to-blue-500 text-white rounded-xl text-xs font-semibold shadow-md shadow-sky-500/25 transition-all flex items-center gap-1.5 active:scale-95"
            >
              <Filter className="w-3.5 h-3.5" />
              Filter
            </button>

            <button
              type="button"
              onClick={() => {
                setSearch('');
                setCategory('All');
                setPriorityFilter('All');
                setStatusTab('All');
                setPage(1);
                fetchTickets();
              }}
              className="p-2 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700/80 rounded-xl text-slate-400 hover:text-white text-xs transition-colors active:scale-95"
              title="Reset Filters"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
        </form>
      </div>

      {/* Ticket List Table */}
      <div className="aviation-glass-card bg-slate-900/80 border border-slate-800/90 rounded-2xl shadow-xl overflow-hidden backdrop-blur-xl">
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
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400 text-sm">
                    <div className="flex items-center justify-center gap-2">
                      <RefreshCw className="w-4 h-4 text-sky-400 animate-spin" />
                      Loading flight tickets...
                    </div>
                  </td>
                </tr>
              ) : tickets && tickets.length > 0 ? (
                tickets.map((t) => (
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
                        to={`/workflows?ticketId=${t.id}`}
                        className="px-2.5 py-1.5 bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 hover:text-indigo-300 border border-indigo-500/30 rounded-lg text-xs font-medium transition-all inline-flex items-center gap-1 active:scale-95 shadow-sm"
                        title="Run 5-Agent Workflow"
                      >
                        <Bot className="w-3 h-3 text-indigo-400" />
                        Agents
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
                    No tickets found matching the selected criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-4 border-t border-slate-800/80 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-400 font-mono">
          <div>
            Showing <span className="font-semibold text-white">{tickets.length}</span> of{' '}
            <span className="font-semibold text-white">{total}</span> total tickets
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page <= 1}
              className="px-3 py-1.5 bg-slate-800/80 hover:bg-slate-700/80 disabled:opacity-40 border border-slate-700 rounded-lg text-slate-200 transition-all flex items-center gap-1 active:scale-95"
            >
              <ChevronLeft className="w-3.5 h-3.5" /> Prev
            </button>
            <span className="px-2 font-mono text-white">
              Page {page} of {Math.max(1, pages)}
            </span>
            <button
              onClick={() => setPage(Math.min(pages, page + 1))}
              disabled={page >= pages}
              className="px-3 py-1.5 bg-slate-800/80 hover:bg-slate-700/80 disabled:opacity-40 border border-slate-700 rounded-lg text-slate-200 transition-all flex items-center gap-1 active:scale-95"
            >
              Next <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
