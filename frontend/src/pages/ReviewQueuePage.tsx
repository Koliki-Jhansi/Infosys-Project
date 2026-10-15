import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { reviewsApi } from '../services/api';
import { Ticket } from '../types';
import { useAuth } from '../features/auth/AuthContext';
import {
  UserCheck,
  AlertTriangle,
  RefreshCw,
  Clock,
  Shield,
  Check,
  X,
  Sliders,
  ArrowRight,
  Plane,
  AlertCircle,
  ExternalLink,
  Sparkles,
  CheckCircle2,
  ShieldAlert,
  User
} from 'lucide-react';

export const ReviewQueuePage: React.FC = () => {
  const { user, isSupport, loginAsDemo } = useAuth();
  const [queue, setQueue] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState<string | null>(null);
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [reviewAction, setReviewAction] = useState<'APPROVE' | 'REJECT' | 'OVERRIDE'>('APPROVE');
  const [notes, setNotes] = useState('');
  const [overrideCategory, setOverrideCategory] = useState('');
  const [overridePriority, setOverridePriority] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState('');

  const loadQueue = async () => {
    try {
      setLoading(true);
      setAuthError(null);
      const data = await reviewsApi.getQueue();
      setQueue(data);
    } catch (err: any) {
      console.error('Failed to load review queue', err);
      if (err.response?.status === 403) {
        setAuthError(err.response?.data?.detail || "Operation not permitted. Requires one of roles: ['ADMIN', 'SUPPORT_ENGINEER', 'SUPPORT_AGENT']");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
  }, [user?.role]);


  const openReviewModal = (t: Ticket) => {
    setSelectedTicket(t);
    setReviewAction('APPROVE');
    setNotes('');
    setOverrideCategory(t.classification?.predicted_category || t.category);
    setOverridePriority(t.classification?.priority || 'P3 Medium');
  };

  const handleSubmitReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTicket) return;
    try {
      setSubmitting(true);
      await reviewsApi.reviewTicket(selectedTicket.id, {
        action: reviewAction,
        notes: notes || 'Station supervisor approved during review queue triage',
        override_category: reviewAction === 'OVERRIDE' ? overrideCategory : undefined,
        override_priority: reviewAction === 'OVERRIDE' ? overridePriority : undefined,
      });
      setSelectedTicket(null);
      setMessage(`Ticket #${selectedTicket.id} supervisory review recorded successfully.`);
      await loadQueue();
    } catch (err) {
      console.error('Failed to submit review', err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-fade-in-up">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-sky-950/60 pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500/20 to-orange-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 shadow-lg shadow-amber-950/50">
              <UserCheck className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold tracking-tight text-white font-display">
                  Human-in-the-Loop Review Queue
                </h1>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-amber-500/10 text-amber-300 border border-amber-500/20">
                  MILESTONE 4
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Incidents flagged with confidence &lt; 70%, safety policy overrides, or financial escalations awaiting supervisor review.
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={loadQueue}
          className="px-4 py-2.5 bg-slate-900/90 hover:bg-slate-800 border border-slate-700/80 text-slate-200 rounded-xl text-xs font-semibold transition-all flex items-center gap-2 self-start hover:border-slate-600 shadow-sm cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-sky-400' : ''}`} />
          Refresh Queue
        </button>
      </div>

      {message && (
        <div className="p-4 rounded-2xl bg-emerald-950/40 border border-emerald-500/30 text-emerald-200 text-xs flex items-center justify-between shadow-lg shadow-emerald-950/20">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span className="font-medium">{message}</span>
          </div>
          <button
            onClick={() => setMessage('')}
            className="text-slate-400 hover:text-white px-2 py-0.5 rounded hover:bg-white/10"
          >
            &times;
          </button>
        </div>
      )}

      {/* Access Denied Warning Banner for Non-Support Users */}
      {(authError || !isSupport) && (
        <div className="p-6 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-200 shadow-xl space-y-3">
          <div className="flex items-start gap-3">
            <ShieldAlert className="w-6 h-6 text-amber-400 flex-shrink-0 mt-0.5" />
            <div className="space-y-1.5 flex-1">
              <h2 className="text-sm font-bold text-white font-['Outfit']">
                Restricted Access: Milestone 4 Human Review Queue
              </h2>
              <p className="text-xs text-amber-300/90 leading-relaxed font-['Inter']">
                The supervisor review queue is reserved for Airline Operations Support Agents, Systems Engineers, and Administrators. Ordinary passenger accounts cannot triage safety and financial policy overrides.
              </p>
              {authError && (
                <p className="text-[11px] font-mono bg-slate-900/90 text-amber-400 p-2.5 rounded-lg border border-amber-500/20">
                  {authError}
                </p>
              )}
              <div className="pt-2 flex flex-wrap items-center gap-2">
                <span className="text-xs text-slate-300">
                  Currently signed in as <strong className="text-white">{user?.full_name}</strong> ({user?.role}). Switch persona to test:
                </span>
                <button
                  onClick={() => loginAsDemo('SUPPORT_AGENT')}
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-sky-600 to-blue-600 hover:from-sky-500 hover:to-blue-500 text-white shadow-md shadow-sky-600/30 transition-all cursor-pointer"
                >
                  Switch to Support Agent
                </button>
                <button
                  onClick={() => loginAsDemo('ADMIN')}
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 transition-all cursor-pointer"
                >
                  Switch to Admin
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Queue Table */}
      <div className="aviation-glass-card rounded-2xl shadow-xl overflow-hidden">

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-[10px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-800 font-mono">
              <tr>
                <th className="py-3.5 px-6">Ticket & Flight Service</th>
                <th className="py-3.5 px-6">Priority</th>
                <th className="py-3.5 px-6">AI Confidence</th>
                <th className="py-3.5 px-6">Review Reason</th>
                <th className="py-3.5 px-6">Reporter</th>
                <th className="py-3.5 px-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {loading && queue.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400">
                    <RefreshCw className="w-6 h-6 text-sky-500 animate-spin mx-auto mb-2" />
                    Checking review queue...
                  </td>
                </tr>
              ) : queue.length > 0 ? (
                queue.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-4 px-6">
                      <Link to={`/tickets/${t.id}`} className="font-bold text-white hover:text-sky-400 font-display transition-colors">
                        #{t.id} - {t.title}
                      </Link>
                      <div className="text-[11px] text-slate-400 flex items-center gap-2 mt-0.5">
                        <span className="font-mono text-cyan-400">{t.affected_service || t.category}</span>
                        <span>•</span>
                        <Clock className="w-3 h-3 text-slate-500" />
                        <span>{new Date(t.created_at).toLocaleString()}</span>
                      </div>
                    </td>
                    <td className="py-4 px-6">
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded border font-mono ${
                          t.classification?.priority === 'P1 Critical'
                            ? 'text-rose-300 bg-rose-500/10 border-rose-500/30'
                            : t.classification?.priority === 'P2 High'
                            ? 'text-orange-300 bg-orange-500/10 border-orange-500/30'
                            : 'text-amber-300 bg-amber-500/10 border-amber-500/30'
                        }`}
                      >
                        {t.classification?.priority || 'Pending'}
                      </span>
                    </td>
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-2.5">
                        <div className="w-16 bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800 shadow-inner">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${
                              (t.classification?.confidence_score || 0) >= 70 ? 'bg-emerald-500' : 'bg-amber-500'
                            }`}
                            style={{ width: `${t.classification?.confidence_score || 0}%` }}
                          />
                        </div>
                        <span className="text-xs font-mono font-bold text-amber-400">
                          {t.classification?.confidence_score || 0}%
                        </span>
                      </div>
                    </td>
                    <td className="py-4 px-6">
                      <p className="text-xs text-amber-300/90 leading-tight max-w-xs flex items-center gap-1.5">
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                        <span>{t.classification?.review_reason || 'Requires manual sign-off before automation.'}</span>
                      </p>
                    </td>
                    <td className="py-4 px-6 text-xs text-slate-400">
                      {t.reporter?.full_name || 'Passenger'}
                    </td>
                    <td className="py-4 px-6 text-right space-x-2 whitespace-nowrap">
                      <button
                        onClick={() => openReviewModal(t)}
                        className="px-3.5 py-1.5 bg-gradient-to-r from-amber-600 to-orange-500 hover:from-amber-500 hover:to-orange-400 text-white rounded-xl text-xs font-semibold shadow-md shadow-amber-600/20 transition-all cursor-pointer"
                      >
                        Review
                      </button>
                      <Link
                        to={`/tickets/${t.id}`}
                        className="px-2.5 py-1.5 bg-slate-900/90 hover:bg-slate-800 text-slate-300 rounded-xl text-xs font-medium border border-slate-700/80 inline-block transition-colors"
                      >
                        Inspect
                      </Link>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="py-14 text-center text-slate-400 text-xs">
                    <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto mb-2 opacity-80" />
                    <p className="font-semibold text-slate-200">Review queue is clear!</p>
                    <p className="text-slate-400 mt-1">All passenger tickets satisfy confidence thresholds (&ge; 70%) or have been approved.</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Review Modal */}
      {selectedTicket && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="aviation-glass-card rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5 border border-sky-500/30 animate-fade-in-up">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-white text-base flex items-center gap-2 font-display">
                <Shield className="w-4 h-4 text-amber-400" />
                Review Ticket #{selectedTicket.id}
              </h3>
              <button
                onClick={() => setSelectedTicket(null)}
                className="text-slate-400 hover:text-white text-lg px-2 py-1 rounded transition-colors cursor-pointer"
              >
                &times;
              </button>
            </div>

            <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 text-xs space-y-2">
              <div className="font-bold text-white font-display text-sm">{selectedTicket.title}</div>
              <p className="text-slate-300 line-clamp-2 leading-relaxed">{selectedTicket.description}</p>
              <div className="flex items-center gap-3 pt-1 text-[11px] text-slate-400 font-mono">
                <span>Score: <strong className="text-amber-400">{selectedTicket.classification?.confidence_score}%</strong></span>
                <span>•</span>
                <span>Category: <strong className="text-white font-sans">{selectedTicket.classification?.predicted_category}</strong></span>
                <span>•</span>
                <span>Priority: <strong className="text-white">{selectedTicket.classification?.priority}</strong></span>
              </div>
            </div>

            <form onSubmit={handleSubmitReview} className="space-y-4 text-xs">
              <div>
                <label className="block text-[10px] font-bold text-slate-300 uppercase tracking-wider mb-2 font-mono">
                  Supervisory Decision Action
                </label>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={() => setReviewAction('APPROVE')}
                    className={`py-2 px-3 rounded-xl text-xs font-semibold border flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                      reviewAction === 'APPROVE'
                        ? 'bg-emerald-600 text-white border-emerald-500 shadow-lg shadow-emerald-600/20'
                        : 'bg-slate-900/90 text-slate-300 border-slate-700/80 hover:bg-slate-800'
                    }`}
                  >
                    <Check className="w-3.5 h-3.5" /> Approve
                  </button>
                  <button
                    type="button"
                    onClick={() => setReviewAction('OVERRIDE')}
                    className={`py-2 px-3 rounded-xl text-xs font-semibold border flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                      reviewAction === 'OVERRIDE'
                        ? 'bg-sky-600 text-white border-sky-500 shadow-lg shadow-sky-600/20'
                        : 'bg-slate-900/90 text-slate-300 border-slate-700/80 hover:bg-slate-800'
                    }`}
                  >
                    <Sliders className="w-3.5 h-3.5" /> Override
                  </button>
                  <button
                    type="button"
                    onClick={() => setReviewAction('REJECT')}
                    className={`py-2 px-3 rounded-xl text-xs font-semibold border flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                      reviewAction === 'REJECT'
                        ? 'bg-rose-600 text-white border-rose-500 shadow-lg shadow-rose-600/20'
                        : 'bg-slate-900/90 text-slate-300 border-slate-700/80 hover:bg-slate-800'
                    }`}
                  >
                    <X className="w-3.5 h-3.5" /> Reject
                  </button>
                </div>
              </div>

              {reviewAction === 'OVERRIDE' && (
                <div className="grid grid-cols-2 gap-3 bg-slate-950/80 p-3.5 rounded-xl border border-slate-800">
                  <div>
                    <label className="block text-[11px] text-slate-400 mb-1 font-mono">New Category</label>
                    <input
                      type="text"
                      value={overrideCategory}
                      onChange={(e) => setOverrideCategory(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-sky-500"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] text-slate-400 mb-1 font-mono">New Priority</label>
                    <select
                      value={overridePriority}
                      onChange={(e) => setOverridePriority(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-sky-500"
                    >
                      <option value="P1 Critical">P1 Critical</option>
                      <option value="P2 High">P2 High</option>
                      <option value="P3 Medium">P3 Medium</option>
                      <option value="P4 Low">P4 Low</option>
                    </select>
                  </div>
                </div>
              )}

              <div>
                <label className="block text-[10px] font-bold text-slate-300 uppercase tracking-wider mb-1 font-mono">
                  Station Supervisor Justification & Notes
                </label>
                <textarea
                  required
                  rows={3}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="State reason for approving, rejecting, or overriding this ticket..."
                  className="w-full bg-slate-900 border border-slate-700/80 rounded-xl p-3 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-sky-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setSelectedTicket(null)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-xl cursor-pointer transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-gradient-to-r from-sky-600 to-cyan-500 hover:from-sky-500 hover:to-cyan-400 text-white text-xs font-semibold rounded-xl shadow-lg shadow-sky-600/20 disabled:opacity-50 cursor-pointer transition-all"
                >
                  {submitting ? 'Submitting...' : 'Commit Decision'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
