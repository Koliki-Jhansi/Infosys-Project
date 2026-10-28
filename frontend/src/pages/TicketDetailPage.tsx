import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ticketsApi, reviewsApi, jiraApi } from '../services/api';
import { Ticket, TicketNote, JiraRecord } from '../types';
import { useAuth } from '../features/auth/AuthContext';
import {
  Clock,
  User,
  Shield,
  AlertTriangle,
  CheckCircle2,
  Cpu,
  RefreshCw,
  ArrowLeft,
  Check,
  X,
  Sliders,
  Sparkles,
  Send,
  MessageSquare,
  Bot,
  ExternalLink,
  CheckCheck,
  Layers
} from 'lucide-react';

export const TicketDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { isSupport, user } = useAuth();

  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [loading, setLoading] = useState(true);
  const [reclassifying, setReclassifying] = useState(false);
  const [reviewModalOpen, setReviewModalOpen] = useState(false);
  const [reviewAction, setReviewAction] = useState<'APPROVE' | 'REJECT' | 'OVERRIDE'>('APPROVE');
  const [reviewNotes, setReviewNotes] = useState('');
  const [overrideCategory, setOverrideCategory] = useState('');
  const [overridePriority, setOverridePriority] = useState('');
  const [reviewSubmitting, setReviewSubmitting] = useState(false);
  const [message, setMessage] = useState('');

  // Internal Notes State
  const [newNote, setNewNote] = useState('');
  const [submittingNote, setSubmittingNote] = useState(false);

  // Status Action State
  const [actionLoading, setActionLoading] = useState(false);

  // Jira Sync State
  const [syncingJira, setSyncingJira] = useState(false);
  const [refreshingJira, setRefreshingJira] = useState(false);

  const handleSyncToJira = async () => {
    if (!ticket) return;
    try {
      setSyncingJira(true);
      const rec = await jiraApi.createTicketIssue(ticket.id);
      setTicket({
        ...ticket,
        jira_records: [rec]
      });
      setMessage(`Ticket #${ticket.id} dispatched to Jira Cloud: ${rec.jira_key}`);
    } catch (err: any) {
      console.error('Failed to sync ticket to Jira', err);
      setMessage(err.response?.data?.detail || 'Failed to sync to Jira Cloud.');
    } finally {
      setSyncingJira(false);
    }
  };

  const handleRefreshJira = async () => {
    if (!ticket) return;
    try {
      setRefreshingJira(true);
      const rec = await jiraApi.refreshTicketJira(ticket.id);
      setTicket({
        ...ticket,
        jira_records: [rec]
      });
      setMessage(`Jira Cloud status refreshed: ${rec.jira_key} (${rec.status})`);
    } catch (err: any) {
      console.error('Failed to refresh Jira status', err);
    } finally {
      setRefreshingJira(false);
    }
  };

  const loadTicket = async () => {
    if (!id) return;
    try {
      setLoading(true);
      const data = await ticketsApi.getById(parseInt(id, 10));
      setTicket(data);
      if (data.classification) {
        setOverrideCategory(data.classification.predicted_category);
        setOverridePriority(data.classification.priority);
      }
    } catch (err) {
      console.error('Failed to load passenger ticket', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTicket();
  }, [id]);

  const handleReclassify = async () => {
    if (!ticket) return;
    try {
      setReclassifying(true);
      await ticketsApi.classify(ticket.id);
      setMessage('Ticket successfully reclassified with airline policy evaluation.');
      await loadTicket();
    } catch (err) {
      console.error('Reclassification failed', err);
    } finally {
      setReclassifying(false);
    }
  };

  const handleResolve = async () => {
    if (!ticket) return;
    try {
      setActionLoading(true);
      await ticketsApi.resolve(ticket.id, { response: 'Marked as resolved.' });
      setMessage('Ticket marked as RESOLVED successfully.');
      await loadTicket();
    } catch (err: any) {
      console.error('Failed to resolve ticket', err);
      setMessage(err.response?.data?.detail || 'Failed to resolve ticket.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleEscalate = async () => {
    if (!ticket) return;
    try {
      setActionLoading(true);
      await ticketsApi.escalate(ticket.id, { reason: 'Manual escalation requested for senior agent attention.' });
      setMessage('Ticket escalated to human supervisor queue.');
      await loadTicket();
    } catch (err) {
      console.error('Failed to escalate ticket', err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticket || !newNote.trim()) return;
    try {
      setSubmittingNote(true);
      await ticketsApi.addNote(ticket.id, { content: newNote.trim(), message_type: 'INTERNAL_NOTE' });
      setNewNote('');
      setMessage('Internal support note recorded.');
      await loadTicket();
    } catch (err) {
      console.error('Failed to add note', err);
    } finally {
      setSubmittingNote(false);
    }
  };

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticket) return;
    try {
      setReviewSubmitting(true);
      await reviewsApi.reviewTicket(ticket.id, {
        action: reviewAction,
        notes: reviewNotes,
        override_category: reviewAction === 'OVERRIDE' ? overrideCategory : undefined,
        override_priority: reviewAction === 'OVERRIDE' ? overridePriority : undefined,
      });
      setReviewModalOpen(false);
      setMessage(`Review completed (${reviewAction}). Status updated.`);
      await loadTicket();
    } catch (err) {
      console.error('Review failed', err);
    } finally {
      setReviewSubmitting(false);
    }
  };

  if (loading && !ticket) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] space-y-4">
        <RefreshCw className="w-8 h-8 text-sky-400 animate-spin" />
        <p className="text-slate-400 text-sm">Loading passenger ticket details...</p>
      </div>
    );
  }

  if (!ticket) {
    return (
      <div className="p-8 text-center text-slate-400">
        <p>Ticket #{id} not found.</p>
        <Link to="/tickets" className="text-sky-400 hover:underline mt-2 inline-block">
          &larr; Back to all tickets
        </Link>
      </div>
    );
  }

  const c = ticket.classification;
  const confidenceScore = ticket.ai_confidence ?? c?.confidence_score ?? 0;
  const isHighConfidence = confidenceScore >= 70;

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12 animate-fade-in-up">
      {/* Top Breadcrumb & Action Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 aviation-glass-card bg-slate-900/80 p-5 rounded-2xl border border-slate-800/90 shadow-xl backdrop-blur-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-sky-500/5 rounded-full blur-2xl pointer-events-none" />
        <div className="flex items-center gap-3 relative z-10">
          <Link
            to="/tickets"
            className="p-2.5 bg-slate-800/90 hover:bg-slate-700/90 text-slate-200 rounded-xl transition-all border border-slate-700/80 active:scale-95 shadow-sm"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-mono text-sky-400 font-bold bg-sky-500/10 px-2.5 py-0.5 rounded-lg border border-sky-500/30">
                {ticket.ticket_number || `#TK-${String(ticket.id).padStart(4, '0')}`}
              </span>
              <span
                className={`text-xs font-bold px-2.5 py-0.5 rounded-full border backdrop-blur-sm ${
                  ticket.status === 'NEEDS_REVIEW'
                    ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                    : ticket.status === 'RESOLVED'
                    ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                    : ticket.status === 'IN_PROGRESS'
                    ? 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40'
                    : 'bg-sky-500/20 text-sky-300 border-sky-500/40'
                }`}
              >
                {ticket.status === 'NEEDS_REVIEW' ? 'ESCALATED' : ticket.status}
              </span>
              {ticket.booking_reference && (
                <span className="text-xs font-mono font-bold bg-sky-500/10 text-sky-300 px-2 py-0.5 rounded-md border border-sky-500/25">
                  PNR: {ticket.booking_reference}
                </span>
              )}
              {ticket.flight_number && (
                <span className="text-xs font-mono text-slate-300 bg-slate-800/90 px-2 py-0.5 rounded-md border border-slate-700/80">
                  Flight {ticket.flight_number}
                </span>
              )}
            </div>
            <h1 className="text-xl md:text-2xl font-bold text-white mt-1.5 tracking-tight font-display">
              {ticket.title}
            </h1>
          </div>
        </div>

        {/* Operational Actions */}
        <div className="flex flex-wrap items-center gap-2 relative z-10">
          {/* Resolve Button */}
          {ticket.status !== 'RESOLVED' && (
            <button
              onClick={handleResolve}
              disabled={actionLoading}
              className="btn-aviation px-3.5 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white rounded-xl text-xs font-semibold shadow-md shadow-emerald-500/25 transition-all flex items-center gap-1.5 active:scale-95"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              Resolve
            </button>
          )}

          {/* Escalate Button */}
          {ticket.status !== 'NEEDS_REVIEW' && (
            <button
              onClick={handleEscalate}
              disabled={actionLoading}
              className="btn-aviation px-3.5 py-2 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white rounded-xl text-xs font-semibold shadow-md shadow-amber-500/25 transition-all flex items-center gap-1.5 active:scale-95"
            >
              <AlertTriangle className="w-3.5 h-3.5" />
              Escalate
            </button>
          )}

          {/* AI Solution Trigger */}
          <Link
            to={`/ai-solution?ticketId=${ticket.id}`}
            className="btn-aviation px-3.5 py-2 bg-gradient-to-r from-sky-600 to-blue-600 hover:from-sky-500 hover:to-blue-500 text-white rounded-xl text-xs font-semibold shadow-md shadow-sky-500/25 transition-all flex items-center gap-1.5 active:scale-95"
          >
            <Sparkles className="w-3.5 h-3.5" />
            AI Solution
          </Link>

          {/* Multi-Agent Workflow Trigger */}
          <Link
            to={`/ai-solution?ticketId=${ticket.id}`}
            className="btn-aviation px-3.5 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-xl text-xs font-semibold shadow-md shadow-indigo-500/25 transition-all flex items-center gap-1.5 active:scale-95"
          >
            <Bot className="w-3.5 h-3.5" />
            View Multi-Agent Workflow
          </Link>

          {/* Reclassify */}
          <button
            onClick={handleReclassify}
            disabled={reclassifying}
            className="px-3 py-2 bg-slate-800/90 hover:bg-slate-700/90 border border-slate-700/80 text-slate-200 rounded-xl text-xs font-medium transition-all flex items-center gap-1.5 active:scale-95 shadow-sm"
            title="Re-run policy classification"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${reclassifying ? 'animate-spin text-sky-400' : 'text-slate-400'}`} />
            {reclassifying ? 'Evaluating...' : 'Reclassify'}
          </button>

          {/* Jira Sync Shortcut */}
          {ticket.jira_records && ticket.jira_records.length > 0 ? (
            <Link
              to="/jira"
              className="px-3 py-2 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/30 text-blue-300 rounded-xl text-xs font-medium transition-all flex items-center gap-1.5 active:scale-95 shadow-sm font-mono"
            >
              <Layers className="w-3.5 h-3.5 text-blue-400" />
              {ticket.jira_records[0].jira_key}
            </Link>
          ) : isSupport && (
            <button
              onClick={handleSyncToJira}
              disabled={syncingJira}
              className="px-3 py-2 bg-slate-800/90 hover:bg-slate-700/90 border border-slate-700/80 text-cyan-300 rounded-xl text-xs font-medium transition-all flex items-center gap-1.5 active:scale-95 shadow-sm cursor-pointer"
              title="Sync ticket to Jira Cloud"
            >
              <Layers className={`w-3.5 h-3.5 ${syncingJira ? 'animate-spin text-cyan-400' : 'text-cyan-400'}`} />
              {syncingJira ? 'Syncing...' : 'Sync Jira'}
            </button>
          )}
        </div>
      </div>

      {message && (
        <div className="p-3.5 rounded-xl bg-sky-500/10 border border-sky-500/30 text-sky-300 text-sm flex items-center justify-between">
          <span>{message}</span>
          <button onClick={() => setMessage('')} className="text-slate-400 hover:text-white">
            &times;
          </button>
        </div>
      )}

      {/* Escalation Warning */}
      {ticket.status === 'NEEDS_REVIEW' && (
        <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-200 text-sm flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-bold">Escalated for Human Support Agent Review</span>
            <p className="text-xs text-amber-300/90 leading-relaxed">
              {c?.review_reason || 'This passenger inquiry requires human oversight due to policy confidence thresholds or safety guidelines.'}
            </p>
          </div>
        </div>
      )}

      {/* Main Grid: Left Dossier (7 Cols) & Right AI Intelligence (5 Cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Passenger Dossier & Notes */}
        <div className="lg:col-span-7 space-y-6">
          {/* Passenger & Ticket Information Card */}
          <div className="aviation-glass-card bg-slate-900/80 border border-slate-800/90 rounded-2xl p-6 shadow-xl backdrop-blur-xl space-y-5">
            <h2 className="text-xs font-bold uppercase tracking-wider text-sky-400 flex items-center gap-2 font-mono">
              <User className="w-4 h-4 text-sky-400" /> Passenger & Booking Dossier
            </h2>

            {/* Passenger Attributes Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 bg-slate-950/70 rounded-xl border border-slate-800/80 text-xs">
              <div>
                <span className="text-slate-400 block text-[11px]">Passenger Name</span>
                <span className="font-semibold text-white mt-0.5 block">
                  {ticket.passenger_name || ticket.reporter?.full_name || 'Passenger'}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Contact Email</span>
                <span className="font-semibold text-white mt-0.5 block truncate">
                  {ticket.passenger_email || ticket.reporter?.email || 'N/A'}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Booking PNR</span>
                <span className="font-semibold text-sky-400 font-mono mt-0.5 block">
                  {ticket.booking_reference || 'N/A'}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Flight Number</span>
                <span className="font-semibold text-emerald-400 font-mono mt-0.5 block">
                  {ticket.flight_number || 'N/A'}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Travel Date</span>
                <span className="font-semibold text-white mt-0.5 block">
                  {ticket.travel_date || 'N/A'}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Category</span>
                <span className="font-semibold text-white mt-0.5 block">{ticket.category}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Priority</span>
                <span className="font-semibold text-white mt-0.5 block">
                  {ticket.classification?.priority || ticket.urgency || 'Medium'}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Created At</span>
                <span className="font-semibold text-white font-mono mt-0.5 block">
                  {new Date(ticket.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>

            {/* Passenger Description */}
            <div>
              <span className="text-xs font-semibold text-slate-300 block mb-1.5">
                Detailed Passenger Inquiry
              </span>
              <p className="text-sm text-slate-200 leading-relaxed bg-slate-950/70 p-4 rounded-xl border border-slate-800/80 whitespace-pre-wrap">
                {ticket.description}
              </p>
            </div>

            {/* AI Generated Resolution if available */}
            {ticket.final_response && (
              <div className="pt-2 border-t border-slate-800/80">
                <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider block mb-2 flex items-center gap-1.5 font-mono">
                  <CheckCheck className="w-4 h-4 text-emerald-400" /> AI Generated Passenger Solution
                </span>
                <div className="text-sm text-slate-200 leading-relaxed bg-emerald-950/20 border border-emerald-500/30 p-4 rounded-xl whitespace-pre-wrap">
                  {ticket.final_response}
                </div>
              </div>
            )}
          </div>

          {/* Internal Notes & Support Staff Communication */}
          <div className="aviation-glass-card bg-slate-900/80 border border-slate-800/90 rounded-2xl p-6 shadow-xl backdrop-blur-xl space-y-4">
            <h2 className="text-xs font-bold uppercase tracking-wider text-sky-400 flex items-center gap-2 font-mono">
              <MessageSquare className="w-4 h-4 text-sky-400" /> Internal Agent Notes & Comments
            </h2>

            {/* Notes List */}
            <div className="space-y-3">
              {ticket.notes && ticket.notes.length > 0 ? (
                ticket.notes.map((n: TicketNote) => (
                  <div key={n.id} className="p-3.5 bg-slate-950/70 rounded-xl border border-slate-800/80 space-y-1 text-xs">
                    <div className="flex items-center justify-between text-slate-400">
                      <span className="font-semibold text-white flex items-center gap-1.5">
                        <User className="w-3.5 h-3.5 text-sky-400" />
                        {n.author?.full_name || 'Support Staff'}
                      </span>
                      <span className="font-mono text-[11px]">
                        {new Date(n.created_at).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-slate-300 pt-1 leading-relaxed">{n.content}</p>
                  </div>
                ))
              ) : (
                <p className="text-xs text-slate-400 italic">No internal agent notes added yet.</p>
              )}
            </div>

            {/* Add Note Form */}
            <form onSubmit={handleAddNote} className="pt-3 border-t border-slate-800/80 flex gap-2">
              <input
                type="text"
                value={newNote}
                onChange={(e) => setNewNote(e.target.value)}
                placeholder="Add an internal note or agent dispatch comment..."
                className="flex-1 px-3.5 py-2 bg-slate-800/80 border border-slate-700/80 rounded-xl text-xs text-white placeholder-slate-400 focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-500/30 transition-all"
              />
              <button
                type="submit"
                disabled={submittingNote || !newNote.trim()}
                className="btn-aviation px-4 py-2 bg-gradient-to-r from-sky-600 to-blue-600 hover:from-sky-500 hover:to-blue-500 disabled:opacity-40 text-white rounded-xl text-xs font-semibold shadow-md shadow-sky-500/20 transition-all flex items-center gap-1 active:scale-95"
              >
                <Send className="w-3.5 h-3.5" />
                Add Note
              </button>
            </form>
          </div>

          {/* Status Change Audit Trail */}
          <div className="aviation-glass-card bg-slate-900/80 border border-slate-800/90 rounded-2xl p-6 shadow-xl backdrop-blur-xl space-y-4">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2 font-mono">
              <Clock className="w-4 h-4 text-sky-400" />
              Status Transition Audit History
            </h2>
            <div className="space-y-3">
              {ticket.status_history && ticket.status_history.length > 0 ? (
                ticket.status_history.map((h, i) => (
                  <div key={h.id || i} className="flex items-start gap-3 text-xs border-l-2 border-sky-500/40 pl-4 py-1">
                    <div className="w-2 h-2 rounded-full bg-sky-400 mt-1 flex-shrink-0 animate-ping" />
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-white">
                          {h.old_status ? `${h.old_status} → ${h.new_status}` : h.new_status}
                        </span>
                        <span className="text-slate-400 font-mono text-[11px]">
                          {new Date(h.created_at).toLocaleString()}
                        </span>
                      </div>
                      {h.reason && <p className="text-slate-400 mt-0.5">{h.reason}</p>}
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-xs text-slate-400">No status transitions recorded yet.</p>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: AI Intelligence & Policy Verification */}
        <div className="lg:col-span-5 space-y-6">
          <div className="aviation-glass-card bg-slate-900/80 border border-slate-800/90 rounded-2xl p-6 shadow-xl backdrop-blur-xl space-y-5 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/5 rounded-full blur-2xl pointer-events-none" />
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-4 relative z-10">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-sky-500/15 text-sky-400 border border-sky-500/30">
                  <Cpu className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-sm font-bold text-white font-display">AI Policy Evaluation</h2>
                  <p className="text-[11px] text-slate-400 font-mono">Model: {c?.model_name || 'AeroAssist-Agentic'}</p>
                </div>
              </div>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-sky-500/10 text-sky-300 border border-sky-500/25">
                Grounding Engine
              </span>
            </div>

            {c ? (
              <div className="space-y-4 relative z-10">
                {/* Confidence Gauge with 70% threshold indicator */}
                <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800/80 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-300 font-medium">Confidence Score</span>
                    <span
                      className={`font-mono font-bold text-base ${
                        isHighConfidence ? 'text-emerald-400' : 'text-amber-400'
                      }`}
                    >
                      {confidenceScore}%
                    </span>
                  </div>

                  {/* Progress Bar */}
                  <div className="w-full bg-slate-800/80 h-2 rounded-full overflow-hidden border border-slate-700/60">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${
                        isHighConfidence ? 'bg-gradient-to-r from-emerald-500 to-teal-400' : 'bg-gradient-to-r from-amber-500 to-orange-400'
                      }`}
                      style={{ width: `${confidenceScore}%` }}
                    />
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1 font-mono">
                    <span>Threshold: 70.0%</span>
                    <span>
                      {isHighConfidence
                        ? 'Passed: Cleared for Resolution'
                        : 'Below 70%: Review Mandated'}
                    </span>
                  </div>
                </div>

                {/* Categorization Badges */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800/80">
                    <span className="text-[11px] text-slate-400 block mb-1">Diagnosed Category</span>
                    <span className="text-xs font-semibold text-white">{c.predicted_category}</span>
                  </div>
                  <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800/80">
                    <span className="text-[11px] text-slate-400 block mb-1">Assigned Priority</span>
                    <span
                      className={`text-xs font-bold ${
                        c.priority === 'P1 Critical' || c.priority === 'Urgent'
                          ? 'text-rose-400'
                          : c.priority === 'P2 High' || c.priority === 'High'
                          ? 'text-amber-400'
                          : 'text-sky-400'
                      }`}
                    >
                      {c.priority}
                    </span>
                  </div>
                </div>

                {/* AI Explanation */}
                <div>
                  <span className="text-xs font-semibold text-slate-300 block mb-1">
                    AI Rationale & Assessment
                  </span>
                  <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/70 p-3 rounded-xl border border-slate-800/80">
                    {c.explanation}
                  </p>
                </div>

                {/* Detected Keywords */}
                {c.detected_keywords && c.detected_keywords.length > 0 && (
                  <div>
                    <span className="text-xs font-semibold text-slate-300 block mb-1.5 font-mono text-[11px]">
                      Extracted Policy Keywords
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {c.detected_keywords.map((kw, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 rounded text-[11px] bg-sky-500/10 text-sky-300 border border-sky-500/20 font-mono"
                        >
                          #{kw}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Recommended Action */}
                <div className="p-3.5 bg-sky-500/10 border border-sky-500/20 rounded-xl text-xs space-y-1">
                  <span className="font-semibold text-sky-300 block font-mono">Recommended Action</span>
                  <p className="text-slate-300 leading-relaxed">{c.recommended_next_action}</p>
                </div>

                {/* Human Review Sign-off if already reviewed */}
                {c.is_reviewed && (
                  <div className="p-3.5 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-xs space-y-1">
                    <span className="font-semibold text-emerald-300 flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Human Review Completed
                    </span>
                    <p className="text-slate-300">{c.review_notes}</p>
                    {c.reviewed_at && (
                      <span className="text-[10px] text-slate-400 block font-mono">
                        Date: {new Date(c.reviewed_at).toLocaleString()}
                      </span>
                    )}
                  </div>
                )}

                {/* Review Trigger Button for Support Agents */}
                {isSupport && (
                  <button
                    onClick={() => setReviewModalOpen(true)}
                    className="w-full py-2.5 bg-slate-800/90 hover:bg-slate-700/90 text-slate-200 border border-slate-700/80 rounded-xl text-xs font-semibold transition-all flex items-center justify-center gap-2 active:scale-95 shadow-sm"
                  >
                    <Shield className="w-3.5 h-3.5 text-amber-400" />
                    Human Review & Policy Override
                  </button>
                )}
              </div>
            ) : (
              <div className="py-8 text-center text-slate-400 text-xs">
                Classification pending. Click "Reclassify" above.
              </div>
            )}
          </div>

          {/* Jira Cloud Integration & Sync Card */}
          <div className="aviation-glass-card rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-blue-400" />
                <h3 className="font-bold text-white text-xs font-display uppercase tracking-wider">
                  Jira Cloud Synchronization
                </h3>
              </div>
              <span className="text-[10px] font-mono text-cyan-400 font-bold bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                Atlassian Sync
              </span>
            </div>

            {ticket.jira_records && ticket.jira_records.length > 0 ? (
              <div className="space-y-3">
                {ticket.jira_records.map((jr) => (
                  <div key={jr.id} className="p-4 bg-slate-950/80 rounded-xl border border-sky-500/30 space-y-2.5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-cyan-400 text-sm">{jr.jira_key}</span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                          {jr.status}
                        </span>
                      </div>
                      <a
                        href={jr.jira_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-cyan-400 hover:text-cyan-300 text-[11px] font-mono flex items-center gap-1 transition-colors"
                      >
                        Inspect in Jira <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>

                    <p className="text-xs text-white font-medium line-clamp-2">{jr.summary}</p>

                    <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono pt-1 border-t border-slate-800">
                      <span>Priority: <strong className="text-slate-200">{jr.priority}</strong></span>
                      <span>Type: <strong className="text-slate-200">{jr.issue_type}</strong></span>
                    </div>

                    {isSupport && (
                      <button
                        onClick={handleRefreshJira}
                        disabled={refreshingJira}
                        className="w-full mt-1 py-1.5 bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white rounded-lg text-xs font-semibold border border-slate-700/80 transition-all flex items-center justify-center gap-1.5 cursor-pointer"
                      >
                        <RefreshCw className={`w-3.5 h-3.5 ${refreshingJira ? 'animate-spin text-sky-400' : ''}`} />
                        {refreshingJira ? 'Refreshing Jira Status...' : 'Refresh Jira Status'}
                      </button>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-3">
                <p className="text-xs text-slate-300 leading-relaxed">
                  Dispatch this passenger incident ticket to Jira Cloud to track engineering tasks, avionics troubleshooting, or baggage team workflows.
                </p>

                {isSupport ? (
                  <button
                    onClick={handleSyncToJira}
                    disabled={syncingJira}
                    className="w-full py-2.5 bg-gradient-to-r from-sky-600 to-cyan-500 hover:from-sky-500 hover:to-cyan-400 text-white rounded-xl text-xs font-semibold shadow-lg shadow-sky-600/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50 cursor-pointer"
                  >
                    {syncingJira ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Synchronizing with Jira...
                      </>
                    ) : (
                      <>
                        <Layers className="w-3.5 h-3.5" /> Dispatch & Link to Jira Cloud
                      </>
                    )}
                  </button>
                ) : (
                  <span className="text-[11px] text-slate-500 italic block">
                    Jira dispatch available for support engineers.
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Human Review Modal */}
      {reviewModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-white text-base flex items-center gap-2">
                <Shield className="w-4 h-4 text-amber-400" />
                Human Agent Sign-Off (Ticket #{ticket.id})
              </h3>
              <button onClick={() => setReviewModalOpen(false)} className="text-slate-400 hover:text-white">
                &times;
              </button>
            </div>

            <form onSubmit={handleReviewSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-2">
                  Review Decision
                </label>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={() => setReviewAction('APPROVE')}
                    className={`py-2 px-3 rounded-lg text-xs font-semibold border flex items-center justify-center gap-1.5 ${
                      reviewAction === 'APPROVE'
                        ? 'bg-emerald-600 text-white border-emerald-500 shadow'
                        : 'bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700'
                    }`}
                  >
                    <Check className="w-3.5 h-3.5" /> Approve
                  </button>
                  <button
                    type="button"
                    onClick={() => setReviewAction('OVERRIDE')}
                    className={`py-2 px-3 rounded-lg text-xs font-semibold border flex items-center justify-center gap-1.5 ${
                      reviewAction === 'OVERRIDE'
                        ? 'bg-sky-600 text-white border-sky-500 shadow'
                        : 'bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700'
                    }`}
                  >
                    <Sliders className="w-3.5 h-3.5" /> Override
                  </button>
                  <button
                    type="button"
                    onClick={() => setReviewAction('REJECT')}
                    className={`py-2 px-3 rounded-lg text-xs font-semibold border flex items-center justify-center gap-1.5 ${
                      reviewAction === 'REJECT'
                        ? 'bg-rose-600 text-white border-rose-500 shadow'
                        : 'bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700'
                    }`}
                  >
                    <X className="w-3.5 h-3.5" /> Reject
                  </button>
                </div>
              </div>

              {reviewAction === 'OVERRIDE' && (
                <div className="grid grid-cols-2 gap-4 bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                  <div>
                    <label className="block text-xs text-slate-400 mb-1">Override Category</label>
                    <input
                      type="text"
                      value={overrideCategory}
                      onChange={(e) => setOverrideCategory(e.target.value)}
                      className="w-full bg-slate-800 border border-slate-700 rounded-md px-2.5 py-1.5 text-xs text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-slate-400 mb-1">Override Priority</label>
                    <select
                      value={overridePriority}
                      onChange={(e) => setOverridePriority(e.target.value)}
                      className="w-full bg-slate-800 border border-slate-700 rounded-md px-2.5 py-1.5 text-xs text-white"
                    >
                      <option value="Urgent">Urgent</option>
                      <option value="High">High</option>
                      <option value="Medium">Medium</option>
                      <option value="Low">Low</option>
                    </select>
                  </div>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                  Support Agent Notes & Audit Justification
                </label>
                <textarea
                  required
                  rows={3}
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder="State technical justification, confirmed policy, or corrective guidance..."
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 text-xs text-white focus:outline-none focus:border-sky-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setReviewModalOpen(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={reviewSubmitting}
                  className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg shadow disabled:opacity-50"
                >
                  {reviewSubmitting ? 'Recording...' : 'Commit Review Decision'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
