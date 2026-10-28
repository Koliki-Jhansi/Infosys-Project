import React, { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Sparkles,
  Bot,
  Play,
  RotateCw,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ExternalLink,
  Search,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  GitBranch,
  Mail,
  ShieldCheck,
  AlertCircle,
  X,
  Layers,
  FileText
} from 'lucide-react';
import { ticketsApi, aiSolutionApi } from '../services/api';
import { Ticket } from '../types';

interface AgentStageExecution {
  id?: number;
  agent_name: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  duration_ms?: number;
  outputs?: any;
  error_message?: string;
}

const REQUIRED_STAGES = [
  'Ticket Analysis Agent',
  'RAG Knowledge Retrieval Agent',
  'Priority and Criticality Analysis',
  'AI Solution Generation',
  'Confidence Evaluation',
  'Final Decision'
];

export const AiSolutionPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const initialTicketId = searchParams.get('ticketId') ? parseInt(searchParams.get('ticketId')!, 10) : null;

  // Tickets table state
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(8);
  const [totalTickets, setTotalTickets] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [tableLoading, setTableLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  // Processing state
  const [processingTickets, setProcessingTickets] = useState<Record<number, boolean>>({});
  const [activeTicketId, setActiveTicketId] = useState<number | null>(initialTicketId);
  const [activeTicket, setActiveTicket] = useState<Ticket | null>(null);

  // Workflow result & timeline state
  const [activeResult, setActiveResult] = useState<any | null>(null);
  const [workflowLoading, setWorkflowLoading] = useState(false);
  const [workflowError, setWorkflowError] = useState<string | null>(null);
  const [showWorkflowModal, setShowWorkflowModal] = useState(false);

  // Fetch tickets for table
  const fetchTickets = useCallback(async (currentPage: number, search?: string) => {
    try {
      setTableLoading(true);
      const res = await ticketsApi.list({
        page: currentPage,
        size: pageSize,
        search: search && search.trim() ? search.trim() : undefined
      });
      setTickets(res.items || []);
      setTotalTickets(res.total || 0);
      setTotalPages(res.pages || 1);
    } catch (err) {
      console.error('Failed to load tickets', err);
    } finally {
      setTableLoading(false);
    }
  }, [pageSize]);

  useEffect(() => {
    fetchTickets(page, searchTerm);
  }, [page, searchTerm, fetchTickets]);

  // Load ticket details and workflow when activeTicketId changes
  const loadTicketWorkflow = useCallback(async (ticketId: number) => {
    try {
      setWorkflowLoading(true);
      setWorkflowError(null);
      const t = await ticketsApi.getById(ticketId);
      setActiveTicket(t);

      const res = await aiSolutionApi.getResults(ticketId);
      setActiveResult(res);
    } catch (err: any) {
      console.error('Failed to load workflow results', err);
      setWorkflowError(err.message || 'Failed to load workflow data');
    } finally {
      setWorkflowLoading(false);
    }
  }, []);

  useEffect(() => {
    if (initialTicketId) {
      setActiveTicketId(initialTicketId);
      loadTicketWorkflow(initialTicketId);
      setShowWorkflowModal(true);
    }
  }, [initialTicketId, loadTicketWorkflow]);

  // Run AI Solution for selected ticket
  const handleRunAiSolution = async (ticket: Ticket) => {
    if (processingTickets[ticket.id]) return; // Prevent duplicate requests

    setProcessingTickets((prev) => ({ ...prev, [ticket.id]: true }));
    setActiveTicketId(ticket.id);
    setActiveTicket(ticket);
    setWorkflowError(null);
    setWorkflowLoading(true);
    setShowWorkflowModal(true);

    try {
      const result = await aiSolutionApi.resolve(ticket.id);
      setActiveResult(result);

      // Refresh ticket list to update status, priority, criticality, and confidence in the table
      fetchTickets(page, searchTerm);
    } catch (err: any) {
      console.error('AI solution execution failed', err);
      setWorkflowError(err.message || 'AI solution processing failed. Please try again.');
    } finally {
      setProcessingTickets((prev) => ({ ...prev, [ticket.id]: false }));
      setWorkflowLoading(false);
    }
  };

  // View Multi-Agent Workflow button handler
  const handleViewWorkflow = async (ticket: Ticket) => {
    setActiveTicketId(ticket.id);
    setActiveTicket(ticket);
    setShowWorkflowModal(true);
    loadTicketWorkflow(ticket.id);
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

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'RESOLVED':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
            AI Resolved
          </span>
        );
      case 'NEEDS_REVIEW':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
            Escalated
          </span>
        );
      case 'IN_PROGRESS':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-200">
            In Progress
          </span>
        );
      case 'CLOSED':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-50 text-slate-600 border border-slate-200">
            Closed
          </span>
        );
      case 'SUBMITTED':
      case 'CLASSIFIED':
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-sky-50 text-sky-700 border border-sky-200">
            Open
          </span>
        );
    }
  };

  // Helper to construct normalized 6-stage timeline
  const buildTimelineStages = (): AgentStageExecution[] => {
    const rawExecutions: any[] = activeResult?.agent_executions || [];
    const isProcessing = activeTicketId ? Boolean(processingTickets[activeTicketId]) : false;

    return REQUIRED_STAGES.map((stageName) => {
      // Find matching execution by name
      const match = rawExecutions.find((a) => {
        const name = (a.agent_name || '').toLowerCase();
        if (stageName === 'Ticket Analysis Agent') return name.includes('diagnosis') || name.includes('ticket analysis');
        if (stageName === 'RAG Knowledge Retrieval Agent') return name.includes('retrieval');
        if (stageName === 'Priority and Criticality Analysis') return name.includes('priority');
        if (stageName === 'AI Solution Generation') return name.includes('resolution') || name.includes('solution');
        if (stageName === 'Confidence Evaluation') return name.includes('validation') || name.includes('confidence');
        if (stageName === 'Final Decision') return name.includes('escalation') || name.includes('decision');
        return false;
      });

      if (match) {
        return {
          id: match.id,
          agent_name: stageName,
          status: match.status === 'COMPLETED' ? 'COMPLETED' : match.status === 'FAILED' ? 'FAILED' : 'RUNNING',
          duration_ms: match.duration_ms,
          outputs: match.outputs,
          error_message: match.error_message
        };
      }

      if (isProcessing) {
        return {
          agent_name: stageName,
          status: 'RUNNING'
        };
      }

      return {
        agent_name: stageName,
        status: 'PENDING'
      };
    });
  };

  const timelineStages = buildTimelineStages();
  const isCurrentlyProcessing = activeTicketId ? Boolean(processingTickets[activeTicketId]) : false;

  return (
    <div className="bg-[#FFFFFF] min-h-screen p-6 sm:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">AI Solutions</h1>
          <p className="text-sm text-slate-500 mt-1">
            Grounded AI processing, autonomous multi-agent workflow, and confidence-based decision engine
          </p>
        </div>
        <button
          onClick={() => fetchTickets(page, searchTerm)}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-medium text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 transition-colors shadow-sm self-start sm:self-auto"
        >
          <RotateCw className={`w-3.5 h-3.5 ${tableLoading ? 'animate-spin text-sky-600' : 'text-slate-500'}`} />
          <span>Refresh Tickets</span>
        </button>
      </div>

      {/* Main Tickets Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {/* Table Toolbar */}
        <div className="p-5 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Eligible Flight Support Tickets</h2>
            <p className="text-xs text-slate-500">
              Select any ticket to trigger the RAG multi-agent resolution workflow
            </p>
          </div>
          <div className="relative w-full sm:w-72">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by title, ID, or passenger..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(1);
              }}
              className="w-full pl-9 pr-3 py-2 text-xs rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent text-slate-800 placeholder-slate-400"
            />
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 text-[11px] font-semibold text-slate-600 uppercase tracking-wider border-b border-slate-200">
                <th className="py-3 px-4">Ticket ID</th>
                <th className="py-3 px-4">Ticket Title</th>
                <th className="py-3 px-4">Priority</th>
                <th className="py-3 px-4">Criticality</th>
                <th className="py-3 px-4">AI Confidence</th>
                <th className="py-3 px-4">Current Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
              {tableLoading ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    <RotateCw className="w-6 h-6 animate-spin mx-auto text-sky-500 mb-2" />
                    <span>Loading tickets...</span>
                  </td>
                </tr>
              ) : tickets.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    No tickets available for processing.
                  </td>
                </tr>
              ) : (
                tickets.map((t) => {
                  const displayId = t.ticket_number || `TK-${t.id.toString().padStart(4, '0')}`;
                  const priority = t.classification?.priority || t.urgency;
                  const criticality = t.classification?.criticality || t.business_impact;
                  const confidence = t.ai_confidence;
                  const isProcessing = Boolean(processingTickets[t.id]);

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
                          <span className={confidence >= 70 ? 'text-emerald-700 font-semibold' : 'text-amber-700 font-semibold'}>
                            {confidence}%
                          </span>
                        ) : (
                          <span className="text-slate-400 font-normal">Not processed</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        {getStatusBadge(t.status)}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <div className="inline-flex items-center gap-2">
                          {/* Run AI Solution Button */}
                          <button
                            onClick={() => handleRunAiSolution(t)}
                            disabled={isProcessing}
                            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all shadow-sm ${
                              isProcessing
                                ? 'bg-sky-100 text-sky-500 cursor-not-allowed'
                                : 'bg-sky-600 text-white hover:bg-sky-700 active:scale-95'
                            }`}
                          >
                            {isProcessing ? (
                              <>
                                <RotateCw className="w-3.5 h-3.5 animate-spin" />
                                <span>Running AI...</span>
                              </>
                            ) : (
                              <>
                                <Sparkles className="w-3.5 h-3.5" />
                                <span>Run AI Solution</span>
                              </>
                            )}
                          </button>

                          {/* View Multi-Agent Workflow Button */}
                          <button
                            onClick={() => handleViewWorkflow(t)}
                            className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 border border-slate-200 transition-colors"
                            title="View Multi-Agent Workflow Details"
                          >
                            <GitBranch className="w-3.5 h-3.5 text-indigo-600" />
                            <span className="hidden md:inline">Workflow</span>
                          </button>
                        </div>
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
              disabled={page <= 1 || tableLoading}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md border border-slate-300 bg-white hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
              <span>Previous</span>
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages || tableLoading}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md border border-slate-300 bg-white hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <span>Next</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Multi-Agent Workflow & Results Panel / Modal */}
      {showWorkflowModal && activeTicket && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-sky-100 flex items-center justify-center text-sky-700">
                  <Bot className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-sky-700">
                      {activeTicket.ticket_number || `TK-${activeTicket.id.toString().padStart(4, '0')}`}
                    </span>
                    <span className="text-slate-300">&bull;</span>
                    <h3 className="text-sm font-bold text-slate-900 truncate max-w-md">
                      {activeTicket.title}
                    </h3>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Category: {activeTicket.category} &bull; Passenger: {activeTicket.passenger_name || 'Passenger'}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowWorkflowModal(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto space-y-6 flex-1 text-xs">
              {workflowError && (
                <div className="p-3.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{workflowError}</span>
                </div>
              )}

              {/* 1. Compact Multi-Agent Workflow Timeline */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                    <GitBranch className="w-4 h-4 text-indigo-600" />
                    Multi-Agent Workflow Stages
                  </h4>
                  {isCurrentlyProcessing && (
                    <span className="inline-flex items-center gap-1.5 text-xs text-sky-600 font-semibold animate-pulse">
                      <RotateCw className="w-3.5 h-3.5 animate-spin" />
                      Executing Pipeline...
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {timelineStages.map((stage, idx) => {
                    const isCompleted = stage.status === 'COMPLETED';
                    const isRunning = stage.status === 'RUNNING';
                    const isFailed = stage.status === 'FAILED';

                    return (
                      <div
                        key={idx}
                        className={`p-3.5 rounded-xl border transition-all ${
                          isCompleted
                            ? 'bg-emerald-50/50 border-emerald-200'
                            : isRunning
                            ? 'bg-sky-50/50 border-sky-300 ring-2 ring-sky-200'
                            : isFailed
                            ? 'bg-rose-50 border-rose-200'
                            : 'bg-slate-50 border-slate-200 opacity-60'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-mono font-bold text-slate-400">
                            STAGE {idx + 1}
                          </span>
                          {isCompleted ? (
                            <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700">
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              Completed
                            </span>
                          ) : isRunning ? (
                            <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-sky-700 animate-pulse">
                              <RotateCw className="w-3.5 h-3.5 animate-spin" />
                              Running
                            </span>
                          ) : isFailed ? (
                            <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-700">
                              <AlertTriangle className="w-3.5 h-3.5" />
                              Failed
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-[11px] text-slate-400">
                              <Clock className="w-3 h-3" />
                              Pending
                            </span>
                          )}
                        </div>

                        <div className="font-semibold text-slate-900 mt-1.5">
                          {stage.agent_name}
                        </div>

                        {stage.duration_ms !== undefined && (
                          <div className="text-[10px] text-slate-500 mt-1">
                            Duration: {stage.duration_ms} ms
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* 2. Confidence Evaluation & Final Decision Banner */}
              {activeResult && activeResult.confidence_score !== undefined && (
                <div
                  className={`p-5 rounded-xl border ${
                    activeResult.confidence_score >= 70
                      ? 'bg-emerald-50/70 border-emerald-300'
                      : 'bg-amber-50/70 border-amber-300'
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs uppercase font-bold tracking-wider text-slate-600">
                          Final AI Confidence Score:
                        </span>
                        <span
                          className={`text-2xl font-extrabold ${
                            activeResult.confidence_score >= 70 ? 'text-emerald-700' : 'text-amber-700'
                          }`}
                        >
                          {activeResult.confidence_score}%
                        </span>
                        <span className="text-xs font-semibold px-2 py-0.5 rounded bg-white border border-slate-300 text-slate-600">
                          Threshold: 70%
                        </span>
                      </div>
                      <div className="text-xs text-slate-700 mt-1.5">
                        <strong>Decision: </strong>
                        {activeResult.decision === 'ESCALATED' ? (
                          <span className="text-amber-800 font-semibold">
                            Confidence below 70% threshold &bull; Escalated to Atlassian Jira Cloud
                          </span>
                        ) : (
                          <span className="text-emerald-800 font-semibold">
                            Confidence 70% or higher &bull; Automated AI Resolution Approved
                          </span>
                        )}
                      </div>
                      {activeResult.decision_summary && (
                        <p className="text-[11px] text-slate-600 mt-1">
                          {activeResult.decision_summary}
                        </p>
                      )}
                    </div>

                    {/* Jira / Email status box */}
                    <div className="self-start sm:self-auto flex flex-col items-end gap-2">
                      {/* Jira status if escalated */}
                      {activeResult.jira && (
                        <div className="bg-white p-3 rounded-lg border border-amber-200 shadow-sm text-right">
                          <div className="text-[11px] text-slate-500">Jira Ticket Created:</div>
                          <div className="font-mono font-bold text-indigo-700 text-sm">
                            {activeResult.jira.jira_key}
                          </div>
                          {activeResult.jira.jira_url && (
                            <a
                              href={activeResult.jira.jira_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 text-[11px] font-semibold text-indigo-600 hover:text-indigo-800 underline mt-1"
                            >
                              <span>Open Jira Issue</span>
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          )}
                        </div>
                      )}

                      {/* Jira error with safe retry */}
                      {activeResult.jira_error && (
                        <div className="bg-white p-3 rounded-lg border border-rose-200 text-right">
                          <div className="text-rose-700 text-xs font-medium">Jira Creation Failed:</div>
                          <div className="text-[11px] text-slate-600">{activeResult.jira_error}</div>
                          <button
                            onClick={() => handleRunAiSolution(activeTicket)}
                            className="mt-2 text-xs font-semibold px-2.5 py-1 rounded bg-rose-600 text-white hover:bg-rose-700"
                          >
                            Retry Jira Escalation
                          </button>
                        </div>
                      )}

                      {/* Email delivery if >= 70% */}
                      {activeResult.email_delivery && (
                        <div className="bg-white p-3 rounded-lg border border-emerald-200 shadow-sm text-right">
                          <div className="flex items-center justify-end gap-1 text-[11px] text-slate-500">
                            <Mail className="w-3.5 h-3.5 text-emerald-600" />
                            <span>Passenger Email Dispatch:</span>
                          </div>
                          <div className="text-xs font-semibold mt-0.5">
                            {activeResult.email_delivery.status === 'DELIVERED' ? (
                              <span className="text-emerald-700">Delivered</span>
                            ) : activeResult.email_delivery.status === 'SERVICE_NOT_CONFIGURED' ? (
                              <span className="text-amber-700">Service Not Configured (SMTP)</span>
                            ) : (
                              <span className="text-rose-700">{activeResult.email_delivery.status}</span>
                            )}
                          </div>
                          <p className="text-[10px] text-slate-500 max-w-xs mt-0.5">
                            {activeResult.email_delivery.message}
                          </p>
                          {!activeResult.email_delivery.success && (
                            <button
                              onClick={() => handleRunAiSolution(activeTicket)}
                              className="mt-1.5 text-[11px] font-medium px-2 py-0.5 rounded bg-slate-100 hover:bg-slate-200 border border-slate-300 text-slate-700"
                            >
                              Retry Delivery
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* 3. Generated Grounded Solution */}
              {activeResult?.generated_response && (
                <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2 flex items-center gap-1.5">
                    <FileText className="w-3.5 h-3.5 text-sky-600" />
                    AI-Generated Grounded Solution
                  </h4>
                  <div className="bg-slate-50 rounded-lg p-3.5 text-xs text-slate-800 font-sans whitespace-pre-wrap leading-relaxed border border-slate-200">
                    {activeResult.generated_response}
                  </div>
                </div>
              )}

              {/* 4. Relevant Retrieved Knowledge Sources */}
              {activeResult?.retrieved_sources && activeResult.retrieved_sources.length > 0 && (
                <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-1.5">
                    <BookOpen className="w-3.5 h-3.5 text-sky-600" />
                    Retrieved Knowledge Sources ({activeResult.retrieved_sources.length})
                  </h4>
                  <div className="space-y-2">
                    {activeResult.retrieved_sources.map((src: any, idx: number) => (
                      <div key={idx} className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-slate-900">
                            {src.document_title || `Document #${src.document_id || idx + 1}`}
                          </span>
                          {src.relevance_score && (
                            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-sky-100 text-sky-800 font-semibold">
                              Score: {Math.round(src.relevance_score * 100)}%
                            </span>
                          )}
                        </div>
                        {src.excerpt && (
                          <p className="text-slate-600 text-[11px] mt-1.5 line-clamp-2">
                            "{src.excerpt}"
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
              <span className="text-xs text-slate-500 font-mono">
                Ticket Status: <strong>{activeTicket.status}</strong>
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleRunAiSolution(activeTicket)}
                  disabled={isCurrentlyProcessing}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-white bg-sky-600 hover:bg-sky-700 disabled:opacity-50 transition-colors shadow-sm"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Re-Run AI Workflow</span>
                </button>
                <button
                  onClick={() => setShowWorkflowModal(false)}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-700 bg-white border border-slate-300 hover:bg-slate-100 transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AiSolutionPage;
