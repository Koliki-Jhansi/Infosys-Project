import React, { useEffect, useState, useCallback } from 'react';
import { ticketsApi } from '../services/api';
import { Ticket } from '../types';
import {
  Layers,
  RefreshCw,
  Search,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  AlertTriangle,
  CheckCircle2
} from 'lucide-react';

export const EscalatedTicketsPage: React.FC = () => {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [totalTickets, setTotalTickets] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  const fetchEscalated = useCallback(async (currentPage: number, search?: string) => {
    try {
      setLoading(true);
      const res = await ticketsApi.getEscalated({
        page: currentPage,
        size: pageSize,
        search: search && search.trim() ? search.trim() : undefined
      });
      setTickets(res.items || []);
      setTotalTickets(res.total || 0);
      setTotalPages(res.pages || 1);
    } catch (err) {
      console.error('Failed to load escalated tickets', err);
    } finally {
      setLoading(false);
    }
  }, [pageSize]);

  useEffect(() => {
    fetchEscalated(page, searchTerm);
  }, [page, searchTerm, fetchEscalated]);

  const handleRefresh = () => {
    fetchEscalated(page, searchTerm);
  };

  const getPriorityBadge = (priority?: string, urgency?: string) => {
    const val = priority || urgency || 'P3 Medium';
    if (val.includes('Critical') || val === 'Urgent') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
          {val}
        </span>
      );
    }
    if (val.includes('High')) {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-orange-50 text-orange-700 border border-orange-200">
          {val}
        </span>
      );
    }
    if (val.includes('Medium')) {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-sky-50 text-sky-700 border border-sky-200">
          {val}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-slate-50 text-slate-700 border border-slate-200">
        {val}
      </span>
    );
  };

  const getCriticalityBadge = (criticality?: string, impact?: string) => {
    const val = criticality || impact || 'Medium';
    if (val === 'Critical') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
          Critical
        </span>
      );
    }
    if (val === 'High') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
          High
        </span>
      );
    }
    if (val === 'Medium') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
          Medium
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-slate-50 text-slate-700 border border-slate-200">
        {val}
      </span>
    );
  };

  return (
    <div className="bg-[#FFFFFF] min-h-screen p-6 sm:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Escalated Tickets</h1>
          <p className="text-sm text-slate-500 mt-1">
            Displaying only flight support tickets that were successfully escalated and synced to Atlassian Jira Cloud.
          </p>
        </div>
        <button
          onClick={handleRefresh}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-medium text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 transition-colors shadow-sm self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-sky-600' : 'text-slate-500'}`} />
          <span>Refresh Escalated</span>
        </button>
      </div>

      {/* Main Table Card */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {/* Toolbar */}
        <div className="p-5 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-rose-50 flex items-center justify-center text-rose-600">
              <Layers className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900">Synchronized Jira Issues</h2>
              <p className="text-xs text-slate-500">
                {totalTickets} {totalTickets === 1 ? 'ticket' : 'tickets'} escalated to Jira
              </p>
            </div>
          </div>
          <div className="relative w-full sm:w-72">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by title, ticket ID, or Jira key..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(1);
              }}
              className="w-full pl-9 pr-3 py-2 text-xs rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent text-slate-800 placeholder-slate-400"
            />
          </div>
        </div>

        {/* Table Content */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 text-[11px] font-semibold text-slate-600 uppercase tracking-wider border-b border-slate-200">
                <th className="py-3 px-4">Ticket ID</th>
                <th className="py-3 px-4">Ticket Title</th>
                <th className="py-3 px-4">Priority</th>
                <th className="py-3 px-4">Criticality</th>
                <th className="py-3 px-4">AI Confidence</th>
                <th className="py-3 px-4">Jira Ticket ID</th>
                <th className="py-3 px-4">Escalation Status</th>
                <th className="py-3 px-4 text-right">Jira Link</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto text-sky-500 mb-2" />
                    <span>Loading escalated tickets...</span>
                  </td>
                </tr>
              ) : tickets.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    No escalated Jira tickets found.
                  </td>
                </tr>
              ) : (
                tickets.map((t) => {
                  const displayId = t.ticket_number || `TK-${t.id.toString().padStart(4, '0')}`;
                  const priority = t.classification?.priority || t.urgency;
                  const criticality = t.classification?.criticality || t.business_impact;
                  const confidence = t.ai_confidence;
                  const jiraRecord = t.jira_records && t.jira_records.length > 0 ? t.jira_records[0] : null;
                  const jiraKey = jiraRecord?.jira_key || '—';
                  const jiraStatus = jiraRecord?.status || 'Escalated';
                  const jiraUrl = jiraRecord?.jira_url;

                  return (
                    <tr key={t.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-3.5 px-4 font-mono font-medium text-sky-700">
                        {displayId}
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-slate-900 max-w-xs sm:max-w-sm truncate" title={t.title}>
                          {t.title}
                        </div>
                        <div className="text-[11px] text-slate-500">
                          {t.category} &bull; {t.passenger_name || 'Passenger'}
                        </div>
                      </td>
                      <td className="py-3.5 px-4">
                        {getPriorityBadge(priority, t.urgency)}
                      </td>
                      <td className="py-3.5 px-4">
                        {getCriticalityBadge(criticality, t.business_impact)}
                      </td>
                      <td className="py-3.5 px-4 font-mono font-medium">
                        {confidence !== null && confidence !== undefined ? (
                          <span className={confidence >= 70 ? 'text-emerald-700 font-semibold' : 'text-rose-600 font-semibold'}>
                            {confidence}%
                          </span>
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4 font-mono font-bold text-indigo-700">
                        {jiraKey}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
                          {jiraStatus}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        {jiraUrl ? (
                          <a
                            href={jiraUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 transition-colors"
                          >
                            <span>Open Jira</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        ) : (
                          <span className="text-slate-400 text-xs">No link</span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Controls */}
        <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between text-xs text-slate-600">
          <div>
            Showing Page <span className="font-semibold text-slate-900">{page}</span> of{' '}
            <span className="font-semibold text-slate-900">{totalPages}</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1 || loading}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md border border-slate-300 bg-white hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
              <span>Previous</span>
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages || loading}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md border border-slate-300 bg-white hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <span>Next</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EscalatedTicketsPage;
