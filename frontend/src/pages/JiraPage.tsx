import React, { useEffect, useState } from 'react';
import { jiraApi, ticketsApi } from '../services/api';
import { JiraRecord, Ticket, JiraProject, JiraIssue, JiraTransition, JiraComment, JiraStatus } from '../types';
import { useAuth } from '../features/auth/AuthContext';
import {
  Layers,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  RefreshCw,
  PlusCircle,
  Send,
  ShieldCheck,
  Server,
  Link as LinkIcon,
  Check,
  Copy,
  Search,
  Filter,
  Sliders,
  ChevronLeft,
  ChevronRight,
  Clock,
  User,
  MessageSquare,
  Edit3,
  X,
  ArrowRight,
  AlertTriangle,
  FileCode,
  Tag,
  CheckSquare
} from 'lucide-react';

export const JiraPage: React.FC = () => {
  const { isSupport } = useAuth();

  // Jira Status & Connection
  const [statusData, setStatusData] = useState<JiraStatus | null>(null);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<any | null>(null);

  // Projects
  const [projects, setProjects] = useState<JiraProject[]>([]);
  const [selectedProjectKey, setSelectedProjectKey] = useState<string>('All');

  // Issues & Pagination
  const [issues, setIssues] = useState<JiraIssue[]>([]);
  const [totalIssues, setTotalIssues] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [pageSize] = useState(8);
  const [loadingIssues, setLoadingIssues] = useState(true);

  // Filters
  const [searchKeyword, setSearchKeyword] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [priorityFilter, setPriorityFilter] = useState('All');
  const [jqlMode, setJqlMode] = useState(false);
  const [jqlQuery, setJqlQuery] = useState('');

  // Selected Issue Detail Drawer
  const [selectedIssue, setSelectedIssue] = useState<JiraIssue | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [editingDetail, setEditingDetail] = useState(false);
  const [editSummary, setEditSummary] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [savingEdit, setSavingEdit] = useState(false);

  // Transitions & Comments
  const [transitions, setTransitions] = useState<JiraTransition[]>([]);
  const [selectedTransitionId, setSelectedTransitionId] = useState('');
  const [transitioning, setTransitioning] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [submittingComment, setSubmittingComment] = useState(false);

  // Create Issue Modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [createProject, setCreateProject] = useState('AERO');
  const [createType, setCreateType] = useState('Task');
  const [createPriority, setCreatePriority] = useState('High');
  const [createSummary, setCreateSummary] = useState('');
  const [createDescription, setCreateDescription] = useState('');
  const [createAssignee, setCreateAssignee] = useState('');
  const [creating, setCreating] = useState(false);

  // Manual Ticket Dispatcher State
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [selectedTicketId, setSelectedTicketId] = useState('');
  const [syncingTicket, setSyncingTicket] = useState(false);
  const [syncResult, setSyncResult] = useState<any | null>(null);
  const [syncError, setSyncError] = useState('');

  // Notification Toast
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const loadStatus = async () => {
    try {
      const data = await jiraApi.getStatus();
      setStatusData(data);
    } catch (err) {
      console.error('Failed to load Jira status', err);
    }
  };

  const loadProjects = async () => {
    try {
      const projs = await jiraApi.getProjects();
      setProjects(projs);
      if (projs.length > 0 && selectedProjectKey === 'All') {
        setCreateProject(projs[0].key);
      }
    } catch (err) {
      console.error('Failed to load Jira projects', err);
    }
  };

  const loadIssues = async (pageNum = 1) => {
    try {
      setLoadingIssues(true);
      const params: any = {
        page: pageNum,
        size: pageSize
      };

      if (jqlMode && jqlQuery.trim()) {
        params.jql = jqlQuery.trim();
      } else {
        if (selectedProjectKey !== 'All') params.project_key = selectedProjectKey;
        if (statusFilter !== 'All') params.status = statusFilter;
        if (priorityFilter !== 'All') params.priority = priorityFilter;
        if (searchKeyword.trim()) params.search = searchKeyword.trim();
      }

      const res = await jiraApi.getIssues(params);
      setIssues(res.items);
      setTotalIssues(res.total);
      setPage(res.page);
      setTotalPages(res.pages);
    } catch (err) {
      console.error('Failed to load Jira issues', err);
    } finally {
      setLoadingIssues(false);
    }
  };

  const loadTickets = async () => {
    try {
      const data = await ticketsApi.list({ size: 50 });
      setTickets(data.items);
    } catch (err) {
      console.error('Failed to load tickets', err);
    }
  };

  useEffect(() => {
    loadStatus();
    loadProjects();
    loadTickets();
  }, []);

  useEffect(() => {
    loadIssues(1);
  }, [selectedProjectKey, statusFilter, priorityFilter]);

  const handleTestConnection = async () => {
    try {
      setTesting(true);
      setTestResult(null);
      const res = await jiraApi.testConnection();
      setTestResult(res);
      await loadStatus();
      await loadProjects();
    } catch (err: any) {
      setTestResult({
        success: false,
        mode: 'REAL_CLOUD',
        message: err.response?.data?.detail || 'Jira connection test failed.'
      });
    } finally {
      setTesting(false);
    }
  };

  const handleSelectIssue = async (issueKey: string) => {
    try {
      setLoadingDetail(true);
      const issue = await jiraApi.getIssue(issueKey);
      setSelectedIssue(issue);
      setEditSummary(issue.summary);
      setEditDescription(issue.description);
      setEditingDetail(false);

      const trans = await jiraApi.getTransitions(issueKey);
      setTransitions(trans);
      if (trans.length > 0) {
        setSelectedTransitionId(trans[0].id);
      }
    } catch (err) {
      console.error('Failed to load issue details', err);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleSaveEdit = async () => {
    if (!selectedIssue) return;
    try {
      setSavingEdit(true);
      const updated = await jiraApi.updateIssue(selectedIssue.key, {
        summary: editSummary.trim(),
        description: editDescription.trim()
      });
      setSelectedIssue(updated);
      setEditingDetail(false);
      setNotification({ type: 'success', text: `Issue ${selectedIssue.key} updated successfully.` });
      await loadIssues(page);
    } catch (err: any) {
      setNotification({ type: 'error', text: err.response?.data?.detail || 'Failed to update issue.' });
    } finally {
      setSavingEdit(false);
    }
  };

  const handleTransition = async () => {
    if (!selectedIssue || !selectedTransitionId) return;
    try {
      setTransitioning(true);
      const updated = await jiraApi.transitionIssue(selectedIssue.key, {
        transition_id: selectedTransitionId
      });
      setSelectedIssue(updated);
      const trans = await jiraApi.getTransitions(selectedIssue.key);
      setTransitions(trans);
      setNotification({ type: 'success', text: `Issue ${selectedIssue.key} transitioned to '${updated.status}'.` });
      await loadIssues(page);
    } catch (err: any) {
      setNotification({ type: 'error', text: err.response?.data?.detail || 'Failed to transition issue.' });
    } finally {
      setTransitioning(false);
    }
  };

  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedIssue || !newComment.trim()) return;
    try {
      setSubmittingComment(true);
      const comm = await jiraApi.addComment(selectedIssue.key, newComment.trim());
      setSelectedIssue({
        ...selectedIssue,
        comments: [...selectedIssue.comments, comm]
      });
      setNewComment('');
      setNotification({ type: 'success', text: 'Comment published to Jira Cloud.' });
    } catch (err: any) {
      setNotification({ type: 'error', text: err.response?.data?.detail || 'Failed to post comment.' });
    } finally {
      setSubmittingComment(false);
    }
  };

  const handleCreateIssue = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createSummary.trim()) return;
    try {
      setCreating(true);
      const newIss = await jiraApi.createIssue({
        project_key: createProject,
        issue_type: createType,
        priority: createPriority,
        summary: createSummary.trim(),
        description: createDescription.trim(),
        assignee: createAssignee.trim() || undefined
      });
      setCreateModalOpen(false);
      setCreateSummary('');
      setCreateDescription('');
      setNotification({ type: 'success', text: `Created Jira issue ${newIss.key} successfully.` });
      await loadIssues(1);
    } catch (err: any) {
      setNotification({ type: 'error', text: err.response?.data?.detail || 'Failed to create Jira issue.' });
    } finally {
      setCreating(false);
    }
  };

  const handleManualSync = async (e: React.FormEvent) => {
    e.preventDefault();
    const tid = parseInt(selectedTicketId);
    if (!tid) return;
    setSyncError('');
    setSyncingTicket(true);
    setSyncResult(null);

    try {
      const res = await jiraApi.createTicketIssue(tid);
      setSyncResult(res);
      setNotification({ type: 'success', text: `Ticket #${tid} synced to Jira: ${res.jira_key}` });
      await loadTickets();
      await loadIssues(1);
    } catch (err: any) {
      setSyncError(err.response?.data?.detail || 'Failed to sync ticket to Jira.');
    } finally {
      setSyncingTicket(false);
    }
  };

  // Status badge style helper
  const getStatusBadge = (statusStr: string) => {
    const s = statusStr.toLowerCase();
    if (s.includes('done') || s.includes('resolved') || s.includes('closed')) {
      return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
    }
    if (s.includes('progress') || s.includes('review') || s.includes('investigating')) {
      return 'bg-sky-500/20 text-sky-300 border-sky-500/30';
    }
    return 'bg-amber-500/20 text-amber-300 border-amber-500/30';
  };

  const getPriorityBadge = (prioStr: string) => {
    const p = prioStr.toLowerCase();
    if (p.includes('highest') || p.includes('critical')) return 'text-rose-400 bg-rose-500/10 border-rose-500/20';
    if (p.includes('high')) return 'text-orange-400 bg-orange-500/10 border-orange-500/20';
    if (p.includes('medium')) return 'text-sky-400 bg-sky-500/10 border-sky-500/20';
    return 'text-slate-400 bg-slate-800 border-slate-700';
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16 animate-fade-in-up">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-sky-950/60 pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/20 to-sky-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400 shadow-lg shadow-blue-950/50">
              <Layers className="w-5 h-5 text-blue-400 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold tracking-tight text-white font-display">
                  Jira Cloud Command & Issue Dashboard
                </h1>
                <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold border ${
                  statusData?.mode === 'REAL_CLOUD'
                    ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                    : 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                }`}>
                  {statusData?.mode || 'SIMULATED'}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Bidirectional Jira Cloud REST API synchronization, project issue management, and ticket integration.
              </p>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {isSupport && (
            <button
              onClick={() => setCreateModalOpen(true)}
              className="px-4 py-2.5 bg-gradient-to-r from-sky-600 via-sky-500 to-cyan-500 hover:from-sky-500 hover:to-cyan-400 text-white rounded-xl text-xs font-semibold shadow-lg shadow-sky-600/20 transition-all flex items-center gap-2 cursor-pointer transform hover:-translate-y-0.5"
            >
              <PlusCircle className="w-4 h-4" />
              Create Jira Issue
            </button>
          )}
          <button
            onClick={handleTestConnection}
            disabled={testing}
            className="px-4 py-2.5 bg-slate-900/90 hover:bg-slate-800 border border-slate-700/80 text-slate-200 rounded-xl text-xs font-semibold transition-all flex items-center gap-2 disabled:opacity-50 cursor-pointer"
          >
            {testing ? <RefreshCw className="w-4 h-4 animate-spin text-sky-400" /> : <Server className="w-4 h-4 text-sky-400" />}
            Test Connectivity
          </button>
        </div>
      </div>

      {!isSupport && (
        <div className="p-4 rounded-2xl bg-sky-950/40 border border-sky-500/25 text-xs text-sky-200 flex items-start gap-3 shadow-md">
          <AlertTriangle className="w-4 h-4 text-sky-400 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-semibold text-white">Passenger Read-Only View</span>
            <p className="text-[11px] text-slate-300">
              You are currently viewing Jira Cloud synchronization in passenger read-only mode. Creating issues, transitioning statuses, and testing connectivity require Airline Support Agent or Admin privileges.
            </p>
          </div>
        </div>
      )}

      {notification && (

        <div
          className={`p-4 rounded-2xl border text-xs flex items-center justify-between shadow-lg transition-all ${
            notification.type === 'success'
              ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-200 shadow-emerald-950/20'
              : 'bg-rose-950/40 border-rose-500/30 text-rose-200 shadow-rose-950/20'
          }`}
        >
          <div className="flex items-center gap-2">
            {notification.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            )}
            <span className="font-medium">{notification.text}</span>
          </div>
          <button
            onClick={() => setNotification(null)}
            className="text-slate-400 hover:text-white px-2 py-0.5 rounded hover:bg-white/10"
          >
            &times;
          </button>
        </div>
      )}

      {/* Connectivity Test Result Banner */}
      {testResult && (
        <div
          className={`p-4 rounded-2xl border text-xs flex items-start gap-3 animate-fade-in-up ${
            testResult.success
              ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-200 shadow-lg shadow-emerald-950/20'
              : 'bg-rose-950/40 border-rose-500/30 text-rose-200 shadow-lg shadow-rose-950/20'
          }`}
        >
          {testResult.success ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
          ) : (
            <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          )}
          <div className="space-y-0.5 flex-1">
            <span className="font-bold text-sm block font-display">
              {testResult.success ? 'Jira Cloud Connectivity Verified' : 'Jira Connectivity Diagnostic'}
            </span>
            <p className="leading-relaxed">{testResult.message}</p>
            {testResult.user && (
              <span className="text-[11px] font-mono text-cyan-300 block pt-1">
                Authenticated Principal: {testResult.user} ({testResult.email}) • Accessible Projects: {testResult.project_count || 3}
              </span>
            )}
          </div>
          <button onClick={() => setTestResult(null)} className="text-slate-400 hover:text-white text-base">
            &times;
          </button>
        </div>
      )}

      {/* Quick Telemetry & Integration Parameters HUD */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="aviation-glass-card rounded-2xl p-4 shadow-sm space-y-1">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider font-mono">Integration State</span>
          <div className="flex items-center justify-between">
            <span className="text-xl font-bold text-white font-mono">{statusData?.mode || 'SIMULATED'}</span>
            <span className={`w-2.5 h-2.5 rounded-full ${statusData?.mode === 'REAL_CLOUD' ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
          </div>
          <span className="text-[11px] text-slate-400 font-mono truncate block">{statusData?.base_url}</span>
        </div>

        <div className="aviation-glass-card rounded-2xl p-4 shadow-sm space-y-1">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider font-mono">Accessible Projects</span>
          <div className="flex items-center justify-between">
            <span className="text-xl font-bold text-cyan-400 font-mono">{projects.length} Active</span>
            <span className="p-1.5 rounded-lg bg-sky-500/10 text-sky-400 font-mono text-[10px]">Cloud REST v3</span>
          </div>
          <span className="text-[11px] text-slate-400 font-mono">Default: {statusData?.project_key || 'IT'}</span>
        </div>

        <div className="aviation-glass-card rounded-2xl p-4 shadow-sm space-y-1">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider font-mono">Total Issues Tracked</span>
          <div className="flex items-center justify-between">
            <span className="text-xl font-bold text-white font-mono">{totalIssues}</span>
            <span className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 font-mono text-[10px]">Synced</span>
          </div>
          <span className="text-[11px] text-slate-400 font-mono">Deduplication: SHA-256</span>
        </div>

        <div className="aviation-glass-card rounded-2xl p-4 shadow-sm space-y-1">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider font-mono">Target Issue Type</span>
          <div className="flex items-center justify-between">
            <span className="text-xl font-bold text-amber-300 font-mono">{statusData?.default_issue_type || 'Task'}</span>
            <CheckSquare className="w-4 h-4 text-amber-400" />
          </div>
          <span className="text-[11px] text-slate-400 font-mono">Account: {statusData?.configured_email || 'Configured'}</span>
        </div>
      </div>

      {/* Controls & Search Filter Toolbar */}
      <div className="aviation-glass-card rounded-2xl p-5 shadow-sm space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          {/* Project Selector Pills */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="text-slate-400 font-mono text-[11px]">Project:</span>
            <button
              onClick={() => setSelectedProjectKey('All')}
              className={`px-3 py-1.5 rounded-xl font-semibold transition-all cursor-pointer ${
                selectedProjectKey === 'All'
                  ? 'bg-gradient-to-r from-sky-600 to-cyan-500 text-white shadow-md shadow-sky-600/20'
                  : 'bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800'
              }`}
            >
              All Projects
            </button>
            {projects.map((p) => (
              <button
                key={p.key}
                onClick={() => setSelectedProjectKey(p.key)}
                className={`px-3 py-1.5 rounded-xl font-semibold transition-all cursor-pointer font-mono text-xs ${
                  selectedProjectKey === p.key
                    ? 'bg-gradient-to-r from-sky-600 to-cyan-500 text-white shadow-md shadow-sky-600/20'
                    : 'bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800'
                }`}
              >
                {p.key} ({p.name})
              </button>
            ))}
          </div>

          {/* JQL Mode Switcher */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setJqlMode(!jqlMode)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
                jqlMode
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                  : 'bg-slate-900 border border-slate-700/80 text-slate-400 hover:text-white'
              }`}
            >
              <FileCode className="w-3.5 h-3.5" />
              {jqlMode ? 'JQL Query Mode (Active)' : 'Switch to JQL'}
            </button>
          </div>
        </div>

        {/* Search & Filters */}
        {jqlMode ? (
          <div className="flex gap-2.5 pt-1">
            <input
              type="text"
              value={jqlQuery}
              onChange={(e) => setJqlQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && loadIssues(1)}
              placeholder="e.g. project = AERO AND status = 'In Progress' ORDER BY created DESC"
              className="flex-1 bg-slate-900/90 border border-slate-700/80 rounded-xl px-4 py-2 text-xs text-white placeholder-slate-400 font-mono focus:outline-none focus:border-sky-500"
            />
            <button
              onClick={() => loadIssues(1)}
              className="px-5 py-2 bg-gradient-to-r from-sky-600 to-cyan-500 text-white rounded-xl text-xs font-semibold shadow hover:opacity-95 cursor-pointer"
            >
              Execute JQL
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && loadIssues(1)}
                placeholder="Search issue key, summary, description..."
                className="w-full bg-slate-900/90 border border-slate-700/80 rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-sky-500"
              />
            </div>

            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-mono text-[11px] shrink-0">Status:</span>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
              >
                <option value="All">All Statuses</option>
                <option value="To Do">To Do</option>
                <option value="In Progress">In Progress</option>
                <option value="In Review">In Review</option>
                <option value="Done">Done</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-mono text-[11px] shrink-0">Priority:</span>
              <select
                value={priorityFilter}
                onChange={(e) => setPriorityFilter(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
              >
                <option value="All">All Priorities</option>
                <option value="Highest">Highest</option>
                <option value="High">High</option>
                <option value="Medium">Medium</option>
                <option value="Low">Low</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Main Issues Directory Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Issues List Table (2 Columns wide) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="aviation-glass-card rounded-2xl shadow-xl overflow-hidden">
            <div className="p-4 border-b border-slate-800/80 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckSquare className="w-4 h-4 text-sky-400" />
                <h3 className="font-bold text-white text-xs font-display uppercase tracking-wider">
                  Jira Cloud Issues Directory ({totalIssues})
                </h3>
              </div>
              <span className="text-[11px] text-slate-400 font-mono">Click issue row to inspect details & transitions</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/80 text-[10px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-800 font-mono">
                  <tr>
                    <th className="py-3 px-4">Key</th>
                    <th className="py-3 px-4">Summary</th>
                    <th className="py-3 px-4">Priority</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Assignee</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {loadingIssues ? (
                    <tr>
                      <td colSpan={6} className="py-12 text-center text-slate-400">
                        <RefreshCw className="w-6 h-6 text-sky-400 animate-spin mx-auto mb-2" />
                        Querying Jira Cloud REST API...
                      </td>
                    </tr>
                  ) : issues.length > 0 ? (
                    issues.map((iss) => (
                      <tr
                        key={iss.key}
                        onClick={() => handleSelectIssue(iss.key)}
                        className={`hover:bg-slate-800/50 transition-colors cursor-pointer ${
                          selectedIssue?.key === iss.key ? 'bg-sky-500/10 border-l-2 border-l-sky-400' : ''
                        }`}
                      >
                        <td className="py-3.5 px-4 font-mono font-bold text-cyan-400 whitespace-nowrap">
                          {iss.key}
                        </td>
                        <td className="py-3.5 px-4">
                          <span className="font-semibold text-white block line-clamp-1">{iss.summary}</span>
                          <span className="text-[10px] text-slate-400 font-mono mt-0.5 block">{iss.issue_type} • {iss.project_key}</span>
                        </td>
                        <td className="py-3.5 px-4 whitespace-nowrap">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold border font-mono ${getPriorityBadge(iss.priority)}`}>
                            {iss.priority}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 whitespace-nowrap">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold border font-mono ${getStatusBadge(iss.status)}`}>
                            {iss.status}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-slate-400 text-[11px] whitespace-nowrap">
                          {iss.assignee_name || 'Unassigned'}
                        </td>
                        <td className="py-3.5 px-4 text-right whitespace-nowrap">
                          <a
                            href={iss.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-cyan-400 border border-slate-700/80 inline-flex items-center gap-1 transition-colors text-[10px] font-mono"
                          >
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={6} className="py-12 text-center text-slate-400 text-xs">
                        No Jira issues match the current query criteria.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="p-3.5 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
              <span className="font-mono text-[11px]">
                Showing {issues.length} of {totalIssues} issues
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => loadIssues(Math.max(1, page - 1))}
                  disabled={page <= 1}
                  className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-700/80 text-slate-300 disabled:opacity-40 hover:bg-slate-800 cursor-pointer"
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                </button>
                <span className="font-mono text-white text-[11px]">Page {page} of {Math.max(1, totalPages)}</span>
                <button
                  onClick={() => loadIssues(Math.min(totalPages, page + 1))}
                  disabled={page >= totalPages}
                  className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-700/80 text-slate-300 disabled:opacity-40 hover:bg-slate-800 cursor-pointer"
                >
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>

          {/* Manual Incident Ticket Dispatcher */}
          <div className="aviation-glass-card rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Send className="w-4 h-4 text-sky-400" />
                <h3 className="font-bold text-white text-xs font-display uppercase tracking-wider">
                  Manual Flight Incident Ticket Dispatcher
                </h3>
              </div>
              <span className="text-[11px] text-slate-400 font-mono">Sync supported tickets to Jira Cloud</span>
            </div>

            {syncError && (
              <div className="p-3 bg-rose-950/40 border border-rose-500/30 text-rose-300 text-xs rounded-xl">
                {syncError}
              </div>
            )}

            {syncResult && (
              <div className="p-3.5 bg-emerald-950/40 border border-emerald-500/30 text-emerald-200 text-xs rounded-xl space-y-1">
                <div className="flex items-center gap-2 font-bold font-display">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  Jira Issue Synchronized: {syncResult.jira_key}
                </div>
                <a
                  href={syncResult.jira_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-cyan-400 hover:underline flex items-center gap-1 font-mono text-[11px] pt-1"
                >
                  Inspect in Jira Cloud &rarr;
                </a>
              </div>
            )}

            <form onSubmit={handleManualSync} className="flex flex-col sm:flex-row gap-3 text-xs">
              <select
                value={selectedTicketId}
                onChange={(e) => setSelectedTicketId(e.target.value)}
                className="flex-1 bg-slate-900 border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-white focus:outline-none focus:border-sky-500 text-xs"
              >
                <option value="">-- Choose passenger incident ticket to dispatch --</option>
                {tickets.map((t) => (
                  <option key={t.id} value={t.id}>
                    #{t.id} - {t.title} ({t.category}) [{t.status}]
                  </option>
                ))}
              </select>

              <button
                type="submit"
                disabled={syncingTicket || !selectedTicketId}
                className="px-6 py-2.5 bg-gradient-to-r from-sky-600 via-sky-500 to-cyan-500 hover:from-sky-500 hover:to-cyan-400 text-white font-semibold rounded-xl shadow-lg shadow-sky-600/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50 cursor-pointer shrink-0"
              >
                {syncingTicket ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                Dispatch to Jira
              </button>
            </form>
          </div>
        </div>

        {/* Right Column: Detailed Issue Inspector & Transition Panel */}
        <div className="space-y-4">
          <div className="aviation-glass-card rounded-2xl p-5 shadow-xl space-y-4 sticky top-20">
            {selectedIssue ? (
              <div className="space-y-4 animate-fade-in-up">
                {/* Header */}
                <div className="flex items-start justify-between border-b border-slate-800 pb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-cyan-400 text-sm">{selectedIssue.key}</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border font-mono ${getStatusBadge(selectedIssue.status)}`}>
                        {selectedIssue.status}
                      </span>
                    </div>
                    <span className="text-[11px] text-slate-400 font-mono block mt-1">
                      Project: {selectedIssue.project_key} • {selectedIssue.issue_type}
                    </span>
                  </div>

                  <a
                    href={selectedIssue.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-cyan-400 border border-slate-700/80 transition-colors"
                    title="Open in Jira"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>

                {/* Summary & Description */}
                {editingDetail ? (
                  <div className="space-y-3">
                    <div>
                      <label className="block text-[10px] font-mono text-slate-400 mb-1">Summary</label>
                      <input
                        type="text"
                        value={editSummary}
                        onChange={(e) => setEditSummary(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] font-mono text-slate-400 mb-1">Description</label>
                      <textarea
                        rows={4}
                        value={editDescription}
                        onChange={(e) => setEditDescription(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-700/80 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-sky-500 font-sans leading-relaxed"
                      />
                    </div>
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={() => setEditingDetail(false)}
                        className="px-3 py-1.5 bg-slate-800 text-slate-300 rounded-xl text-xs"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={handleSaveEdit}
                        disabled={savingEdit}
                        className="px-3.5 py-1.5 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-xs font-semibold disabled:opacity-50"
                      >
                        {savingEdit ? 'Saving...' : 'Save Changes'}
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className="font-bold text-white text-sm font-display">{selectedIssue.summary}</h4>
                      {isSupport && (
                        <button
                          onClick={() => setEditingDetail(true)}
                          className="text-slate-400 hover:text-sky-300 p-1"
                          title="Edit Issue"
                        >
                          <Edit3 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                    <p className="text-xs text-slate-300 bg-slate-950/70 p-3.5 rounded-xl border border-slate-800/80 leading-relaxed font-sans whitespace-pre-wrap max-h-48 overflow-y-auto">
                      {selectedIssue.description || 'No description provided.'}
                    </p>
                  </div>
                )}

                {/* Workflow Transitions Action */}
                <div className="pt-2 border-t border-slate-800/80 space-y-2">
                  <span className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider block">
                    Workflow Status Transition
                  </span>
                  {transitions.length > 0 ? (
                    <div className="flex gap-2">
                      <select
                        value={selectedTransitionId}
                        onChange={(e) => setSelectedTransitionId(e.target.value)}
                        className="flex-1 bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500 font-mono"
                      >
                        {transitions.map((t) => (
                          <option key={t.id} value={t.id}>
                            {t.name} &rarr; {t.to_status}
                          </option>
                        ))}
                      </select>
                      <button
                        onClick={handleTransition}
                        disabled={transitioning}
                        className="px-3.5 py-2 bg-gradient-to-r from-sky-600 to-cyan-500 hover:from-sky-500 hover:to-cyan-400 text-white rounded-xl text-xs font-semibold shadow disabled:opacity-50 cursor-pointer shrink-0"
                      >
                        {transitioning ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : 'Transition'}
                      </button>
                    </div>
                  ) : (
                    <span className="text-[11px] text-slate-500 italic block">No further transitions available.</span>
                  )}
                </div>

                {/* Comments Thread */}
                <div className="pt-3 border-t border-slate-800/80 space-y-3">
                  <span className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider block flex items-center gap-1.5">
                    <MessageSquare className="w-3 h-3 text-sky-400" />
                    Jira Activity & Comments ({selectedIssue.comments?.length || 0})
                  </span>

                  <div className="space-y-2 max-h-44 overflow-y-auto pr-1">
                    {selectedIssue.comments && selectedIssue.comments.length > 0 ? (
                      selectedIssue.comments.map((c, i) => (
                        <div key={i} className="p-2.5 bg-slate-950/80 rounded-xl border border-slate-800 text-[11px] space-y-1">
                          <div className="flex items-center justify-between text-slate-400 font-mono text-[10px]">
                            <span className="font-bold text-slate-300">{c.author}</span>
                            <span>{new Date(c.created_at).toLocaleDateString()}</span>
                          </div>
                          <p className="text-slate-200 leading-relaxed">{c.body}</p>
                        </div>
                      ))
                    ) : (
                      <p className="text-slate-500 text-[11px] italic">No comments posted yet.</p>
                    )}
                  </div>

                  {/* Add Comment Input */}
                  <form onSubmit={handleAddComment} className="flex gap-2 pt-1">
                    <input
                      type="text"
                      value={newComment}
                      onChange={(e) => setNewComment(e.target.value)}
                      placeholder="Add comment..."
                      className="flex-1 bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-1.5 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-sky-500"
                    />
                    <button
                      type="submit"
                      disabled={submittingComment || !newComment.trim()}
                      className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-sky-400 font-semibold rounded-xl text-xs border border-slate-700 disabled:opacity-40 cursor-pointer"
                    >
                      {submittingComment ? <RefreshCw className="w-3 h-3 animate-spin" /> : 'Post'}
                    </button>
                  </form>
                </div>
              </div>
            ) : (
              <div className="py-16 text-center text-slate-500 space-y-2">
                <Layers className="w-8 h-8 text-slate-600 mx-auto" />
                <p className="text-xs text-slate-400">Select any Jira issue to inspect fields, trigger workflow transitions, or append comments.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Create Issue Modal */}
      {createModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="aviation-glass-card rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4 border border-sky-500/30 animate-fade-in-up">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-white text-base flex items-center gap-2 font-display">
                <PlusCircle className="w-4 h-4 text-sky-400" />
                Create Jira Cloud Issue
              </h3>
              <button
                onClick={() => setCreateModalOpen(false)}
                className="text-slate-400 hover:text-white text-lg px-2 py-1 rounded transition-colors cursor-pointer"
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleCreateIssue} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1 font-mono text-[11px]">Target Project</label>
                  <select
                    value={createProject}
                    onChange={(e) => setCreateProject(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-sky-500"
                  >
                    {projects.map((p) => (
                      <option key={p.key} value={p.key}>
                        {p.key} - {p.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1 font-mono text-[11px]">Issue Type</label>
                  <select
                    value={createType}
                    onChange={(e) => setCreateType(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-sky-500"
                  >
                    <option value="Task">Task</option>
                    <option value="Bug">Bug</option>
                    <option value="Story">Story</option>
                    <option value="Incident">Incident</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1 font-mono text-[11px]">Priority</label>
                  <select
                    value={createPriority}
                    onChange={(e) => setCreatePriority(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-sky-500"
                  >
                    <option value="Highest">Highest</option>
                    <option value="High">High</option>
                    <option value="Medium">Medium</option>
                    <option value="Low">Low</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1 font-mono text-[11px]">Assignee (Optional)</label>
                  <input
                    type="text"
                    value={createAssignee}
                    onChange={(e) => setCreateAssignee(e.target.value)}
                    placeholder="e.g. Sarah Connor"
                    className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-sky-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1 font-mono text-[11px]">Issue Summary</label>
                <input
                  type="text"
                  required
                  value={createSummary}
                  onChange={(e) => setCreateSummary(e.target.value)}
                  placeholder="e.g. Flight AA-902 turnaround baggage transfer sync failure"
                  className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-sky-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1 font-mono text-[11px]">Description</label>
                <textarea
                  required
                  rows={4}
                  value={createDescription}
                  onChange={(e) => setCreateDescription(e.target.value)}
                  placeholder="State detailed technical context, reproduction steps, or flight details..."
                  className="w-full bg-slate-900 border border-slate-700/80 rounded-xl p-3 text-white focus:outline-none focus:border-sky-500 leading-relaxed"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setCreateModalOpen(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-5 py-2 bg-gradient-to-r from-sky-600 to-cyan-500 hover:from-sky-500 hover:to-cyan-400 text-white font-semibold rounded-xl shadow-lg shadow-sky-600/20 disabled:opacity-50 cursor-pointer transition-all"
                >
                  {creating ? 'Creating in Jira...' : 'Create Issue'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
