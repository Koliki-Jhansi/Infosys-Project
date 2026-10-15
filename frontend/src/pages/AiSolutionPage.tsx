import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import {
  Sparkles,
  Plane,
  Bot,
  BookOpen,
  CheckCircle2,
  AlertTriangle,
  RotateCw,
  Send,
  ShieldCheck,
  User,
  ArrowRight,
  ExternalLink,
  Edit3,
  ThumbsUp,
  ThumbsDown,
  Clock,
  Layers,
  FileCheck,
  PlusCircle,
  HelpCircle,
  Star,
  Search,
  Check,
  ChevronDown,
  ChevronUp,
  AlertCircle
} from 'lucide-react';
import { ticketsApi, aiSolutionApi, analyticsApi } from '../services/api';
import { Ticket, AiSolutionResult } from '../types';

interface BenchmarkCase {
  id: string;
  name: string;
  category: string;
  confidenceType: 'HIGH' | 'LOW' | 'DISPUTE' | 'CONTRADICTORY' | 'INCOMPLETE' | 'UNSUPPORTED';
  badge: string;
  badgeClass: string;
  title: string;
  description: string;
  passenger_name: string;
  passenger_email: string;
  booking_reference: string;
  flight_number: string;
  travel_date: string;
  expected_outcome: 'RESOLVE' | 'ESCALATE';
  expected_confidence: string;
  benchmark_notes: string;
}

const BENCHMARK_TEST_SUITE: BenchmarkCase[] = [
  {
    id: 'case-refund-24h',
    name: '24-Hour Refund (Full Policy Supported)',
    category: 'Cancellation and Refund',
    confidenceType: 'HIGH',
    badge: 'High Confidence (~92%)',
    badgeClass: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    title: 'Request 100% refund under 24-hour cancellation rule',
    description: 'I purchased ticket AA-REF24 yesterday afternoon at 3:15 PM and need to cancel it today at 11:00 AM, which is within the 24-hour window. My departure is next month. Please issue a full refund to my original payment card in accordance with airline policy without any cancellation fees.',
    passenger_name: 'David Miller',
    passenger_email: 'david.miller@example.com',
    booking_reference: 'AA-REF24',
    flight_number: 'AA-304',
    travel_date: '2026-11-20',
    expected_outcome: 'RESOLVE',
    expected_confidence: '90-95%',
    benchmark_notes: 'Full policy match with verified 24-Hour Cancellation Runbook. Should achieve high confidence (>70% threshold) and pass validation.'
  },
  {
    id: 'case-baggage-unsupported',
    name: 'Missing Baggage with No Runbook Match',
    category: 'Baggage',
    confidenceType: 'LOW',
    badge: 'Low Confidence (<40%)',
    badgeClass: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    title: 'Antique cello lost with custom unbranded titanium case and no barcode scan',
    description: 'My vintage acoustic cello in an unbranded titanium composite flight case with no barcode luggage tag was supposed to transfer at JFK Terminal 8. Ground handlers have no record of luggage transfer and the carousel was completely empty. It contains an irreplaceable instrument valued over $45,000.',
    passenger_name: 'Elena Rostova',
    passenger_email: 'elena.r@example.com',
    booking_reference: 'AA-BAG99',
    flight_number: 'AA-712',
    travel_date: '2026-10-14',
    expected_outcome: 'ESCALATE',
    expected_confidence: '25-45%',
    benchmark_notes: 'High-value non-standard cargo with no standard policy chunk. Confidence falls below 70% policy threshold; mandatory supervisor escalation.'
  },
  {
    id: 'case-connecting-dispute',
    name: 'Complex Connecting Flight Dispute',
    category: 'Flight Delay',
    confidenceType: 'DISPUTE',
    badge: 'Dispute / Layover (~65%)',
    badgeClass: 'bg-sky-500/10 text-sky-400 border-sky-500/30',
    title: '35-minute international connection missed due to tarmac hold',
    description: 'Flight AA-488 landed on time but sat on the taxiway for 45 minutes awaiting an open gate at ORD. As a result, 6 passengers missed connecting flight AA-902 to London. Station agent refused meal and hotel vouchers, claiming air traffic control was at fault. We request hotel vouchers and rebooking on partner airlines.',
    passenger_name: 'Marcus Chen',
    passenger_email: 'mchen@connect.org',
    booking_reference: 'AA-MIS42',
    flight_number: 'AA-488',
    travel_date: '2026-10-15',
    expected_outcome: 'ESCALATE',
    expected_confidence: '60-68%',
    benchmark_notes: 'Contested carrier taxiway delay vs ATC weather fault. Requires human station manager override.'
  },
  {
    id: 'case-contradictory',
    name: 'Contradictory Passenger Claim',
    category: 'Booking and Reservation',
    confidenceType: 'CONTRADICTORY',
    badge: 'Contradictory / Caution',
    badgeClass: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
    title: 'Passenger voluntarily cancelled online but demands airline cancellation compensation',
    description: 'I voluntarily clicked cancel online on Tuesday because my meeting was postponed. However, your app says the flight was delayed by maintenance on Thursday morning. Since the flight had maintenance issues, I demand cash compensation plus statutory penalties even though I already accepted a flight credit on Tuesday.',
    passenger_name: 'Sarah Jenkins',
    passenger_email: 'sarah.j@travel.net',
    booking_reference: 'AA-CON91',
    flight_number: 'AA-104',
    travel_date: '2026-10-16',
    expected_outcome: 'ESCALATE',
    expected_confidence: '45-60%',
    benchmark_notes: 'Contradictory timeline in passenger request. Validation agent flags inconsistency for human review.'
  },
  {
    id: 'case-incomplete',
    name: 'Incomplete Ticket (Missing PNR & Flight)',
    category: 'Other',
    confidenceType: 'INCOMPLETE',
    badge: 'Incomplete Data (<35%)',
    badgeClass: 'bg-slate-500/10 text-slate-400 border-slate-500/30',
    title: 'Help with my flight ASAP',
    description: 'My flight is messed up and I need to change my seat and travel date immediately. Please fix it right now and send confirmation to my phone.',
    passenger_name: 'Anonymous Traveler',
    passenger_email: 'guest@unknown.com',
    booking_reference: '',
    flight_number: '',
    travel_date: '',
    expected_outcome: 'ESCALATE',
    expected_confidence: '20-35%',
    benchmark_notes: 'Missing required booking reference (PNR), flight number, and travel date. Insufficient evidence for resolution.'
  },
  {
    id: 'case-unsupported-comp',
    name: 'Unsupported Guaranteed Compensation',
    category: 'Payment',
    confidenceType: 'UNSUPPORTED',
    badge: 'Unsupported ($10k)',
    badgeClass: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
    title: 'Demand $10,000 cash wire transfer for 2-hour weather delay',
    description: 'My domestic flight AA-220 was delayed by 2 hours due to heavy thunderstorms over Denver. I demand an immediate $10,000 wire transfer into my bank account within 1 hour as personal damages for a missed dinner engagement.',
    passenger_name: 'Arthur Pendelton',
    passenger_email: 'arthur.p@legalcorp.com',
    booking_reference: 'AA-CMP88',
    flight_number: 'AA-220',
    travel_date: '2026-10-12',
    expected_outcome: 'ESCALATE',
    expected_confidence: '35-50%',
    benchmark_notes: 'Weather delays are non-compensable under airline contract of carriage. Request exceeds policy limits.'
  }
];

export const AiSolutionPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const preselectedTicketId = searchParams.get('ticketId');

  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [selectedTicketId, setSelectedTicketId] = useState<number | null>(
    preselectedTicketId ? parseInt(preselectedTicketId, 10) : null
  );
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);

  const [loadingTickets, setLoadingTickets] = useState(true);
  const [resolving, setResolving] = useState(false);
  const [aiResult, setAiResult] = useState<AiSolutionResult | null>(null);
  const [editedResponse, setEditedResponse] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [actionMessage, setActionMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Active benchmark scenario (if triggered from preset)
  const [activeBenchmark, setActiveBenchmark] = useState<BenchmarkCase | null>(null);

  // Custom Ticket Form State
  const [showCustomForm, setShowCustomForm] = useState(false);
  const [customForm, setCustomForm] = useState({
    title: '',
    passenger_name: '',
    passenger_email: '',
    booking_reference: '',
    flight_number: '',
    category: 'Cancellation and Refund',
    description: ''
  });
  const [creatingCustom, setCreatingCustom] = useState(false);

  // Ground-Truth Feedback State
  const [feedbackLabel, setFeedbackLabel] = useState<'CORRECT' | 'PARTIALLY_CORRECT' | 'INCORRECT' | 'UNABLE_TO_ASSESS'>('CORRECT');
  const [feedbackRating, setFeedbackRating] = useState<number>(5);
  const [feedbackNotes, setFeedbackNotes] = useState('');
  const [submittingFeedback, setSubmittingFeedback] = useState(false);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);

  // Load ticket directory for selector
  useEffect(() => {
    const fetchTickets = async () => {
      try {
        const res = await ticketsApi.list({ size: 50 });
        setTickets(res.items);
        if (res.items.length > 0 && !selectedTicketId) {
          setSelectedTicketId(res.items[0].id);
        }
      } catch (err) {
        console.error('Failed to load tickets:', err);
      } finally {
        setLoadingTickets(false);
      }
    };
    fetchTickets();
  }, []);

  // When selected ticket changes, load its details and trigger AI solution
  useEffect(() => {
    if (!selectedTicketId) return;

    const loadTicketAndSolution = async () => {
      try {
        const ticketData = await ticketsApi.getById(selectedTicketId);
        setSelectedTicket(ticketData);
        setActionMessage(null);
        setIsEditing(false);
        setFeedbackSubmitted(false);

        // Fetch AI resolution
        setResolving(true);
        const result = await aiSolutionApi.resolve(selectedTicketId);
        setAiResult(result);
        setEditedResponse(result.generated_response);
      } catch (err: any) {
        console.error('Failed to generate AI solution:', err);
        setActionMessage({
          type: 'error',
          text: err.response?.data?.detail || 'Failed to process AI solution for this ticket.'
        });
      } finally {
        setResolving(false);
      }
    };

    loadTicketAndSolution();
  }, [selectedTicketId]);

  const handleRegenerate = async () => {
    if (!selectedTicketId) return;
    setResolving(true);
    setActionMessage(null);
    setFeedbackSubmitted(false);
    try {
      const result = await aiSolutionApi.resolve(selectedTicketId);
      setAiResult(result);
      setEditedResponse(result.generated_response);
      setIsEditing(false);
      setActionMessage({ type: 'success', text: 'AI solution re-synthesized and validated against knowledge base.' });
    } catch (err: any) {
      setActionMessage({ type: 'error', text: 'Regeneration failed.' });
    } finally {
      setResolving(false);
    }
  };

  const handleApproveAndResolve = async () => {
    if (!selectedTicketId) return;
    try {
      await ticketsApi.resolve(selectedTicketId, { response: isEditing ? editedResponse : aiResult?.generated_response });
      setActionMessage({ type: 'success', text: 'Ticket marked AI RESOLVED. Response saved to passenger record.' });
      const updated = await ticketsApi.getById(selectedTicketId);
      setSelectedTicket(updated);
    } catch (err: any) {
      setActionMessage({ type: 'error', text: 'Failed to resolve ticket.' });
    }
  };

  const handleEscalate = async () => {
    if (!selectedTicketId) return;
    try {
      await ticketsApi.escalate(selectedTicketId, { reason: 'Escalated from AI Solution console by support specialist' });
      setActionMessage({ type: 'success', text: 'Ticket status updated to ESCALATED. Assigned to human agent queue.' });
      const updated = await ticketsApi.getById(selectedTicketId);
      setSelectedTicket(updated);
    } catch (err: any) {
      setActionMessage({ type: 'error', text: 'Failed to escalate ticket.' });
    }
  };

  // Launch Benchmark Test Scenario
  const handleRunBenchmarkCase = async (bCase: BenchmarkCase) => {
    try {
      setResolving(true);
      setActiveBenchmark(bCase);
      setActionMessage(null);
      setFeedbackSubmitted(false);

      // Create ticket on the fly for benchmark
      const newTicket = await ticketsApi.create({
        title: bCase.title,
        passenger_name: bCase.passenger_name,
        passenger_email: bCase.passenger_email,
        booking_reference: bCase.booking_reference,
        flight_number: bCase.flight_number,
        travel_date: bCase.travel_date,
        category: bCase.category,
        urgency: 'Medium',
        description: bCase.description
      });

      // Update tickets list and select
      setTickets((prev) => [newTicket, ...prev]);
      setSelectedTicketId(newTicket.id);
      setSelectedTicket(newTicket);

      // Run AI resolution
      const result = await aiSolutionApi.resolve(newTicket.id);
      setAiResult(result);
      setEditedResponse(result.generated_response);
      setIsEditing(false);

      setActionMessage({
        type: 'success',
        text: `Benchmark '${bCase.name}' created as #${newTicket.ticket_number} and evaluated successfully.`
      });
    } catch (err: any) {
      console.error('Benchmark execution error:', err);
      setActionMessage({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to execute benchmark test case.'
      });
    } finally {
      setResolving(false);
    }
  };

  // Handle Custom Ticket Creation
  const handleCreateCustomTicket = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customForm.title.trim() || !customForm.description.trim()) return;

    try {
      setCreatingCustom(true);
      const newTicket = await ticketsApi.create({
        title: customForm.title,
        passenger_name: customForm.passenger_name || 'Passenger Tester',
        passenger_email: customForm.passenger_email || 'tester@airline.com',
        booking_reference: customForm.booking_reference,
        flight_number: customForm.flight_number,
        category: customForm.category,
        description: customForm.description
      });

      setTickets((prev) => [newTicket, ...prev]);
      setSelectedTicketId(newTicket.id);
      setSelectedTicket(newTicket);
      setShowCustomForm(false);
      setCustomForm({
        title: '',
        passenger_name: '',
        passenger_email: '',
        booking_reference: '',
        flight_number: '',
        category: 'Cancellation and Refund',
        description: ''
      });

      setActionMessage({
        type: 'success',
        text: `Custom test ticket #${newTicket.ticket_number} created and queued for AI evaluation.`
      });
    } catch (err: any) {
      setActionMessage({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to create test ticket.'
      });
    } finally {
      setCreatingCustom(false);
    }
  };

  // Submit Ground-Truth Labeling Feedback
  const handleSubmitGroundTruthFeedback = async () => {
    if (!aiResult?.evaluation_id || !selectedTicketId) return;

    try {
      setSubmittingFeedback(true);
      await analyticsApi.submitFeedback({
        evaluation_id: aiResult.evaluation_id,
        ticket_id: selectedTicketId,
        accuracy_label: feedbackLabel,
        source_grounding_rating: feedbackRating,
        notes: feedbackNotes.trim() || undefined
      });
      setFeedbackSubmitted(true);
      setActionMessage({
        type: 'success',
        text: `Ground-truth label '${feedbackLabel}' successfully recorded in evaluation dataset.`
      });
    } catch (err: any) {
      console.error('Failed to submit ground truth feedback:', err);
      setActionMessage({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to record feedback.'
      });
    } finally {
      setSubmittingFeedback(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12 animate-fade-in-up">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-2xl bg-sky-500/15 border border-sky-500/30 flex items-center justify-center text-sky-400 shadow-md shadow-sky-500/10">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight font-display">
                AI Solution <span className="bg-gradient-to-r from-sky-400 via-cyan-300 to-blue-500 bg-clip-text text-transparent">& Validation Console</span>
              </h1>
            </div>
          </div>
          <p className="text-sm text-slate-300 mt-1">
            Synthesize grounded airline solutions, test high vs low confidence cases, and record human ground-truth evaluations.
          </p>
        </div>

        {/* Global Controls */}
        <div className="flex flex-wrap items-center gap-3">
          <Link
            to="/analytics"
            className="px-3.5 py-2.5 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 text-slate-200 text-xs font-semibold flex items-center gap-2 border border-slate-700/80 transition-all active:scale-95 shadow-sm"
          >
            <Clock className="w-3.5 h-3.5 text-sky-400" /> View AI Analytics
          </Link>
          <button
            onClick={() => setShowCustomForm(!showCustomForm)}
            className="btn-aviation px-4 py-2.5 rounded-xl bg-gradient-to-r from-sky-600 via-sky-500 to-blue-600 hover:from-sky-500 hover:to-blue-500 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-sky-500/25 transition-all active:scale-95"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            {showCustomForm ? 'Close Custom Form' : 'New Test Ticket'}
          </button>
        </div>
      </div>

      {actionMessage && (
        <div
          className={`p-4 rounded-xl border text-sm flex items-center justify-between backdrop-blur-md ${
            actionMessage.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
          }`}
        >
          <span>{actionMessage.text}</span>
          <button onClick={() => setActionMessage(null)} className="text-xs opacity-75 hover:opacity-100 font-bold">
            &times;
          </button>
        </div>
      )}

      {/* Expandable Custom Test Ticket Form */}
      {showCustomForm && (
        <form
          onSubmit={handleCreateCustomTicket}
          className="aviation-glass-card p-6 rounded-2xl bg-slate-900/85 border border-sky-500/30 shadow-2xl space-y-4 backdrop-blur-xl animate-fade-in-up"
        >
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-sky-400 flex items-center gap-2 font-mono">
              <PlusCircle className="w-4 h-4 text-sky-400" /> Create Custom AI Test Ticket
            </span>
            <span className="text-xs text-slate-400 font-mono">Evaluate custom queries (ambiguous, unsupported, contradictory)</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
            <div>
              <label className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider block mb-1">
                Subject / Title *
              </label>
              <input
                type="text"
                required
                value={customForm.title}
                onChange={(e) => setCustomForm({ ...customForm, title: e.target.value })}
                placeholder="e.g. Flight delay compensation claim"
                className="w-full bg-slate-800/80 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-500/30 transition-all"
              />
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider block mb-1">
                Category
              </label>
              <select
                value={customForm.category}
                onChange={(e) => setCustomForm({ ...customForm, category: e.target.value })}
                className="w-full bg-slate-800/80 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-500/30 transition-all cursor-pointer"
              >
                <option value="Cancellation and Refund" className="bg-slate-900">Cancellation and Refund</option>
                <option value="Baggage" className="bg-slate-900">Baggage Claim</option>
                <option value="Flight Delay" className="bg-slate-900">Flight Delay</option>
                <option value="Flight Cancellation" className="bg-slate-900">Flight Cancellation</option>
                <option value="Booking and Reservation" className="bg-slate-900">Booking and Reservation</option>
                <option value="Special Assistance" className="bg-slate-900">Special Assistance</option>
                <option value="Payment" className="bg-slate-900">Payment</option>
                <option value="Other" className="bg-slate-900">Other</option>
              </select>
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider block mb-1">
                Passenger Name
              </label>
              <input
                type="text"
                value={customForm.passenger_name}
                onChange={(e) => setCustomForm({ ...customForm, passenger_name: e.target.value })}
                placeholder="e.g. John Doe"
                className="w-full bg-slate-800/80 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-500/30 transition-all"
              />
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider block mb-1">
                Booking Ref (PNR)
              </label>
              <input
                type="text"
                value={customForm.booking_reference}
                onChange={(e) => setCustomForm({ ...customForm, booking_reference: e.target.value })}
                placeholder="e.g. AA-XYZ99"
                className="w-full bg-slate-800/80 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-white font-mono placeholder-slate-400 focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-500/30 transition-all uppercase"
              />
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider block mb-1">
                Flight Number
              </label>
              <input
                type="text"
                value={customForm.flight_number}
                onChange={(e) => setCustomForm({ ...customForm, flight_number: e.target.value })}
                placeholder="e.g. AA-104"
                className="w-full bg-slate-800/80 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-white font-mono placeholder-slate-400 focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-500/30 transition-all uppercase"
              />
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider block mb-1">
                Passenger Email
              </label>
              <input
                type="email"
                value={customForm.passenger_email}
                onChange={(e) => setCustomForm({ ...customForm, passenger_email: e.target.value })}
                placeholder="e.g. passenger@email.com"
                className="w-full bg-slate-800/80 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-500/30 transition-all"
              />
            </div>
          </div>

          <div>
            <label className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider block mb-1">
              Passenger Inquiry / Issue Description *
            </label>
            <textarea
              required
              rows={3}
              value={customForm.description}
              onChange={(e) => setCustomForm({ ...customForm, description: e.target.value })}
              placeholder="Enter passenger issue text (try adding conflicting dates, missing luggage tags, or clear 24h refund requests)..."
              className="w-full bg-slate-800/80 border border-slate-700/80 rounded-xl p-3 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-500/30 leading-relaxed transition-all"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setShowCustomForm(false)}
              className="px-3.5 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 text-xs font-semibold transition-all"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={creatingCustom}
              className="btn-aviation px-4 py-2 rounded-xl bg-gradient-to-r from-sky-600 to-blue-600 hover:from-sky-500 hover:to-blue-500 text-white text-xs font-semibold shadow-lg shadow-sky-500/25 disabled:opacity-50 transition-all active:scale-95"
            >
              {creatingCustom ? 'Creating & Queueing...' : 'Create & Evaluate'}
            </button>
          </div>
        </form>
      )}

      {/* Main 2-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* LEFT COLUMN: Ticket Directory, Presets, Passenger Dossier (5 cols) */}
        <div className="lg:col-span-5 space-y-5">
          {/* Section 11: Benchmark Test Scenarios Card */}
          <div className="aviation-glass-card p-5 rounded-2xl bg-slate-900/80 border border-slate-800/90 shadow-xl backdrop-blur-xl space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center gap-1.5 font-mono">
                <Sparkles className="w-3.5 h-3.5 text-sky-400" /> Benchmark Evaluation Presets
              </span>
              <span className="text-[10px] text-slate-400 font-mono">High vs Low Confidence Tests</span>
            </div>

            <p className="text-[11px] text-slate-300 leading-relaxed">
              Test model calibration with deliberately clear, ambiguous, incomplete, contradictory, or unsupported passenger queries:
            </p>

            <div className="space-y-2">
              {BENCHMARK_TEST_SUITE.map((bCase) => (
                <div
                  key={bCase.id}
                  className={`p-3 rounded-xl border text-xs transition-all duration-200 ${
                    activeBenchmark?.id === bCase.id
                      ? 'bg-sky-500/15 border-sky-400/50 shadow-md shadow-sky-500/10'
                      : 'bg-slate-950/70 border-slate-800/80 hover:border-sky-500/40 hover:bg-slate-900/60'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-white">{bCase.name}</span>
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border backdrop-blur-sm ${bCase.badgeClass}`}>
                          {bCase.badge}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 leading-tight line-clamp-1">{bCase.description}</p>
                    </div>

                    <button
                      onClick={() => handleRunBenchmarkCase(bCase)}
                      disabled={resolving}
                      className="btn-aviation px-3 py-1.5 rounded-lg bg-gradient-to-r from-sky-600 to-blue-600 hover:from-sky-500 hover:to-blue-500 text-white font-semibold text-[11px] flex items-center gap-1 flex-shrink-0 shadow-sm disabled:opacity-50 active:scale-95 transition-all"
                    >
                      <span>Run</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Ticket Selector & Dossier Card */}
          <div className="aviation-glass-card p-5 rounded-2xl bg-slate-900/80 border border-slate-800/90 shadow-xl backdrop-blur-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2 font-mono">
                <Plane className="w-3.5 h-3.5 text-sky-400" /> Ticket Dossier
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-sky-500/15 text-sky-300 border border-sky-500/30">
                {selectedTicket?.status || 'SUBMITTED'}
              </span>
            </div>

            {/* Ticket Selector Dropdown */}
            <div>
              <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                Select Ticket From Queue:
              </label>
              <select
                value={selectedTicketId || ''}
                onChange={(e) => {
                  setSelectedTicketId(parseInt(e.target.value, 10));
                  setActiveBenchmark(null);
                }}
                className="w-full bg-slate-950/80 border border-slate-700/80 text-slate-200 text-xs rounded-xl px-3 py-2 font-medium focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-500/30 transition-all cursor-pointer"
              >
                {tickets.map((t) => (
                  <option key={t.id} value={t.id} className="bg-slate-900">
                    {t.ticket_number || `TK-${String(t.id).padStart(4, '0')}`} — {t.passenger_name || 'Passenger'} (
                    {t.category})
                  </option>
                ))}
              </select>
            </div>

            {selectedTicket ? (
              <div className="space-y-3.5 text-sm">
                <div>
                  <h3 className="font-bold text-white text-sm leading-snug font-display">{selectedTicket.title}</h3>
                  <p className="text-xs text-sky-400 mt-1 font-mono">
                    Ticket Ref: {selectedTicket.ticket_number || `TK-${String(selectedTicket.id).padStart(4, '0')}`}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3 pt-2.5 border-t border-slate-800/80 text-xs">
                  <div>
                    <span className="text-slate-400 block text-[11px]">Passenger Name</span>
                    <span className="font-semibold text-slate-200 mt-0.5 block">{selectedTicket.passenger_name || 'Passenger'}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Passenger Email</span>
                    <span className="font-semibold text-slate-200 mt-0.5 block truncate">{selectedTicket.passenger_email || 'N/A'}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Booking Reference (PNR)</span>
                    <span className="font-mono font-bold text-sky-400 mt-0.5 block">{selectedTicket.booking_reference || 'N/A'}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Flight Number</span>
                    <span className="font-mono font-bold text-emerald-400 mt-0.5 block">{selectedTicket.flight_number || 'N/A'}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Category</span>
                    <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-800/80 text-slate-300 border border-slate-700/80 inline-block mt-0.5">
                      {selectedTicket.category}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Travel Date</span>
                    <span className="text-slate-300 font-medium mt-0.5 block">{selectedTicket.travel_date || 'N/A'}</span>
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-800/80">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-300 block mb-2 font-mono text-[11px]">
                    Detailed Passenger Problem Description
                  </span>
                  <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800/80 text-xs text-slate-300 leading-relaxed max-h-48 overflow-y-auto">
                    {selectedTicket.description}
                  </div>
                </div>
              </div>
            ) : (
              <div className="py-8 text-center text-slate-500 text-xs">Select or create a ticket to inspect details.</div>
            )}
          </div>

          {/* Quick Navigation to 5-Agent Workflow */}
          <div className="p-4 rounded-xl aviation-glass-card bg-slate-900/80 border border-slate-800/90 flex items-center justify-between text-xs backdrop-blur-xl">
            <div>
              <span className="font-bold text-white block">Need Multi-Agent Orchestration?</span>
              <span className="text-slate-400">Run the 5-agent pipeline (Diagnosis → Retrieval → Resolution → Validation → Escalation).</span>
            </div>
            <button
              onClick={() => navigate(`/multi-agent-workflow?ticketId=${selectedTicketId}`)}
              className="btn-aviation px-3 py-2 rounded-lg bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 font-semibold flex items-center gap-1.5 transition-all flex-shrink-0 active:scale-95"
            >
              Open Workflow <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* RIGHT COLUMN: AI Solution, Grounding, Validation, Human Ground Truth (7 cols) */}
        <div className="lg:col-span-7 space-y-5">
          {resolving ? (
            <div className="aviation-glass-card p-12 rounded-2xl bg-slate-900/80 border border-slate-800/90 text-center space-y-4 backdrop-blur-xl shadow-xl">
              <RotateCw className="w-9 h-9 text-sky-400 animate-spin mx-auto" />
              <div className="space-y-1">
                <h3 className="font-bold text-white text-base font-display">Retrieving Knowledge & Synthesizing Solution</h3>
                <p className="text-xs text-slate-300">
                  Searching airline vector store, validating policy guardrails, and computing confidence score...
                </p>
              </div>
            </div>
          ) : aiResult ? (
            <>
              {/* Telemetry & Confidence Score Header Banner */}
              <div
                className={`aviation-glass-card p-5 rounded-2xl border shadow-xl backdrop-blur-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 relative overflow-hidden ${
                  aiResult.confidence_score >= aiResult.threshold
                    ? 'bg-emerald-950/20 border-emerald-500/30'
                    : 'bg-amber-950/20 border-amber-500/30'
                }`}
              >
                <div className="flex items-center gap-3.5 relative z-10">
                  <div
                    className={`w-14 h-14 rounded-2xl flex flex-col items-center justify-center font-bold font-mono text-base shadow-lg ${
                      aiResult.confidence_score >= aiResult.threshold
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/35 shadow-emerald-500/10'
                        : 'bg-amber-500/20 text-amber-400 border border-amber-500/35 shadow-amber-500/10'
                    }`}
                  >
                    <span>{aiResult.confidence_score}%</span>
                    <span className="text-[9px] uppercase tracking-wider font-mono font-bold">
                      {aiResult.confidence_score >= aiResult.threshold ? 'Pass' : 'Escalate'}
                    </span>
                  </div>

                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm text-white font-display">
                        {aiResult.confidence_score >= aiResult.threshold
                          ? 'High Confidence Grounded Solution'
                          : 'Review Recommended (Under 70% Policy Gate)'}
                      </span>
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border backdrop-blur-sm ${
                          aiResult.validation.verdict === 'PASS'
                            ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                            : 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                        }`}
                      >
                        VALIDATION: {aiResult.validation.verdict}
                      </span>
                    </div>

                    <div className="flex items-center gap-3 text-xs text-slate-400 mt-1 font-mono">
                      <span>Model: <strong className="text-slate-200">{aiResult.model_name || 'AeroAssist-Agentic-v1'}</strong></span>
                      <span>•</span>
                      <span>Latency: <strong className="text-slate-200">{aiResult.latency_ms || 135} ms</strong></span>
                      {aiResult.evaluation_id && (
                        <>
                          <span>•</span>
                          <span>Eval ID: <strong className="text-sky-400 font-mono">#{aiResult.evaluation_id}</strong></span>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 self-end sm:self-auto relative z-10">
                  <button
                    onClick={handleRegenerate}
                    title="Regenerate with RAG"
                    className="btn-aviation px-3.5 py-2 rounded-xl bg-slate-800/90 hover:bg-slate-700/90 text-slate-200 border border-slate-700/80 transition-all text-xs font-semibold flex items-center gap-1.5 active:scale-95 shadow-sm"
                  >
                    <RotateCw className="w-3.5 h-3.5 text-sky-400" /> Regenerate
                  </button>
                </div>
              </div>

              {/* Synthesized Passenger Response Card */}
              <div className="aviation-glass-card p-6 rounded-2xl bg-slate-900/80 border border-slate-800/90 shadow-xl backdrop-blur-xl space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <div className="flex items-center gap-2 font-mono">
                    <Bot className="w-4 h-4 text-sky-400" />
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-200">
                      Generated Passenger Communication
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setIsEditing(!isEditing)}
                      className="px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-800/80 hover:bg-slate-700/80 text-slate-200 border border-slate-700/80 flex items-center gap-1.5 transition-all"
                    >
                      <Edit3 className="w-3 h-3 text-sky-400" />
                      {isEditing ? 'Preview' : 'Edit Text'}
                    </button>
                  </div>
                </div>

                {isEditing ? (
                  <textarea
                    value={editedResponse}
                    onChange={(e) => setEditedResponse(e.target.value)}
                    rows={8}
                    className="w-full bg-slate-950/80 border border-sky-500/50 rounded-xl p-3.5 text-xs text-slate-200 font-sans focus:outline-none focus:ring-1 focus:ring-sky-500 leading-relaxed"
                  />
                ) : (
                  <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 text-xs text-slate-200 whitespace-pre-line leading-relaxed font-sans">
                    {editedResponse}
                  </div>
                )}

                {/* Grounding Citations */}
                <div className="pt-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-300 block mb-2 flex items-center gap-1.5 font-mono">
                    <BookOpen className="w-3.5 h-3.5 text-sky-400" /> Retrieved Source Documents & Excerpts (
                    {aiResult.retrieved_sources.length})
                  </span>
                  {aiResult.retrieved_sources.length === 0 ? (
                    <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-200">
                      No matching airline knowledge documents found for this query. The response is flagged as ungrounded and requires supervisor review.
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {aiResult.retrieved_sources.map((src, i) => (
                        <div
                          key={i}
                          className="p-3 rounded-xl bg-slate-950/70 border border-slate-800/80 text-xs space-y-1 hover:border-sky-500/30 transition-colors"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-semibold text-white">{src.document_title}</span>
                            <span className="font-mono text-[11px] text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                              {src.similarity_percentage}% match
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-300 leading-relaxed italic">"{src.excerpt}"</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Validation Guardrail Checklist */}
                <div className="pt-3 border-t border-slate-800/80">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-300 block mb-2 flex items-center gap-1.5 font-mono">
                    <ShieldCheck className="w-3.5 h-3.5 text-sky-400" /> Validation Agent Policy & Safety Audit
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                    {aiResult.validation.validation_checks.map((chk, idx) => (
                      <div
                        key={idx}
                        className={`p-2.5 rounded-xl border flex items-start gap-2 ${
                          chk.status === 'PASS'
                            ? 'bg-emerald-500/10 border-emerald-500/25 text-slate-200'
                            : chk.status === 'CAUTION'
                            ? 'bg-amber-500/10 border-amber-500/25 text-slate-200'
                            : 'bg-rose-500/10 border-rose-500/25 text-slate-200'
                        }`}
                      >
                        {chk.status === 'PASS' ? (
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0 mt-0.5" />
                        ) : (
                          <AlertTriangle className="w-3.5 h-3.5 text-amber-400 flex-shrink-0 mt-0.5" />
                        )}
                        <div>
                          <span className="font-semibold text-white block text-[11px]">{chk.check}</span>
                          <span className="text-[10px] text-slate-400 leading-tight block">{chk.detail}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Section 10 & 11: Human Ground-Truth Feedback Evaluation Box */}
                {aiResult.evaluation_id && (
                  <div className="pt-4 border-t border-slate-800/80 bg-slate-950/60 p-4.5 rounded-2xl border border-slate-800/70 space-y-3.5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-sky-400" />
                        <span className="text-xs font-bold uppercase tracking-wider text-slate-200 font-mono">
                          Label Ground-Truth Accuracy for Telemetry Benchmark
                        </span>
                      </div>
                      <span className="text-[11px] font-mono text-sky-400 font-bold bg-sky-500/10 px-2 py-0.5 rounded border border-sky-500/20">
                        Record #{aiResult.evaluation_id}
                      </span>
                    </div>

                    <p className="text-[11px] text-slate-300">
                      As an authorized airline reviewer, evaluate whether this AI generated resolution is factually correct against verified policy:
                    </p>

                    <div className="flex flex-wrap items-center gap-2">
                      {[
                        { val: 'CORRECT', label: 'Correct', color: 'emerald' },
                        { val: 'PARTIALLY_CORRECT', label: 'Partially Correct', color: 'sky' },
                        { val: 'INCORRECT', label: 'Incorrect', color: 'rose' },
                        { val: 'UNABLE_TO_ASSESS', label: 'Unable to Assess', color: 'slate' }
                      ].map((btn) => (
                        <button
                          key={btn.val}
                          type="button"
                          onClick={() => setFeedbackLabel(btn.val as any)}
                          className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                            feedbackLabel === btn.val
                              ? 'bg-gradient-to-r from-sky-600 to-blue-600 text-white border-sky-400 shadow-sm'
                              : 'bg-slate-900 text-slate-300 border-slate-800 hover:border-slate-700'
                          }`}
                        >
                          {btn.label}
                        </button>
                      ))}
                    </div>

                    <div className="flex items-center gap-4 text-xs">
                      <span className="text-slate-400">Grounding Rating:</span>
                      <div className="flex items-center gap-1">
                        {[1, 2, 3, 4, 5].map((s) => (
                          <button
                            key={s}
                            type="button"
                            onClick={() => setFeedbackRating(s)}
                            className="p-1 text-amber-400 hover:scale-125 transition-transform"
                          >
                            <Star className={`w-4 h-4 ${s <= feedbackRating ? 'fill-amber-400' : 'text-slate-700'}`} />
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <input
                        type="text"
                        value={feedbackNotes}
                        onChange={(e) => setFeedbackNotes(e.target.value)}
                        placeholder="Optional evaluator review notes (e.g. valid under 24hr refund rule)..."
                        className="flex-1 bg-slate-900/90 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-500/30 transition-all"
                      />
                      <button
                        onClick={handleSubmitGroundTruthFeedback}
                        disabled={submittingFeedback || feedbackSubmitted}
                        className="btn-aviation px-4 py-2 rounded-xl bg-slate-800/90 hover:bg-slate-700/90 border border-slate-700/80 text-sky-400 hover:text-sky-300 text-xs font-semibold transition-all disabled:opacity-50 active:scale-95"
                      >
                        {feedbackSubmitted ? 'Recorded ✓' : submittingFeedback ? 'Submitting...' : 'Submit Feedback'}
                      </button>
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="pt-4 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3">
                  <div className="text-xs text-slate-400 flex items-center gap-1.5 font-mono">
                    <span>Threshold Gate:</span>
                    <strong className="text-emerald-400 font-mono">70.0%</strong>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleEscalate}
                      className="btn-aviation px-4 py-2.5 rounded-xl bg-slate-800/90 hover:bg-slate-700/90 text-amber-300 text-xs font-semibold flex items-center gap-2 transition-all border border-slate-700/80 active:scale-95 shadow-sm"
                    >
                      <ThumbsDown className="w-3.5 h-3.5" /> Escalate to Human Agent
                    </button>

                    <button
                      onClick={handleApproveAndResolve}
                      className="btn-aviation px-5 py-2.5 rounded-xl bg-gradient-to-r from-sky-600 to-blue-600 hover:from-sky-500 hover:to-blue-500 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-sky-500/25 transition-all active:scale-95"
                    >
                      <ThumbsUp className="w-3.5 h-3.5" /> Approve & Mark AI Resolved
                    </button>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="aviation-glass-card p-12 rounded-2xl bg-slate-900/80 border border-slate-800/90 text-center text-slate-400 text-sm backdrop-blur-xl">
              Select a ticket or benchmark preset on the left to synthesize its AI solution.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AiSolutionPage;
