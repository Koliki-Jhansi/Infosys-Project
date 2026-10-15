import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../features/auth/AuthContext';
import {
  Plane,
  ShieldCheck,
  Bot,
  Luggage,
  Clock,
  Compass,
  ArrowRight,
  Sparkles,
  CheckCircle2,
  FileText,
  UserCheck,
  BarChart3,
  HelpCircle,
  TrendingUp,
  Cpu,
  Layers,
  Search,
  ExternalLink,
  BookOpen
} from 'lucide-react';
import { FlightBackground } from '../components/common/FlightBackground';

export const WelcomePage: React.FC = () => {
  const { user, loginAsDemo } = useAuth();
  const navigate = useNavigate();

  const handleDemoStart = async (role: 'ADMIN' | 'SUPPORT_AGENT' | 'PASSENGER') => {
    await loginAsDemo(role);
    navigate('/home');
  };

  const scrollToSection = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-sky-500/30 relative">
      <FlightBackground variant="hero" showRadar={true} />

      {/* Navigation Header */}
      <header className="border-b border-sky-500/15 bg-slate-950/80 backdrop-blur-xl sticky top-0 z-50 shadow-lg shadow-black/40">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          {/* Logo & Brand */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 via-blue-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-sky-500/25 text-white font-bold transition-transform hover:scale-105">
              <Plane className="w-5 h-5 -rotate-45" />
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight text-white flex items-center gap-1.5 font-['Outfit']">
                AeroAssist <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 via-cyan-300 to-blue-400 font-extrabold">AI</span>
              </span>
              <p className="text-[11px] text-slate-400 hidden sm:block">Intelligent Airline Passenger Support Platform</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-6 text-xs font-semibold text-slate-300">
            <button onClick={() => scrollToSection('overview')} className="hover:text-white transition-colors">
              Overview
            </button>
            <button onClick={() => scrollToSection('features')} className="hover:text-white transition-colors">
              Features
            </button>
            <button onClick={() => scrollToSection('solutions')} className="hover:text-white transition-colors">
              AI Solutions
            </button>
            <button onClick={() => scrollToSection('workflow')} className="hover:text-white transition-colors">
              5-Agent Workflow
            </button>
            <button onClick={() => scrollToSection('analytics')} className="hover:text-white transition-colors">
              Analytics Overview
            </button>
            <button onClick={() => scrollToSection('how-it-works')} className="hover:text-white transition-colors">
              How It Works
            </button>
          </nav>

          {/* Authentication Action Buttons */}
          <div className="flex items-center gap-3">
            {user ? (
              <Link
                to="/home"
                className="px-4 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold flex items-center gap-2 shadow-md shadow-sky-500/20 transition-all"
              >
                Go to Home Console <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="px-3.5 py-2 rounded-xl text-slate-300 hover:text-white hover:bg-slate-800 text-xs font-medium transition-all"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  className="px-4 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold shadow-md shadow-sky-500/20 transition-all"
                >
                  Get Started
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section id="overview" className="relative overflow-hidden pt-16 pb-20 md:pt-24 md:pb-28 border-b border-slate-800/80">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[650px] h-[350px] bg-sky-500/10 blur-[130px] rounded-full pointer-events-none"></div>
        <div className="absolute top-1/3 right-10 w-[350px] h-[350px] bg-blue-600/10 blur-[110px] rounded-full pointer-events-none"></div>

        <div className="max-w-7xl mx-auto px-6 relative z-10 text-center">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-sky-500/10 border border-sky-500/20 text-sky-300 text-xs font-semibold mb-6 shadow-sm">
            <Sparkles className="w-3.5 h-3.5 text-sky-400" />
            <span>Autonomous 5-Agent Multi-Agent Airline Support</span>
          </div>

          <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold text-white tracking-tight leading-tight max-w-4xl mx-auto">
            Smarter Airline Support. Faster Resolutions. Better Passenger Experiences.
          </h1>

          <p className="mt-6 text-base sm:text-lg md:text-xl text-slate-300 max-w-3xl mx-auto leading-relaxed">
            AeroAssist AI helps airline support teams understand passenger issues, retrieve relevant knowledge, generate validated responses, and escalate complex cases through an intelligent multi-agent workflow.
          </p>

          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <Link
              to="/register"
              className="px-6 py-3.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-semibold text-sm sm:text-base shadow-lg shadow-sky-600/25 flex items-center gap-2 transition-all group"
            >
              Get Started <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
            <button
              onClick={() => scrollToSection('features')}
              className="px-6 py-3.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-sm sm:text-base border border-slate-700 transition-all flex items-center gap-2"
            >
              <Sparkles className="w-4 h-4 text-sky-400" />
              Explore AI Features
            </button>
          </div>

          {/* 1-Click Persona Quick Evaluation Bar */}
          <div className="mt-12 max-w-2xl mx-auto p-4 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl backdrop-blur-md">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 text-center">
              1-Click Demo Evaluation Personas
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              <button
                onClick={() => handleDemoStart('ADMIN')}
                className="px-3.5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700/80 border border-slate-700/80 text-left transition-all group"
              >
                <div className="flex items-center gap-2 text-xs font-semibold text-sky-400">
                  <ShieldCheck className="w-3.5 h-3.5" /> Administrator
                </div>
                <p className="text-[11px] text-slate-400 mt-0.5">Full governance & settings</p>
              </button>

              <button
                onClick={() => handleDemoStart('SUPPORT_AGENT')}
                className="px-3.5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700/80 border border-slate-700/80 text-left transition-all group"
              >
                <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400">
                  <UserCheck className="w-3.5 h-3.5" /> Support Agent
                </div>
                <p className="text-[11px] text-slate-400 mt-0.5">Triage, AI review & resolve</p>
              </button>

              <button
                onClick={() => handleDemoStart('PASSENGER')}
                className="px-3.5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700/80 border border-slate-700/80 text-left transition-all group"
              >
                <div className="flex items-center gap-2 text-xs font-semibold text-amber-400">
                  <Luggage className="w-3.5 h-3.5" /> Passenger
                </div>
                <p className="text-[11px] text-slate-400 mt-0.5">Submit tickets & tracking</p>
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Section 1: Intelligent Ticket Management */}
      <section id="features" className="py-16 md:py-20 bg-slate-900/30 border-b border-slate-800/80">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-4">
              <span className="text-xs font-bold uppercase tracking-wider text-sky-400 bg-sky-500/10 px-3 py-1 rounded-full border border-sky-500/20">
                Core Foundation
              </span>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                Intelligent Passenger Ticket Management
              </h2>
              <p className="text-sm sm:text-base text-slate-300 leading-relaxed">
                Capture every passenger incident with structured flight dossiers. From booking references (PNR) and flight numbers to baggage tags and disruption logs, every inquiry is structured, classified, and tracked with full audit history.
              </p>
              <ul className="space-y-2.5 text-xs sm:text-sm text-slate-300 pt-2">
                <li className="flex items-center gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-sky-400 flex-shrink-0" />
                  <span>Automated entity extraction: PNR, flight route, departure time, and urgency</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-sky-400 flex-shrink-0" />
                  <span>Real-time status filtering across Open, In Progress, AI Resolved, and Escalated</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-sky-400 flex-shrink-0" />
                  <span>Internal support notes, station agent assignments, and CSV audit export</span>
                </li>
              </ul>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-2xl space-y-4 font-mono text-xs">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <span className="text-slate-400 font-sans font-bold">Live Ingested Passenger Case</span>
                <span className="text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                  TK-0018
                </span>
              </div>
              <div className="space-y-2 text-slate-300">
                <div className="flex justify-between">
                  <span className="text-slate-500">Passenger:</span>
                  <span className="text-white font-sans font-medium">Captain James Kirk</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Booking PNR:</span>
                  <span className="text-sky-300 font-bold">JK9921</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Flight:</span>
                  <span className="text-emerald-400">AA-902 (JFK &rarr; LHR)</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Category:</span>
                  <span className="text-white">Baggage Claim</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Confidence:</span>
                  <span className="text-emerald-400 font-bold">87.0% (&ge; 70% threshold)</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Section 2: Knowledge-Grounded AI Assistance */}
      <section id="solutions" className="py-16 md:py-20 bg-slate-950 border-b border-slate-800/80">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="order-2 lg:order-1 bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-2xl space-y-4">
              <div className="flex items-center gap-2 text-xs font-bold text-sky-400 uppercase tracking-wider">
                <BookOpen className="w-4 h-4" /> Grounded In Real Aviation Policies
              </div>
              <div className="space-y-2.5 text-xs">
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                  <p className="font-semibold text-white">Baggage Allowances, Lost & Delayed Claims</p>
                  <p className="text-slate-400 mt-1">PIR filing deadlines, Montreal Convention limits ($1,728 SDR), emergency toiletry allowances.</p>
                </div>
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                  <p className="font-semibold text-white">Cancellation and 24-Hour Cooling-Off Refund</p>
                  <p className="text-slate-400 mt-1">Full refund rules within 24 hours of booking for flights departing 7+ days in advance.</p>
                </div>
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                  <p className="font-semibold text-white">Flight Delay & Disruption Duty of Care</p>
                  <p className="text-slate-400 mt-1">Meal vouchers, hotel accommodation, and re-routing standards on 3+ hour delays.</p>
                </div>
              </div>
            </div>

            <div className="order-1 lg:order-2 space-y-4">
              <span className="text-xs font-bold uppercase tracking-wider text-cyan-400 bg-cyan-500/10 px-3 py-1 rounded-full border border-cyan-500/20">
                Retrieval-Augmented Generation
              </span>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                Knowledge-Grounded AI Assistance
              </h2>
              <p className="text-sm sm:text-base text-slate-300 leading-relaxed">
                Never guess airline policies or invent promises. AeroAssist AI indexes commercial operating guidelines, tariffs, and runbooks into a dense vector index, retrieving exact citation passages before answering passenger inquiries.
              </p>
              <ul className="space-y-2 text-xs sm:text-sm text-slate-300 pt-2">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-cyan-400" />
                  <span>Strict grounding: Answers cite document title, chunk index, and relevance score</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-cyan-400" />
                  <span>Explicit insufficient-evidence fallback when policies are missing or ambiguous</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-cyan-400" />
                  <span>Document upload support for PDF, TXT, and Markdown files</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Section 3: Five-Agent Resolution Workflow */}
      <section id="workflow" className="py-16 md:py-20 bg-slate-900/40 border-b border-slate-800/80">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <span className="text-xs font-bold uppercase tracking-wider text-indigo-400 bg-indigo-500/10 px-3 py-1 rounded-full border border-indigo-500/20">
            Multi-Agent Architecture
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight mt-3">
            Five-Agent Cooperative Resolution Pipeline
          </h2>
          <p className="text-slate-400 text-sm sm:text-base max-w-2xl mx-auto mt-2">
            Five specialized autonomous agents collaborate in an audited sequential pipeline to diagnose, retrieve, generate, validate, and escalate airline passenger cases.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mt-12 text-left">
            {/* Agent 1 */}
            <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-md space-y-2.5">
              <div className="w-9 h-9 rounded-xl bg-sky-500/10 text-sky-400 border border-sky-500/20 flex items-center justify-center font-bold text-xs">
                1
              </div>
              <h3 className="font-bold text-white text-sm">Diagnosis Agent</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Extracts PNR, Flight #, dates; detects inquiry category and evaluates flight disruption urgency.
              </p>
            </div>

            {/* Agent 2 */}
            <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-md space-y-2.5">
              <div className="w-9 h-9 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center justify-center font-bold text-xs">
                2
              </div>
              <h3 className="font-bold text-white text-sm">Retrieval Agent</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Searches policy runbooks, ranks relevant chunks with dense vector embeddings and returns source citations.
              </p>
            </div>

            {/* Agent 3 */}
            <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-md space-y-2.5">
              <div className="w-9 h-9 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20 flex items-center justify-center font-bold text-xs">
                3
              </div>
              <h3 className="font-bold text-white text-sm">Resolution Agent</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Synthesizes a courteous, empathetic, passenger-friendly solution grounded strictly in verified policy.
              </p>
            </div>

            {/* Agent 4 */}
            <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-md space-y-2.5">
              <div className="w-9 h-9 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center font-bold text-xs">
                4
              </div>
              <h3 className="font-bold text-white text-sm">Validation Agent</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Checks relevance, flags unauthorized financial compensation promises, and detects contradictions.
              </p>
            </div>

            {/* Agent 5 */}
            <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-md space-y-2.5">
              <div className="w-9 h-9 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center justify-center font-bold text-xs">
                5
              </div>
              <h3 className="font-bold text-white text-sm">Escalation Agent</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Enforces the 70% confidence threshold, checks validation clearance, and assigns final ticket resolution status.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Section 4: AI Performance Monitoring & Human Escalation */}
      <section id="analytics" className="py-16 md:py-20 bg-slate-950 border-b border-slate-800/80">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-4">
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">
                Observability & Governance
              </span>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                AI Performance Monitoring & Human Oversight
              </h2>
              <p className="text-sm sm:text-base text-slate-300 leading-relaxed">
                Measure actual AI accuracy rather than guessing. AeroAssist AI tracks every evaluation, validation pass rate, latency, and escalation cause. Support supervisors can review and label responses to measure true ground-truth accuracy.
              </p>
              <div className="grid grid-cols-2 gap-3 pt-2 text-xs">
                <div className="p-3 bg-slate-900 rounded-xl border border-slate-800">
                  <span className="text-slate-400 block text-[11px]">Default Policy Gate</span>
                  <span className="text-emerald-400 font-bold text-base font-mono">70.0% Confidence</span>
                </div>
                <div className="p-3 bg-slate-900 rounded-xl border border-slate-800">
                  <span className="text-slate-400 block text-[11px]">Human Supervisory Gate</span>
                  <span className="text-amber-400 font-bold text-base font-mono">Mandatory Review</span>
                </div>
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-2xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <span className="text-xs font-bold uppercase text-slate-400 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-emerald-400" /> Live AI Telemetry Snapshot
                </span>
                <span className="text-[11px] font-mono text-slate-400">Database Grounded</span>
              </div>
              <div className="space-y-3 font-mono text-xs">
                <div>
                  <div className="flex justify-between text-slate-300 mb-1">
                    <span>Validation Pass Rate:</span>
                    <span className="text-emerald-400 font-bold">88.5%</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                    <div className="bg-emerald-400 h-full rounded-full" style={{ width: '88.5%' }} />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-slate-300 mb-1">
                    <span>AI Resolution Rate:</span>
                    <span className="text-sky-400 font-bold">78.4%</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                    <div className="bg-sky-400 h-full rounded-full" style={{ width: '78.4%' }} />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-slate-300 mb-1">
                    <span>Human Escalation Rate:</span>
                    <span className="text-amber-400 font-bold">21.6%</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                    <div className="bg-amber-400 h-full rounded-full" style={{ width: '21.6%' }} />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Section 5: How AeroAssist Works */}
      <section id="how-it-works" className="py-16 md:py-20 bg-slate-900/30 border-b border-slate-800/80">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <span className="text-xs font-bold uppercase tracking-wider text-sky-400 bg-sky-500/10 px-3 py-1 rounded-full border border-sky-500/20">
            End-to-End Lifecycle
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight mt-3">
            How AeroAssist AI Works
          </h2>
          <p className="text-slate-400 text-sm sm:text-base max-w-2xl mx-auto mt-2">
            From initial passenger contact to verified resolution or supervisor handover in four simple steps.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mt-12 text-left">
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
              <span className="text-xs font-mono font-bold text-sky-400 bg-sky-500/10 px-2 py-0.5 rounded border border-sky-500/20">
                Step 1
              </span>
              <h3 className="font-bold text-white text-base">Ticket Ingestion</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Passenger submits inquiry with booking reference, flight details, and issue description.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
              <span className="text-xs font-mono font-bold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
                Step 2
              </span>
              <h3 className="font-bold text-white text-base">Policy Retrieval</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Relevant airline operating policies and passenger rights regulations are semantically retrieved.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
              <span className="text-xs font-mono font-bold text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20">
                Step 3
              </span>
              <h3 className="font-bold text-white text-base">AI Synthesis & Audit</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                A courteous solution is drafted and audited for accuracy, tone, and financial safety compliance.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
              <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                Step 4
              </span>
              <h3 className="font-bold text-white text-base">Resolve or Escalate</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Tickets meeting the 70% threshold are resolved; complex or low-confidence cases route to human staff.
              </p>
            </div>
          </div>

          <div className="mt-14">
            <Link
              to="/register"
              className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-semibold text-base shadow-xl shadow-sky-600/25 transition-all"
            >
              Get Started with AeroAssist AI <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto py-10 bg-slate-950 border-t border-slate-800 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2.5 text-slate-400">
            <div className="w-6 h-6 rounded-lg bg-sky-600 flex items-center justify-center text-white font-bold text-xs">
              <Plane className="w-3.5 h-3.5 -rotate-45" />
            </div>
            <span className="font-bold text-slate-200">AeroAssist AI</span>
            <span>— Intelligent Airline Passenger Support & Ticket Resolution</span>
          </div>

          <div className="flex items-center gap-6 text-slate-400">
            <Link to="/login" className="hover:text-white transition-colors">Sign In</Link>
            <Link to="/register" className="hover:text-white transition-colors">Register</Link>
            <span className="text-slate-600">|</span>
            <p>© 2026 AeroAssist AI Systems. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};
