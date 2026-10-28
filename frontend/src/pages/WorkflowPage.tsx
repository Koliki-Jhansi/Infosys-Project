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
  Plane,
  BookOpen,
  Layers,
  Check,
  Copy,
  ExternalLink,
  Mail,
  AlertTriangle,
  Sliders
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
        setTickets(res.items || []);
        if (res.items && res.items.length > 0 && !selectedTicketId) {
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
      setActionMessage({ type: 'success', text: `Multi-agent workflow execution completed successfully.` });
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

  // The 6 Multi-Agent Stages
  const sixStages = [
    {
      id: 'Ticket Analysis Agent',
      name: 'Ticket Analysis Agent',
      stepNum: '01',
      icon: Search,
      role: 'Ticket & Entity Triage',
      desc: 'Analyzes the issue, extracts passenger details, flight numbers, PNR, and travel urgency.',
    },
    {
      id: 'RAG Knowledge Retrieval Agent',
      name: 'RAG Knowledge Retrieval Agent',
      stepNum: '02',
      icon: BookOpen,
      role: 'Airline RAG Search',
      desc: 'Retrieves relevant policy chunks, baggage rules, and compensation entitlements from knowledge base.',
    },
    {
      id: 'Priority and Criticality Analysis',
      name: 'Priority and Criticality Analysis',
      stepNum: '03',
      icon: Sliders,
      role: 'Severity & Impact',
      desc: 'Evaluates priority (P1-P4) and criticality (Critical/High/Med/Low) based on flight operations policies.',
    },
    {
      id: 'AI Solution Generation',
      name: 'AI Solution Generation',
      stepNum: '04',
      icon: Bot,
      role: 'Policy Synthesis',
      desc: 'Synthesizes grounded passenger-friendly solution with citations from retrieved knowledge sources.',
    },
    {
      id: 'Confidence Evaluation',
      name: 'Confidence Evaluation',
      stepNum: '05',
      icon: ShieldCheck,
      role: 'Confidence & Guardrails',
      desc: 'Evaluates evidence sufficiency, validates response integrity, and calculates actual AI confidence score.',
    },
    {
      id: 'Final Decision',
      name: 'Final Decision',
      stepNum: '06',
      icon: GitBranch,
      role: 'Confidence Decision Engine',
      desc: 'If confidence < 70%, raises Jira issue; if >= 70%, approves resolution and dispatches email.',
    },
  ];

  const getAgentExecution = (stageName: string): AgentExecutionRecord | undefined => {
    if (!workflow?.agent_executions) return undefined;
    const matches = workflow.agent_executions.filter((a) => {
      const name = a.agent_name.toLowerCase();
      if (stageName === 'Ticket Analysis Agent') return name.includes('diagnosis') || name.includes('ticket analysis');
      if (stageName === 'RAG Knowledge Retrieval Agent') return name.includes('retrieval');
      if (stageName === 'Priority and Criticality Analysis') return name.includes('priority');
      if (stageName === 'AI Solution Generation') return name.includes('resolution') || name.includes('solution');
      if (stageName === 'Confidence Evaluation') return name.includes('validation') || name.includes('confidence');
      if (stageName === 'Final Decision') return name.includes('escalation') || name.includes('decision');
      return false;
    });
    return matches.length > 0 ? matches[matches.length - 1] : undefined;
  };

  const statePayload = workflow?.state_payload || {};
  const retrievedSources = statePayload?.retrieval?.sources || [];
  const generatedSolution = selectedTicket?.final_response || statePayload?.resolution?.passenger_response;
  const confidenceScore = selectedTicket?.ai_confidence ?? statePayload?.final_confidence;
  const escalationData = statePayload?.escalation || {};
  const jiraData = escalationData?.jira || (selectedTicket?.jira_records && selectedTicket.jira_records[0]);
  const emailData = escalationData?.email_delivery;

  return (
    <div className="bg-[#FFFFFF] min-h-screen p-6 sm:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Multi-Agent Workflow</h1>
          <p className="text-sm text-slate-500 mt-1">
            Sequential orchestration of 6 autonomous agents with real-time execution telemetry
          </p>
        </div>

        {/* Ticket Selector & Run Trigger */}
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={selectedTicketId || ''}
            onChange={(e) => setSelectedTicketId(parseInt(e.target.value, 10))}
            className="text-xs rounded-lg px-3 py-2 border border-slate-300 focus:outline-none focus:ring-2 focus:ring-sky-500 bg-white text-slate-800"
          >
            {tickets.map((t) => (
              <option key={t.id} value={t.id}>
                {t.ticket_number || `TK-${String(t.id).padStart(4, '0')}`} — {t.title.slice(0, 30)}
              </option>
            ))}
          </select>

          <button
            onClick={handleRunWorkflow}
            disabled={executing || !selectedTicketId}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold text-white bg-sky-600 hover:bg-sky-700 disabled:opacity-50 transition-colors shadow-sm"
          >
            {executing ? (
              <>
                <RotateCw className="w-3.5 h-3.5 animate-spin" />
                <span>Running Workflow...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Run Multi-Agent Workflow</span>
              </>
            )}
          </button>
        </div>
      </div>

      {actionMessage && (
        <div
          className={`p-3.5 rounded-xl border text-xs flex items-center justify-between ${
            actionMessage.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-rose-50 border-rose-200 text-rose-800'
          }`}
        >
          <div className="flex items-center gap-2">
            {actionMessage.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            )}
            <span className="font-medium">{actionMessage.text}</span>
          </div>
          <button
            onClick={() => setActionMessage(null)}
            className="text-xs text-slate-500 hover:text-slate-800 px-2 py-0.5"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Selected Ticket Overview Card */}
      {selectedTicket && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-mono text-xs font-bold text-sky-700 bg-sky-50 px-2 py-0.5 rounded border border-sky-200">
                {selectedTicket.ticket_number || `TK-${String(selectedTicket.id).padStart(4, '0')}`}
              </span>
              <h2 className="text-base font-bold text-slate-900">{selectedTicket.title}</h2>
            </div>
            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500">
              <span>Passenger: <strong className="text-slate-800">{selectedTicket.passenger_name || 'Passenger'}</strong></span>
              <span>Category: <strong className="text-slate-800">{selectedTicket.category}</strong></span>
              <span>Urgency: <strong className="text-slate-800">{selectedTicket.urgency || 'Medium'}</strong></span>
              {selectedTicket.booking_reference && (
                <span>PNR: <strong className="font-mono text-sky-700">{selectedTicket.booking_reference}</strong></span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right">
              <span className="text-[11px] uppercase tracking-wider text-slate-400 font-medium">Status</span>
              <div className="text-xs font-bold text-slate-800 mt-0.5">
                {selectedTicket.status}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 6-Stage Multi-Agent Timeline */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 pb-4">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-sky-600" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Sequential 6-Stage Execution Timeline
            </h3>
          </div>
          <div className="flex items-center gap-4 text-[11px] font-mono">
            <span className="flex items-center gap-1.5 text-slate-500">
              <span className="w-2 h-2 rounded-full bg-slate-300"></span> Pending
            </span>
            <span className="flex items-center gap-1.5 text-sky-600 font-semibold">
              <span className="w-2 h-2 rounded-full bg-sky-500 animate-ping"></span> Running
            </span>
            <span className="flex items-center gap-1.5 text-emerald-600 font-semibold">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span> Completed
            </span>
            <span className="flex items-center gap-1.5 text-rose-600 font-semibold">
              <span className="w-2 h-2 rounded-full bg-rose-500"></span> Failed
            </span>
          </div>
        </div>

        {/* 6-Stage Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sixStages.map((stage, idx) => {
            const exec = getAgentExecution(stage.name);
            const isCompleted = exec?.status === 'COMPLETED';
            const isFailed = exec?.status === 'FAILED';
            const isRunning = executing && !isCompleted && !isFailed;
            const isExpanded = expandedAgent === stage.id;

            return (
              <div
                key={stage.id}
                onClick={() => setExpandedAgent(isExpanded ? null : stage.id)}
                className={`rounded-xl border p-4 space-y-3 cursor-pointer transition-all ${
                  isCompleted
                    ? 'bg-emerald-50/40 border-emerald-200 hover:border-emerald-300'
                    : isRunning
                    ? 'bg-sky-50/40 border-sky-300 ring-2 ring-sky-200'
                    : isFailed
                    ? 'bg-rose-50 border-rose-200'
                    : 'bg-slate-50/60 border-slate-200 opacity-60'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold ${
                      isCompleted
                        ? 'bg-emerald-100 text-emerald-700'
                        : isRunning
                        ? 'bg-sky-100 text-sky-700'
                        : isFailed
                        ? 'bg-rose-100 text-rose-700'
                        : 'bg-slate-200 text-slate-500'
                    }`}
                  >
                    <stage.icon className="w-4 h-4" />
                  </div>
                  <span className="text-[10px] font-mono text-slate-400 font-bold">
                    STEP {stage.stepNum}
                  </span>
                </div>

                <div>
                  <h4 className="font-bold text-slate-900 text-xs">{stage.name}</h4>
                  <p className="text-[10px] text-sky-700 font-medium font-mono mt-0.5">{stage.role}</p>
                </div>

                <p className="text-[11px] text-slate-500 leading-snug line-clamp-2">{stage.desc}</p>

                <div className="pt-2 border-t border-slate-200 flex items-center justify-between text-[11px]">
                  {isCompleted ? (
                    <span className="flex items-center gap-1.5 text-emerald-700 font-semibold font-mono text-[10px]">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Completed
                    </span>
                  ) : isRunning ? (
                    <span className="flex items-center gap-1.5 text-sky-700 font-semibold font-mono text-[10px] animate-pulse">
                      <RotateCw className="w-3.5 h-3.5 animate-spin" /> Running
                    </span>
                  ) : isFailed ? (
                    <span className="flex items-center gap-1.5 text-rose-700 font-semibold font-mono text-[10px]">
                      <AlertCircle className="w-3.5 h-3.5" /> Failed
                    </span>
                  ) : (
                    <span className="flex items-center gap-1.5 text-slate-400 font-medium font-mono text-[10px]">
                      <Clock className="w-3.5 h-3.5" /> Pending
                    </span>
                  )}

                  {exec?.duration_ms !== undefined && (
                    <span className="text-[10px] font-mono text-slate-400">
                      {exec.duration_ms} ms
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Decision Workflow & Execution Details */}
      {workflow && (
        <div className="space-y-6">
          {/* Decision Summary Banner */}
          <div
            className={`p-5 rounded-xl border ${
              confidenceScore !== undefined && confidenceScore >= 70
                ? 'bg-emerald-50 border-emerald-200'
                : 'bg-amber-50 border-amber-200'
            }`}
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs uppercase font-bold text-slate-600">Final Confidence:</span>
                  <span
                    className={`text-2xl font-extrabold ${
                      confidenceScore !== undefined && confidenceScore >= 70 ? 'text-emerald-700' : 'text-amber-700'
                    }`}
                  >
                    {confidenceScore !== undefined ? `${confidenceScore}%` : 'N/A'}
                  </span>
                  <span className="text-xs px-2 py-0.5 rounded bg-white border border-slate-300 text-slate-600 font-semibold">
                    Threshold: 70%
                  </span>
                </div>
                <div className="text-xs text-slate-700 mt-1">
                  <strong>Decision: </strong>
                  {confidenceScore !== undefined && confidenceScore < 70 ? (
                    <span className="text-amber-800 font-semibold">
                      Below 70% threshold &bull; Escalated to Jira Cloud
                    </span>
                  ) : (
                    <span className="text-emerald-800 font-semibold">
                      70% or higher &bull; AI Resolution Approved
                    </span>
                  )}
                </div>
                {escalationData?.decision_summary && (
                  <p className="text-[11px] text-slate-600 mt-1">{escalationData.decision_summary}</p>
                )}
              </div>

              {/* Status details: Jira / Email */}
              <div className="flex flex-col items-end gap-2">
                {jiraData && (
                  <div className="bg-white p-3 rounded-lg border border-amber-200 text-right shadow-sm">
                    <span className="text-[10px] text-slate-400 block">Jira Ticket:</span>
                    <span className="font-mono font-bold text-indigo-700 text-sm">
                      {jiraData.jira_key || jiraData.key}
                    </span>
                    {jiraData.jira_url && (
                      <a
                        href={jiraData.jira_url}
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

                {emailData && (
                  <div className="bg-white p-3 rounded-lg border border-emerald-200 text-right shadow-sm">
                    <div className="flex items-center justify-end gap-1 text-[11px] text-slate-500">
                      <Mail className="w-3.5 h-3.5 text-emerald-600" />
                      <span>Email Delivery:</span>
                    </div>
                    <span className="text-xs font-semibold text-emerald-700 block mt-0.5">
                      {emailData.status}
                    </span>
                    <p className="text-[10px] text-slate-500 max-w-xs">{emailData.message}</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Generated Solution */}
          {generatedSolution && (
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                  <Bot className="w-3.5 h-3.5 text-sky-600" />
                  Generated Grounded Solution
                </h4>
                <button
                  onClick={() => copyToClipboard(generatedSolution, 'solution')}
                  className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-600 hover:text-slate-900"
                >
                  {copiedSection === 'solution' ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedSection === 'solution' ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
              <div className="bg-slate-50 rounded-lg p-4 text-xs text-slate-800 font-sans whitespace-pre-wrap leading-relaxed border border-slate-200">
                {generatedSolution}
              </div>
            </div>
          )}

          {/* Retrieved Knowledge Sources */}
          {retrievedSources.length > 0 && (
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                <BookOpen className="w-3.5 h-3.5 text-sky-600" />
                Retrieved Knowledge Sources ({retrievedSources.length})
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {retrievedSources.map((src: any, idx: number) => (
                  <div key={idx} className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-900">
                        {src.document_title || `Document #${src.chunk_id || idx + 1}`}
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
      )}
    </div>
  );
};

export default WorkflowPage;
