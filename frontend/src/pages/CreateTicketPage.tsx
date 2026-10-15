import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ticketsApi } from '../services/api';
import { useAuth } from '../features/auth/AuthContext';
import {
  PlusCircle,
  Plane,
  Luggage,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  Upload,
  Calendar,
  User,
  Mail,
  FileText,
  Clock,
  ShieldCheck,
  Bot
} from 'lucide-react';

const AIRLINE_CATEGORIES = [
  'Booking and Reservation',
  'Cancellation and Refund',
  'Flight Delay',
  'Flight Cancellation',
  'Baggage',
  'Check-in and Boarding',
  'Seat Selection',
  'Payment',
  'Special Assistance',
  'Other'
];

const PRIORITIES = [
  { label: 'Low', value: 'Low', desc: 'General questions or post-travel feedback' },
  { label: 'Medium', value: 'Medium', desc: 'Standard modifications and baggage inquiries' },
  { label: 'High', value: 'High', desc: 'Disruptions on flights departing within 24 hours' },
  { label: 'Urgent', value: 'Urgent', desc: 'Stranded passengers, medical, or imminent departures' },
];

export const CreateTicketPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [passengerName, setPassengerName] = useState(user?.full_name || '');
  const [passengerEmail, setPassengerEmail] = useState(user?.email || '');
  const [bookingReference, setBookingReference] = useState('');
  const [flightNumber, setFlightNumber] = useState('');
  const [travelDate, setTravelDate] = useState('');
  const [subject, setSubject] = useState('');
  const [category, setCategory] = useState('Baggage');
  const [priority, setPriority] = useState('Medium');
  const [description, setDescription] = useState('');
  const [attachment, setAttachment] = useState<File | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [createdTicket, setCreatedTicket] = useState<{ id: number; ticket_number?: string } | null>(null);

  // Quick-fill demonstration templates
  const handlePreFill = (type: 'baggage' | 'cancellation' | 'wheelchair' | 'refund') => {
    setError('');
    if (type === 'baggage') {
      setPassengerName('David Miller');
      setPassengerEmail('david.miller@example.com');
      setBookingReference('DM8891');
      setFlightNumber('AA-114');
      setTravelDate(new Date().toISOString().split('T')[0]);
      setSubject('Checked bag missing on flight AA-114 baggage carousel at DFW');
      setCategory('Baggage');
      setPriority('High');
      setDescription(
        'Arrived on flight AA-114 from Chicago to DFW at carousel 4. Checked bag tag #AA-993812 did not appear after all other luggage was cleared. It is a navy blue Samsonite hard-shell suitcase containing essential medication and business suit.'
      );
    } else if (type === 'cancellation') {
      setPassengerName('Sophia Martinez');
      setPassengerEmail('sophia.m@example.com');
      setBookingReference('SM4920');
      setFlightNumber('AA-502');
      setTravelDate(new Date(Date.now() + 86400000).toISOString().split('T')[0]);
      setSubject('Connecting flight AA-502 cancelled due to mechanical failure');
      setCategory('Flight Cancellation');
      setPriority('Urgent');
      setDescription(
        'Our connecting flight AA-502 from Chicago ORD to London Heathrow was abruptly cancelled due to maintenance issues. We have an urgent visa interview tomorrow morning and need rebooking on the next partner flight or overnight accommodation.'
      );
    } else if (type === 'wheelchair') {
      setPassengerName('Eleanor Vance');
      setPassengerEmail('eleanor.v@example.com');
      setBookingReference('EV7731');
      setFlightNumber('AA-810');
      setTravelDate(new Date(Date.now() + 172800000).toISOString().split('T')[0]);
      setSubject('Requesting wheelchair ramp assistance for elderly passenger');
      setCategory('Special Assistance');
      setPriority('Medium');
      setDescription(
        'Traveling with elderly passenger recovering from hip surgery. Requesting gate-to-aircraft wheelchair assistance (WCHS) and aisle chair assistance for flight AA-810 from Miami to New York LGA.'
      );
    } else if (type === 'refund') {
      setPassengerName('Marcus Chen');
      setPassengerEmail('marcus.chen@example.com');
      setBookingReference('MC2094');
      setFlightNumber('AA-304');
      setTravelDate(new Date(Date.now() + 432000000).toISOString().split('T')[0]);
      setSubject('Requesting 24-hour full refund for Economy Basic ticket');
      setCategory('Cancellation and Refund');
      setPriority('Medium');
      setDescription(
        'Booked booking reference MC2094 8 hours ago on our official portal. Due to a schedule conflict, I must cancel the journey. Under the 24-hour cooling-off rule, please process a full credit card refund without cancellation penalties.'
      );
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      // Max 10MB
      if (file.size > 10 * 1024 * 1024) {
        setError('Attachment file size must be less than 10MB');
        return;
      }
      setAttachment(file);
    }
  };

  const validateEmail = (email: string) => {
    return /\S+@\S+\.\S+/.test(email);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validation
    if (!passengerName.trim()) {
      setError('Passenger name is required.');
      return;
    }
    if (!passengerEmail.trim() || !validateEmail(passengerEmail)) {
      setError('Please provide a valid passenger email address.');
      return;
    }
    if (!subject.trim()) {
      setError('Subject line is required.');
      return;
    }
    if (!description.trim() || description.length < 15) {
      setError('Please provide a detailed issue description (at least 15 characters).');
      return;
    }

    try {
      setLoading(true);

      const payload = {
        title: subject.trim(),
        subject: subject.trim(),
        description: description.trim(),
        passenger_name: passengerName.trim(),
        passenger_email: passengerEmail.trim(),
        booking_reference: bookingReference.trim().toUpperCase() || undefined,
        flight_number: flightNumber.trim().toUpperCase() || undefined,
        travel_date: travelDate || undefined,
        category,
        priority,
        urgency: priority,
        affected_service: 'Flight Operations',
      };

      const res = await ticketsApi.create(payload);
      setCreatedTicket({
        id: res.id,
        ticket_number: res.ticket_number || `TK-${String(res.id).padStart(4, '0')}`,
      });
    } catch (err: any) {
      console.error('Failed to create ticket', err);
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === 'string'
          ? detail
          : 'Unable to submit ticket to backend. Please check network connection and try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  // If successfully created, display professional outcome card
  if (createdTicket) {
    return (
      <div className="max-w-3xl mx-auto py-8 animate-fade-in-up">
        <div className="aviation-glass-card bg-slate-900/90 border border-emerald-500/30 rounded-3xl p-8 shadow-2xl space-y-6 relative overflow-hidden backdrop-blur-xl">
          <div className="absolute -right-20 -top-20 w-64 h-64 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none animate-pulse-glow" />
          
          <div className="w-16 h-16 rounded-2xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mx-auto shadow-lg shadow-emerald-500/10">
            <CheckCircle2 className="w-8 h-8" />
          </div>

          <div className="text-center space-y-2 relative z-10">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/30">
              Flight Ingestion Confirmed
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white pt-2 font-display">
              Passenger Ticket Ingested
            </h1>
            <p className="text-slate-300 text-sm max-w-md mx-auto leading-relaxed">
              Inquiry registered in commercial flight database and queued for automated resolution and agent evaluation.
            </p>
          </div>

          <div className="bg-slate-800/70 rounded-2xl p-5 border border-slate-700/80 space-y-3 font-mono text-xs relative z-10">
            <div className="flex justify-between items-center text-slate-300">
              <span className="text-slate-400">Assigned Ticket ID:</span>
              <span className="text-sky-400 font-bold text-base font-mono">{createdTicket.ticket_number}</span>
            </div>
            <div className="flex justify-between items-center text-slate-300">
              <span className="text-slate-400">Passenger:</span>
              <span className="text-white font-sans font-medium">{passengerName} ({passengerEmail})</span>
            </div>
            {bookingReference && (
              <div className="flex justify-between items-center text-slate-300">
                <span className="text-slate-400">PNR Reference:</span>
                <span className="text-emerald-400 font-bold">{bookingReference.toUpperCase()}</span>
              </div>
            )}
            {flightNumber && (
              <div className="flex justify-between items-center text-slate-300">
                <span className="text-slate-400">Flight:</span>
                <span className="text-white">{flightNumber.toUpperCase()}</span>
              </div>
            )}
            <div className="flex justify-between items-center text-slate-300">
              <span className="text-slate-400">Category:</span>
              <span className="text-sky-300">{category}</span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 relative z-10">
            <Link
              to={`/ai-solution?ticketId=${createdTicket.id}`}
              className="btn-aviation px-4 py-3 bg-gradient-to-r from-sky-600 via-sky-500 to-blue-600 hover:from-sky-500 hover:to-blue-500 text-white rounded-xl text-sm font-semibold flex items-center justify-center gap-2 shadow-lg shadow-sky-500/25 transition-all active:scale-95"
            >
              <Sparkles className="w-4 h-4" />
              Resolve with AI Solution
            </Link>
            <Link
              to={`/workflows?ticketId=${createdTicket.id}`}
              className="btn-aviation px-4 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-xl text-sm font-semibold flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/25 transition-all active:scale-95"
            >
              <Bot className="w-4 h-4" />
              Run 5-Agent Workflow
            </Link>
          </div>

          <div className="flex items-center justify-between pt-3 border-t border-slate-800 text-xs relative z-10">
            <button
              onClick={() => {
                setCreatedTicket(null);
                setSubject('');
                setDescription('');
                setBookingReference('');
                setFlightNumber('');
              }}
              className="text-slate-400 hover:text-white transition-colors"
            >
              + Submit another ticket
            </button>
            <Link
              to={`/tickets/${createdTicket.id}`}
              className="text-sky-400 hover:text-sky-300 flex items-center gap-1 font-medium transition-colors"
            >
              View Ticket Details &rarr;
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in-up">
      {/* Page Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="p-2.5 rounded-2xl bg-sky-500/10 text-sky-400 border border-sky-500/30 shadow-md shadow-sky-500/10">
              <Plane className="w-5 h-5 -rotate-45" />
            </span>
            <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white font-display">
              Create Passenger Support Ticket
            </h1>
          </div>
          <p className="text-sm text-slate-300 mt-1">
            Submit a passenger inquiry or flight disruption case into the AeroAssist AI pipeline.
          </p>
        </div>

        {/* Demo Preset Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-slate-400 font-mono uppercase tracking-wider">Fast Demo:</span>
          <button
            type="button"
            onClick={() => handlePreFill('baggage')}
            className="px-2.5 py-1.5 bg-slate-800/90 hover:bg-slate-700/90 text-sky-300 rounded-lg text-xs font-medium border border-slate-700/80 transition-all hover:scale-105 active:scale-95"
          >
            Baggage Claim
          </button>
          <button
            type="button"
            onClick={() => handlePreFill('cancellation')}
            className="px-2.5 py-1.5 bg-slate-800/90 hover:bg-slate-700/90 text-rose-300 rounded-lg text-xs font-medium border border-slate-700/80 transition-all hover:scale-105 active:scale-95"
          >
            Flight Cancellation
          </button>
          <button
            type="button"
            onClick={() => handlePreFill('wheelchair')}
            className="px-2.5 py-1.5 bg-slate-800/90 hover:bg-slate-700/90 text-emerald-300 rounded-lg text-xs font-medium border border-slate-700/80 transition-all hover:scale-105 active:scale-95"
          >
            Special Assistance
          </button>
          <button
            type="button"
            onClick={() => handlePreFill('refund')}
            className="px-2.5 py-1.5 bg-slate-800/90 hover:bg-slate-700/90 text-purple-300 rounded-lg text-xs font-medium border border-slate-700/80 transition-all hover:scale-105 active:scale-95"
          >
            24hr Refund
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Form */}
      <form onSubmit={handleSubmit} className="aviation-glass-card bg-slate-900/80 border border-slate-800/90 rounded-2xl p-6 sm:p-8 space-y-6 shadow-2xl backdrop-blur-xl relative overflow-hidden">
        {/* Subtle decorative glow */}
        <div className="absolute top-0 right-0 w-80 h-80 bg-sky-500/5 rounded-full blur-3xl pointer-events-none" />

        {/* Passenger Information Row */}
        <div className="relative z-10">
          <h2 className="text-xs font-bold uppercase tracking-wider text-sky-400 mb-3 flex items-center gap-2 font-mono">
            <User className="w-4 h-4 text-sky-400" /> Passenger Information
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Passenger Full Name <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                required
                value={passengerName}
                onChange={(e) => setPassengerName(e.target.value)}
                placeholder="e.g. Jane Doe"
                className="w-full px-3.5 py-2.5 bg-slate-800/80 border border-slate-700/80 rounded-xl text-sm text-white placeholder-slate-400 focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-500/30 transition-all"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Passenger Email <span className="text-rose-400">*</span>
              </label>
              <input
                type="email"
                required
                value={passengerEmail}
                onChange={(e) => setPassengerEmail(e.target.value)}
                placeholder="e.g. jane.doe@example.com"
                className="w-full px-3.5 py-2.5 bg-slate-800/80 border border-slate-700/80 rounded-xl text-sm text-white placeholder-slate-400 focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-500/30 transition-all"
              />
            </div>
          </div>
        </div>

        {/* Flight & Booking Reference Row */}
        <div className="pt-3 border-t border-slate-800/80 relative z-10">
          <h2 className="text-xs font-bold uppercase tracking-wider text-sky-400 mb-3 flex items-center gap-2 font-mono">
            <Plane className="w-4 h-4 text-sky-400" /> Flight & Travel Details
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Booking Reference (PNR)
              </label>
              <input
                type="text"
                maxLength={8}
                value={bookingReference}
                onChange={(e) => setBookingReference(e.target.value.toUpperCase())}
                placeholder="e.g. AA8492"
                className="w-full px-3.5 py-2.5 bg-slate-800/80 border border-slate-700/80 rounded-xl text-sm text-white font-mono placeholder-slate-400 focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-500/30 uppercase transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Flight Number
              </label>
              <input
                type="text"
                value={flightNumber}
                onChange={(e) => setFlightNumber(e.target.value.toUpperCase())}
                placeholder="e.g. AA-304"
                className="w-full px-3.5 py-2.5 bg-slate-800/80 border border-slate-700/80 rounded-xl text-sm text-white font-mono placeholder-slate-400 focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-500/30 uppercase transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Travel Date
              </label>
              <input
                type="date"
                value={travelDate}
                onChange={(e) => setTravelDate(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-800/80 border border-slate-700/80 rounded-xl text-sm text-white placeholder-slate-400 focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-500/30 transition-all cursor-pointer"
              />
            </div>
          </div>
        </div>

        {/* Ingest Category & Severity Row */}
        <div className="pt-3 border-t border-slate-800/80 relative z-10">
          <h2 className="text-xs font-bold uppercase tracking-wider text-sky-400 mb-3 flex items-center gap-2 font-mono">
            <FileText className="w-4 h-4 text-sky-400" /> Case Classification
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Inquiry Category <span className="text-rose-400">*</span>
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-800/80 border border-slate-700/80 rounded-xl text-sm text-white focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-500/30 transition-all cursor-pointer"
              >
                {AIRLINE_CATEGORIES.map((cat) => (
                  <option key={cat} value={cat} className="bg-slate-900 text-slate-200">
                    {cat}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Priority Level <span className="text-rose-400">*</span>
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-800/80 border border-slate-700/80 rounded-xl text-sm text-white focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-500/30 transition-all cursor-pointer"
              >
                {PRIORITIES.map((p) => (
                  <option key={p.value} value={p.value} className="bg-slate-900 text-slate-200">
                    {p.label} — {p.desc}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Subject & Description */}
        <div className="pt-3 border-t border-slate-800/80 space-y-4 relative z-10">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Subject Line / Issue Summary <span className="text-rose-400">*</span>
            </label>
            <input
              type="text"
              required
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="e.g. Delayed bag at baggage claim or missed connection"
              className="w-full px-3.5 py-2.5 bg-slate-800/80 border border-slate-700/80 rounded-xl text-sm text-white placeholder-slate-400 focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-500/30 transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Detailed Passenger Description <span className="text-rose-400">*</span>
            </label>
            <textarea
              required
              rows={5}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Provide complete details including bag tag numbers, airport terminals, connecting flight itineraries, or special passenger requests..."
              className="w-full px-3.5 py-2.5 bg-slate-800/80 border border-slate-700/80 rounded-xl text-sm text-white placeholder-slate-400 focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-500/30 transition-all leading-relaxed"
            />
          </div>

          {/* Attachment Upload */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Attach Boarding Pass or Baggage Tag (Optional)
            </label>
            <div className="flex items-center gap-3">
              <label className="px-4 py-2.5 bg-slate-800/90 hover:bg-slate-700/90 border border-slate-700/80 rounded-xl text-xs text-slate-300 font-medium cursor-pointer flex items-center gap-2 transition-all hover:border-sky-500/50">
                <Upload className="w-3.5 h-3.5 text-sky-400" />
                <span>{attachment ? attachment.name : 'Upload File (PDF, PNG, JPG)'}</span>
                <input
                  type="file"
                  accept=".pdf,.png,.jpg,.jpeg,.txt"
                  onChange={handleFileChange}
                  className="hidden"
                />
              </label>
              {attachment && (
                <button
                  type="button"
                  onClick={() => setAttachment(null)}
                  className="text-xs text-rose-400 hover:underline"
                >
                  Remove
                </button>
              )}
            </div>
            <p className="text-[11px] text-slate-400 mt-1 font-mono">Maximum upload size: 10MB</p>
          </div>
        </div>

        {/* Submit Actions */}
        <div className="pt-4 border-t border-slate-800/90 flex flex-col sm:flex-row items-center justify-between gap-4 relative z-10">
          <p className="text-xs text-slate-400 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-sky-400" />
            <span>Guaranteed data persistence & instant AI classification</span>
          </p>

          <button
            type="submit"
            disabled={loading}
            className="btn-aviation w-full sm:w-auto px-6 py-3 bg-gradient-to-r from-sky-600 via-sky-500 to-blue-600 hover:from-sky-500 hover:to-blue-500 disabled:opacity-50 text-white rounded-xl text-sm font-semibold shadow-lg shadow-sky-500/25 transition-all flex items-center justify-center gap-2 active:scale-95"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Submitting Ticket...
              </>
            ) : (
              <>
                <PlusCircle className="w-4 h-4" />
                Submit Passenger Ticket
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
