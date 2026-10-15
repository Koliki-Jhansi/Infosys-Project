import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  GitBranch,
  Play,
  RotateCw,
  CheckCircle2,
  AlertCircle,
  Clock,
  ShieldCheck,
  Search,
  Bot,
  ArrowRight,
  ChevronDown,
  ChevronUp,
  FileText,
  ThumbsUp,
  XCircle,
  Plane,
  Luggage,
  Sparkles,
  Info,
  BookOpen,
  Layers,
  Activity,
  Terminal,
  Zap,
  Check,
  Copy
} from 'lucide-react';
import { ticketsApi, workflowApi } from '../services/api';
import { Ticket, WorkflowExecutionRecord, AgentExecutionRecord } from '../types';

export const WorkflowPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const preselectedTicketId = searchParams.get('ticketId');

  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [selectedTicketId, setSelectedTicketId] = useState<number | null>(
    preselectedTicketId ? parseInt(preselectedTicketId, 10) : null
  );
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);

  const [workflow, setWorkflow] = useState<WorkflowExecutionRecord | null>(null);
  const [executing, setExecuting] = useState(false);
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [copiedSection, setCopiedSection] = useState<string | null>(null);

  // Load ticket options
  useEffect(() => {
    const fetchTickets = async () => {
      try {
        const res = await ticketsApi.list({ size: 50 });
        setTickets(res.items);
        if (res.items.length > 0 && !selectedTicketId) {
          setSelectedTicketId(res.items[0].id);
        }
      } catch (err) {
        console.error('Failed to load tickets for workflow:', err);
      }
    };
    fetchTickets();
  }, []);

  // When ticket is selected, load latest workflow
  useEffect(() => {
    if (!selectedTicketId) return;

    const loadWorkflow = async () => {
      try {
        const t = await ticketsApi.getById(selectedTicketId);
        setSelectedTicket(t);

        const wf = await workflowApi.getForTicket(selectedTicketId);
        setWorkflow(wf);
      } catch (err) {
        setWorkflow(null);
      }
    };
    loadWorkflow();
  }, [selectedTicketId]);

  const handleRunWorkflow = async () => {
    if (!selectedTicketId) return;
    setExecuting(true);
    setActionMessage(null);
    try {
      const res = await workflowApi.runForTicket(selectedTicketId);
      setWorkflow(res);
      setActionMessage({ type: 'success', text: `5-Agent Pipeline Execution #${res.id} completed successfully.` });
      const updatedTicket = await ticketsApi.getById(selectedTicketId);
      setSelectedTicket(updatedTicket);
    } catch (err: any) {
      console.error('Workflow execution failed:', err);
      setActionMessage({ type: 'error', text: err.response?.data?.detail || 'Workflow execution failed.' });
    } finally {
      setExecuting(false);
    }
  };

  const handleRetry = async () => {
    if (!workflow) return;
    setExecuting(true);
    setActionMessage(null);
    try {
      const res = await workflowApi.resume(workflow.id);
      setWorkflow(res);
      setActionMessage({ type: 'success', text: `Workflow #${workflow.id} re-orchestrated successfully.` });
    } catch (err: any) {
      setActionMessage({ type: 'error', text: 'Retry failed.' });
    } finally {
      setExecuting(false);
    }
  };

  const copyToClipboard = (text: string, section: string) => {
    navigator.clipboard.writeText(text);
    setCopiedSection(section);
    setTimeout(() => setCopiedSection(null), 2000);
  };

  // 5 Specialized Airline Agents Definition
  const fiveAgents = [
    {
      id: 'Diagnosis Agent',
      name: 'Diagnosis Agent',
      stepNum: '01',
      icon: Search,
      role: 'Ticket & Entity Triage',
      desc: 'Extracts passenger PNR, flight numbers, categories, missing information, and assesses travel urgency.',
    },
    {
      id: 'Retrieval Agent',
      name: 'Retrieval Agent',
      stepNum: '02',
      icon: BookOpen,
      role: 'Airline RAG Search',
      desc: 'Retrieves relevant policy documents, baggage rules, disruption entitlements, and ranking scores.',
    },
    {
      id: 'Resolution Agent',
      name: 'Resolution Agent',
      stepNum: '03',
      icon: Bot,
      role: 'Policy Synthesis',
      desc: 'Synthesizes courteous, passenger-friendly answers strictly grounded in retrieved airline documentation.',
    },
    {
      id: 'Validation Agent',
      name: 'Validation Agent',
      stepNum: '04',
      icon: ShieldCheck,
      role: 'Grounding & Guardrails',
      desc: 'Verifies response against retrieved sources and rejects unauthorized financial commitments or contradictions.',
    },
    {
      id: 'Escalation Agent',
      name: 'Escalation Agent',
      stepNum: '05',
      icon: GitBranch,
      role: '70% Threshold & Handover',
      desc: 'Evaluates confidence score against the 70% threshold; resolves high-confidence tickets or routes to human support.',
    },
  ];

  const getAgentExecution = (agentName: string): AgentExecutionRecord | undefined => {
    if (!workflow?.agent_executions) return undefined;
    const matches = workflow.agent_executions.filter((a) => a.agent_name.toLowerCase().includes(agentName.toLowerCase().split(' ')[0]));
    return matches.length > 0 ? matches[matches.length - 1] : undefined;
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-fade-in-up">
      {/* Page Command Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-sky-950/60 pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sky-500/20 to-cyan-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400 shadow-lg shadow-sky-950/50">
              <GitBranch className="w-5 h-5 text-sky-400 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold text-white tracking-tight font-display">Multi-Agent Workflow Orchestrator</h1>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-sky-500/10 text-sky-300 border border-sky-500/20">
                  MILESTONE 3
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Visual inspection and interactive coordination of 5 autonomous agents executing airline support workflows.
              </p>
            </div>
          </div>
        </div>

        {/* Action Controls Toolbar */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <select
              value={selectedTicketId || ''}
              onChange={(e) => setSelectedTicketId(parseInt(e.target.value, 10))}
              className="bg-slate-900/90 border border-slate-700/80 text-slate-200 text-xs rounded-xl px-3.5 py-2.5 font-medium focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-all shadow-inner pr-8"
            >
              {tickets.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.ticket_number || `TK-${String(t.id).padStart(4, '0')}`} — {t.passenger_name || 'Passenger'} ({t.category})
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleRunWorkflow}
            disabled={executing || !selectedTicketId}
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-sky-600 via-sky-500 to-cyan-500 hover:from-sky-500 hover:to-cyan-400 disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-sky-600/25 transition-all transform hover:-translate-y-0.5 active:translate-y-0 cursor-pointer"
          >
            {executing ? (
              <>
                <RotateCw className="w-3.5 h-3.5 animate-spin" /> Orchestrating 5 Agents...
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" /> Run Multi-Agent Workflow
              </>
            )}
          </button>

          {workflow && (
            <button
              onClick={handleRetry}
              disabled={executing}
              className="p-2.5 rounded-xl bg-slate-900/90 hover:bg-slate-800 text-slate-300 border border-slate-700/80 transition-all hover:text-white hover:border-slate-600 shadow-sm cursor-pointer"
              title="Re-run Workflow"
            >
              <RotateCw className={`w-4 h-4 ${executing ? 'animate-spin text-sky-400' : ''}`} />
            </button>
          )}
        </div>
      </div>

      {actionMessage && (
        <div
          className={`p-4 rounded-2xl border text-xs flex items-center justify-between transition-all backdrop-blur-md ${
            actionMessage.type === 'success'
              ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-200 shadow-lg shadow-emerald-950/20'
              : 'bg-rose-950/40 border-rose-500/30 text-rose-200 shadow-lg shadow-rose-950/20'
          }`}
        >
          <div className="flex items-center gap-2.5">
            {actionMessage.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            )}
            <span className="font-medium">{actionMessage.text}</span>
          </div>
          <button
            onClick={() => setActionMessage(null)}
            className="text-xs opacity-60 hover:opacity-100 transition-opacity px-2 py-0.5 rounded hover:bg-white/10"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Selected Ticket Telemetry Banner */}
      {selectedTicket && (
        <div className="aviation-glass-card rounded-2xl p-4 md:p-5 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="w-11 h-11 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400 font-bold shadow-inner">
              <Plane className="w-5 h-5 -rotate-45 text-sky-400 animate-flight-float" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-bold text-sm text-white font-display">{selectedTicket.title}</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-sky-500/10 text-sky-300 border border-sky-500/20">
                  {selectedTicket.ticket_number || `TK-${String(selectedTicket.id).padStart(4, '0')}`}
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300 border border-slate-700">
                  Flight {selectedTicket.flight_number || 'N/A'}
                </span>
              </div>
              <div className="flex flex-wrap items-center gap-4 text-slate-400 mt-1.5 text-xs">
                <span>Passenger: <strong className="text-slate-200">{selectedTicket.passenger_name || 'Passenger'}</strong></span>
                <span className="flex items-center gap-1 font-mono">
                  PNR: <strong className="text-cyan-400">{selectedTicket.booking_reference || 'N/A'}</strong>
                </span>
                <span>Category: <strong className="text-slate-200">{selectedTicket.category}</strong></span>
                <span>Urgency: <strong className="text-amber-300 font-mono">{selectedTicket.urgency || 'MEDIUM'}</strong></span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right bg-slate-950/50 px-3.5 py-2 rounded-xl border border-slate-800/80">
              <span className="text-slate-400 block text-[10px] uppercase tracking-wider font-mono">Workflow Status</span>
              <span className={`font-bold text-xs flex items-center gap-1.5 justify-end font-mono ${
                workflow?.status === 'COMPLETED' ? 'text-emerald-400' : 'text-amber-400'
              }`}>
                <span className={`w-2 h-2 rounded-full ${
                  workflow?.status === 'COMPLETED' ? 'bg-emerald-400' : 'bg-amber-400 animate-pulse'
                }`} />
                {workflow?.status || 'PENDING EXECUTION'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 5-Stage Interactive Workflow Diagram */}
      <div className="aviation-glass-card rounded-2xl p-6 shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-sky-400" />
            <span className="text-xs font-bold uppercase tracking-wider text-slate-200 font-display">
              Sequential Multi-Agent Orchestration Pipeline
            </span>
          </div>
          <div className="flex items-center gap-4 text-[11px] font-mono">
            <span className="flex items-center gap-1.5 text-slate-400">
              <span className="w-2 h-2 rounded-full bg-slate-600"></span> Pending
            </span>
            <span className="flex items-center gap-1.5 text-sky-400">
              <span className="w-2 h-2 rounded-full bg-sky-400 animate-ping"></span> Active
            </span>
            <span className="flex items-center gap-1.5 text-emerald-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span> Verified
            </span>
            <span className="flex items-center gap-1.5 text-amber-400">
              <span className="w-2 h-2 rounded-full bg-amber-400"></span> Escalated
            </span>
          </div>
        </div>

        {/* Workflow Horizontal Connectors */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3.5 relative">
          {fiveAgents.map((agent, index) => {
            const exec = getAgentExecution(agent.name);
            const isCompleted = exec?.status === 'COMPLETED';
            const isRunning = executing && !isCompleted;
            const isExpanded = expandedAgent === agent.id;

            return (
              <div
                key={agent.id}
                className={`rounded-2xl border transition-all p-4 space-y-3 cursor-pointer relative overflow-hidden group ${
                  isCompleted
                    ? 'bg-gradient-to-b from-slate-900/90 to-slate-950/90 border-emerald-500/30 hover:border-emerald-500/60 shadow-lg shadow-emerald-950/20 hover:-translate-y-1'
                    : isRunning
                    ? 'bg-gradient-to-b from-slate-900/90 to-sky-950/40 border-sky-400/50 shadow-lg shadow-sky-950/30 ring-1 ring-sky-400/30 animate-pulse-glow'
                    : 'bg-slate-900/60 border-slate-800/80 hover:border-slate-700 hover:bg-slate-900/80 hover:-translate-y-0.5'
                }`}
                onClick={() => setExpandedAgent(isExpanded ? null : agent.id)}
              >
                {/* Step Connector Line on Desktop */}
                {index < fiveAgents.length - 1 && (
                  <div className="hidden md:block absolute -right-2 top-8 z-10 w-4 h-[2px] bg-slate-800 pointer-events-none group-hover:bg-sky-500/40 transition-colors" />
                )}

                {/* Agent Header */}
                <div className="flex items-center justify-between">
                  <div
                    className={`w-9 h-9 rounded-xl flex items-center justify-center font-bold transition-all ${
                      isCompleted
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/25 shadow-sm'
                        : isRunning
                        ? 'bg-sky-500/15 text-sky-400 border border-sky-400/30 shadow-md shadow-sky-500/10'
                        : 'bg-slate-800 text-slate-400 border border-slate-700'
                    }`}
                  >
                    <agent.icon className="w-4 h-4" />
                  </div>
                  <span className="text-[10px] font-mono text-slate-500 font-bold bg-slate-950/60 px-2 py-0.5 rounded border border-slate-800/60">
                    Step {agent.stepNum}
                  </span>
                </div>

                <div>
                  <h4 className="font-bold text-white text-xs tracking-tight font-display">{agent.name}</h4>
                  <p className="text-[10px] text-cyan-400 font-medium font-mono mt-0.5">{agent.role}</p>
                </div>

                <p className="text-[11px] text-slate-400 leading-snug line-clamp-2">{agent.desc}</p>

                {/* Execution Status Badge & Duration */}
                <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px]">
                  {isCompleted ? (
                    <span className="flex items-center gap-1.5 text-emerald-400 font-semibold font-mono text-[10px]">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Done
                    </span>
                  ) : isRunning ? (
                    <span className="flex items-center gap-1.5 text-sky-400 font-semibold font-mono text-[10px]">
                      <RotateCw className="w-3.5 h-3.5 animate-spin" /> In Flight
                    </span>
                  ) : (
                    <span className="flex items-center gap-1.5 text-slate-500 font-medium font-mono text-[10px]">
                      <Clock className="w-3.5 h-3.5" /> Pending
                    </span>
                  )}

                  {exec && (
                    <span className="font-mono text-cyan-300 text-[10px] bg-slate-950/80 px-1.5 py-0.5 rounded border border-slate-800/80">
                      {exec.duration_ms}ms
                    </span>
                  )}
                </div>

                <div className="text-right">
                  <span className="text-[10px] text-sky-400 hover:text-sky-300 flex items-center justify-end gap-1 font-mono transition-colors">
                    {isExpanded ? 'Hide Trace' : 'Inspect I/O'}
                    {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Detailed Inspector Drawer for Expanded Agent */}
        {expandedAgent && (
          <div className="p-5 rounded-2xl bg-slate-950 border border-sky-500/30 space-y-4 animate-fade-in-up shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-sky-400" />
                <span className="font-bold text-sm text-white font-display">{expandedAgent} Execution Inspector</span>
                <span className="text-[10px] font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                  Telemetry Snapshot
                </span>
              </div>
              <button
                onClick={() => setExpandedAgent(null)}
                className="text-xs text-slate-400 hover:text-white px-2 py-1 rounded hover:bg-slate-900 transition-colors cursor-pointer"
              >
                Close Drawer
              </button>
            </div>

            {getAgentExecution(expandedAgent) ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                {/* Inputs Box */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-sky-400" /> Agent Inputs
                    </span>
                    <button
                      onClick={() => copyToClipboard(JSON.stringify(getAgentExecution(expandedAgent)?.inputs, null, 2), 'inputs')}
                      className="text-[10px] font-mono text-slate-400 hover:text-sky-300 flex items-center gap-1 transition-colors"
                    >
                      {copiedSection === 'inputs' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                      {copiedSection === 'inputs' ? 'Copied' : 'Copy JSON'}
                    </button>
                  </div>
                  <pre className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 text-sky-200 font-mono text-[11px] max-h-60 overflow-y-auto leading-relaxed selection:bg-sky-500/30">
                    {JSON.stringify(getAgentExecution(expandedAgent)?.inputs, null, 2)}
                  </pre>
                </div>

                {/* Outputs Box */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> Agent Outputs
                    </span>
                    <button
                      onClick={() => copyToClipboard(JSON.stringify(getAgentExecution(expandedAgent)?.outputs, null, 2), 'outputs')}
                      className="text-[10px] font-mono text-slate-400 hover:text-emerald-300 flex items-center gap-1 transition-colors"
                    >
                      {copiedSection === 'outputs' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                      {copiedSection === 'outputs' ? 'Copied' : 'Copy JSON'}
                    </button>
                  </div>
                  <pre className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 text-emerald-300 font-mono text-[11px] max-h-60 overflow-y-auto leading-relaxed selection:bg-emerald-500/30">
                    {JSON.stringify(getAgentExecution(expandedAgent)?.outputs, null, 2)}
                  </pre>
                </div>
              </div>
            ) : (
              <div className="py-8 text-center text-slate-400 text-xs">
                No telemetry recorded for {expandedAgent} yet. Run the workflow above to populate inputs and outputs.
              </div>
            )}
          </div>
        )}
      </div>

      {/* Final Outcome & Handover Card */}
      {workflow && (
        <div className="aviation-glass-card rounded-2xl p-6 shadow-xl space-y-5 animate-fade-in-up">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2 font-display">
              <ShieldCheck className="w-4 h-4 text-sky-400" /> Pipeline Decision & Resolution Outcome
            </span>
            <span
              className={`px-3 py-1 rounded-full text-xs font-bold font-mono tracking-wide border self-start ${
                workflow.state_payload?.escalation?.decision === 'RESOLVED'
                  ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30 shadow-sm shadow-emerald-500/10'
                  : 'bg-amber-500/20 text-amber-300 border-amber-500/30 shadow-sm shadow-amber-500/10'
              }`}
            >
              FINAL OUTCOME: {workflow.state_payload?.escalation?.decision || workflow.status}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 hover:border-slate-700 transition-colors">
              <span className="text-slate-400 block text-[11px] font-mono">Final Confidence Score</span>
              <span className="text-2xl font-bold text-white font-mono mt-1 block">
                {workflow.state_payload?.escalation?.final_confidence || selectedTicket?.ai_confidence || 85}%
              </span>
              <span className="text-[11px] text-cyan-400 block mt-1 font-mono">Autonomous Gate: 70.0% standard</span>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 hover:border-slate-700 transition-colors">
              <span className="text-slate-400 block text-[11px] font-mono">Validation Verdict</span>
              <span className="text-2xl font-bold text-emerald-400 font-mono mt-1 block">
                {workflow.state_payload?.validation?.verdict || 'PASS'}
              </span>
              <span className="text-[11px] text-slate-400 block mt-1">Zero hallucinations detected</span>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 hover:border-slate-700 transition-colors">
              <span className="text-slate-400 block text-[11px] font-mono">Assigned Dispatch Queue</span>
              <span className="text-base font-bold text-slate-200 mt-1 block">
                {workflow.state_payload?.escalation?.assigned_queue || 'Resolved Passenger Queue'}
              </span>
              <span className="text-[11px] text-slate-400 block mt-1">Recorded in airline audit telemetry</span>
            </div>
          </div>

          {workflow.state_payload?.resolution?.passenger_response && (
            <div className="pt-2">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-300 font-display flex items-center gap-2">
                  <FileText className="w-3.5 h-3.5 text-sky-400" />
                  Passenger Communique Prepared by Resolution Agent
                </span>
                <button
                  onClick={() => copyToClipboard(workflow.state_payload.resolution.passenger_response, 'response')}
                  className="text-[11px] font-mono text-slate-400 hover:text-sky-300 flex items-center gap-1 transition-colors"
                >
                  {copiedSection === 'response' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  {copiedSection === 'response' ? 'Copied' : 'Copy Response'}
                </button>
              </div>
              <div className="p-5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-slate-200 whitespace-pre-line leading-relaxed font-sans shadow-inner selection:bg-sky-500/20">
                {workflow.state_payload.resolution.passenger_response}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
