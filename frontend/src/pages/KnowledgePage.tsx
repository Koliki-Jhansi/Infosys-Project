import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { knowledgeApi, ticketsApi } from '../services/api';
import { KnowledgeDocument, RetrievedSource, GroundedSolution, Ticket } from '../types';
import { useAuth } from '../features/auth/AuthContext';
import {
  BookOpen,
  Upload,
  Search,
  Filter,
  Trash2,
  RefreshCw,
  FileText,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  ExternalLink,
  Layers,
  Sparkles,
  ShieldCheck,
  Eye,
  ChevronRight,
  Database,
  Compass,
  FileCode,
  Terminal,
  Check,
  Copy,
  Plane
} from 'lucide-react';

const DOC_TYPES = ['All', 'Policy', 'Procedure', 'Guidance', 'Runbook', 'FAQ'];
const CATEGORIES = [
  'All',
  'Booking and Reservation',
  'Cancellation and Refund',
  'Flight Delay',
  'Flight Cancellation',
  'Baggage',
  'Check-in and Boarding',
  'Seat Selection',
  'Payment',
  'Special Assistance',
  'Other',
];

export const KnowledgePage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const { isSupport } = useAuth();

  const [activeTab, setActiveTab] = useState<'documents' | 'search' | 'troubleshoot'>('documents');
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [categoryFilter, setCategoryFilter] = useState('All');
  const [typeFilter, setTypeFilter] = useState('All');
  const [searchKeyword, setSearchKeyword] = useState('');

  // Upload modal state
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadDocType, setUploadDocType] = useState('Policy');
  const [uploadService, setUploadService] = useState('Flight Operations');
  const [uploadCategory, setUploadCategory] = useState('Baggage');
  const [uploadVersion, setUploadVersion] = useState('1.0');
  const [uploadOwner, setUploadOwner] = useState('Passenger Support & Compliance');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');

  // Document details view modal
  const [selectedDocDetails, setSelectedDocDetails] = useState<any | null>(null);

  // Interactive Search Tab state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<RetrievedSource[]>([]);
  const [searching, setSearching] = useState(false);

  // Ticket Troubleshooting RAG Tab state
  const [ticketIdInput, setTicketIdInput] = useState(searchParams.get('ticketId') || '');
  const [ticketsList, setTicketsList] = useState<Ticket[]>([]);
  const [groundedSolution, setGroundedSolution] = useState<GroundedSolution | null>(null);
  const [generatingSolution, setGeneratingSolution] = useState(false);
  const [solutionError, setSolutionError] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (categoryFilter !== 'All') params.category = categoryFilter;
      if (typeFilter !== 'All') params.doc_type = typeFilter;
      if (searchKeyword.trim()) params.search = searchKeyword.trim();

      const data = await knowledgeApi.listDocuments();
      setDocuments(data);
    } catch (err) {
      console.error('Failed to load documents', err);
    } finally {
      setLoading(false);
    }
  };

  const loadTickets = async () => {
    try {
      const data = await ticketsApi.list({ size: 30 });
      setTicketsList(data.items);
    } catch (err) {
      console.error('Failed to load tickets list for RAG selector', err);
    }
  };

  useEffect(() => {
    loadDocuments();
    loadTickets();
  }, [categoryFilter, typeFilter]);

  useEffect(() => {
    if (searchParams.get('ticketId')) {
      setActiveTab('troubleshoot');
      setTicketIdInput(searchParams.get('ticketId') || '');
      handleGenerateSolution(parseInt(searchParams.get('ticketId')!));
    }
  }, [searchParams]);

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) {
      setUploadError('Please select a file to ingest.');
      return;
    }
    setUploadError('');
    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('title', uploadTitle);
      formData.append('doc_type', uploadDocType);
      formData.append('service', uploadService);
      formData.append('category', uploadCategory);
      formData.append('version', uploadVersion);
      formData.append('owner', uploadOwner);
      formData.append('file', uploadFile);

      await knowledgeApi.uploadDocument(formData);
      setUploadModalOpen(false);
      setUploadTitle('');
      setUploadFile(null);
      await loadDocuments();
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || 'Document ingestion failed.');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (docId: number) => {
    if (!confirm(`Are you sure you want to remove document #${docId}?`)) return;
    try {
      await knowledgeApi.deleteDocument(docId);
      await loadDocuments();
    } catch (err) {
      console.error('Failed to delete doc', err);
    }
  };

  const handleReindex = async (docId: number) => {
    try {
      await knowledgeApi.reindexDocument(docId);
      await loadDocuments();
    } catch (err) {
      console.error('Failed to reindex doc', err);
    }
  };

  const handleInspectDoc = async (docId: number) => {
    try {
      const data = await knowledgeApi.getDocument(docId);
      setSelectedDocDetails(data);
    } catch (err) {
      console.error('Failed to inspect doc', err);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    try {
      setSearching(true);
      const res = await knowledgeApi.searchKnowledge(searchQuery.trim());
      setSearchResults(res.sources);
    } catch (err) {
      console.error('Search failed', err);
    } finally {
      setSearching(false);
    }
  };

  const handleGenerateSolution = async (tid?: number) => {
    const idToUse = tid || parseInt(ticketIdInput);
    if (!idToUse) {
      setSolutionError('Please select or specify a valid Ticket ID.');
      return;
    }
    setSolutionError('');
    setGeneratingSolution(true);

    try {
      const sol = await knowledgeApi.generateSolution(idToUse);
      setGroundedSolution(sol);
    } catch (err: any) {
      setSolutionError(err.response?.data?.detail || 'Failed to generate grounded solution.');
    } finally {
      setGeneratingSolution(false);
    }
  };

  const copyText = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filteredDocs = documents.filter((d) => {
    if (categoryFilter !== 'All' && d.category !== categoryFilter) return false;
    if (typeFilter !== 'All' && d.doc_type !== typeFilter) return false;
    if (
      searchKeyword &&
      !d.title.toLowerCase().includes(searchKeyword.toLowerCase()) &&
      !d.service.toLowerCase().includes(searchKeyword.toLowerCase())
    )
      return false;
    return true;
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12 animate-fade-in-up">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-sky-950/60 pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sky-500/20 to-cyan-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400 shadow-lg shadow-sky-950/50">
              <BookOpen className="w-5 h-5 text-sky-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold tracking-tight text-white font-display">
                  Knowledge Base & RAG Evidence Retrieval
                </h1>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-sky-500/10 text-sky-300 border border-sky-500/20">
                  MILESTONE 2
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Verified airline policies, passenger rights runbooks, tariff guidelines, and vector semantic grounding.
              </p>
            </div>
          </div>
        </div>

        {isSupport && (
          <button
            onClick={() => setUploadModalOpen(true)}
            className="px-4 py-2.5 bg-gradient-to-r from-sky-600 via-sky-500 to-cyan-500 hover:from-sky-500 hover:to-cyan-400 text-white rounded-xl text-xs font-semibold shadow-lg shadow-sky-600/25 transition-all flex items-center gap-2 self-start transform hover:-translate-y-0.5 active:translate-y-0 cursor-pointer"
          >
            <Upload className="w-4 h-4" />
            Ingest Document
          </button>
        )}
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-800/80 space-x-2 md:space-x-8 text-xs font-medium overflow-x-auto pb-1">
        <button
          onClick={() => setActiveTab('documents')}
          className={`pb-3 px-1 flex items-center gap-2 transition-all relative whitespace-nowrap cursor-pointer ${
            activeTab === 'documents' ? 'text-sky-400 font-bold' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Layers className="w-4 h-4" />
          Indexed Policies ({documents.length})
          {activeTab === 'documents' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-sky-500 to-cyan-400 rounded-full" />
          )}
        </button>

        <button
          onClick={() => setActiveTab('search')}
          className={`pb-3 px-1 flex items-center gap-2 transition-all relative whitespace-nowrap cursor-pointer ${
            activeTab === 'search' ? 'text-sky-400 font-bold' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Search className="w-4 h-4" />
          Interactive Vector Search
          {activeTab === 'search' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-sky-500 to-cyan-400 rounded-full" />
          )}
        </button>

        <button
          onClick={() => setActiveTab('troubleshoot')}
          className={`pb-3 px-1 flex items-center gap-2 transition-all relative whitespace-nowrap cursor-pointer ${
            activeTab === 'troubleshoot' ? 'text-sky-400 font-bold' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Sparkles className="w-4 h-4 text-cyan-400" />
          Grounded RAG Solution Generator
          {activeTab === 'troubleshoot' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-sky-500 to-cyan-400 rounded-full" />
          )}
        </button>
      </div>

      {/* TAB 1: Indexed Documents List */}
      {activeTab === 'documents' && (
        <div className="space-y-6">
          {/* Filters Bar */}
          <div className="aviation-glass-card rounded-2xl p-4 flex flex-col md:flex-row gap-4 items-center justify-between shadow-sm">
            <div className="relative w-full md:w-80">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                placeholder="Filter by title or service..."
                className="w-full bg-slate-900/90 border border-slate-700/80 rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-sky-500 transition-all shadow-inner"
              />
            </div>

            <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
              <div className="flex items-center gap-1.5 text-xs text-slate-400">
                <span className="font-mono text-[11px]">Category:</span>
                <select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  className="bg-slate-900/90 border border-slate-700/80 rounded-xl px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                >
                  {CATEGORIES.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center gap-1.5 text-xs text-slate-400">
                <span className="font-mono text-[11px]">Type:</span>
                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                  className="bg-slate-900/90 border border-slate-700/80 rounded-xl px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                >
                  {DOC_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </div>

              <button
                onClick={loadDocuments}
                className="p-2 bg-slate-900/90 border border-slate-700/80 rounded-xl text-slate-300 hover:text-white hover:border-slate-600 transition-colors cursor-pointer"
                title="Refresh documents"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-sky-400' : ''}`} />
              </button>
            </div>
          </div>

          {/* Documents Table */}
          <div className="aviation-glass-card rounded-2xl shadow-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/80 text-[10px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-800 font-mono">
                  <tr>
                    <th className="py-3.5 px-6">Document Title & Owner</th>
                    <th className="py-3.5 px-6">Doc Type</th>
                    <th className="py-3.5 px-6">Service & Category</th>
                    <th className="py-3.5 px-6">Status & Chunks</th>
                    <th className="py-3.5 px-6">File</th>
                    <th className="py-3.5 px-6 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {loading && documents.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-12 text-center text-slate-400">
                        <RefreshCw className="w-6 h-6 text-sky-500 animate-spin mx-auto mb-2" />
                        Loading airline policy corpus...
                      </td>
                    </tr>
                  ) : filteredDocs.length > 0 ? (
                    filteredDocs.map((doc) => (
                      <tr key={doc.id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-4 px-6">
                          <button
                            onClick={() => handleInspectDoc(doc.id)}
                            className="font-bold text-white hover:text-sky-400 text-left block font-display transition-colors cursor-pointer"
                          >
                            {doc.title}
                          </button>
                          <span className="text-[11px] text-slate-400 mt-0.5 block">
                            Owner: {doc.owner} (v{doc.version})
                          </span>
                        </td>
                        <td className="py-4 px-6">
                          <span className="px-2 py-0.5 rounded text-[10px] bg-slate-900 text-slate-300 border border-slate-700/80 font-mono">
                            {doc.doc_type}
                          </span>
                        </td>
                        <td className="py-4 px-6">
                          <div className="text-white font-medium">{doc.service}</div>
                          <div className="text-slate-400 text-[11px]">{doc.category}</div>
                        </td>
                        <td className="py-4 px-6">
                          <div className="flex items-center gap-2">
                            <span
                              className={`text-[10px] font-bold px-2 py-0.5 rounded border font-mono ${
                                doc.status === 'INDEXED'
                                  ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20'
                                  : 'bg-amber-500/10 text-amber-300 border-amber-500/20'
                              }`}
                            >
                              {doc.status}
                            </span>
                            <span className="text-[11px] font-mono text-cyan-400 font-bold bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800">
                              {doc.chunk_count} chunks
                            </span>
                          </div>
                        </td>
                        <td className="py-4 px-6 font-mono text-slate-400 text-[11px]">
                          {doc.file_name || 'Embedded'}
                        </td>
                        <td className="py-4 px-6 text-right space-x-1.5 whitespace-nowrap">
                          <button
                            onClick={() => handleInspectDoc(doc.id)}
                            className="p-1.5 rounded-lg bg-slate-900/90 hover:bg-slate-800 text-slate-300 border border-slate-700 hover:text-white transition-colors cursor-pointer"
                            title="Inspect Chunks"
                          >
                            <Eye className="w-3.5 h-3.5" />
                          </button>
                          {isSupport && (
                            <>
                              <button
                                onClick={() => handleReindex(doc.id)}
                                className="p-1.5 rounded-lg bg-slate-900/90 hover:bg-slate-800 text-sky-400 border border-slate-700 hover:text-sky-300 transition-colors cursor-pointer"
                                title="Reindex Embeddings"
                              >
                                <RefreshCw className="w-3.5 h-3.5" />
                              </button>
                              <button
                                onClick={() => handleDelete(doc.id)}
                                className="p-1.5 rounded-lg bg-slate-900/90 hover:bg-rose-950/40 text-rose-400 border border-slate-700 hover:border-rose-500/40 transition-colors cursor-pointer"
                                title="Delete Document"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </>
                          )}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={6} className="py-12 text-center text-slate-400 text-xs">
                        No policy documents match the current filter.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: Interactive Vector Search */}
      {activeTab === 'search' && (
        <div className="space-y-6">
          <form onSubmit={handleSearch} className="aviation-glass-card rounded-2xl p-6 shadow-xl space-y-4">
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider block font-mono flex items-center gap-2">
              <Search className="w-3.5 h-3.5 text-sky-400" />
              Semantic & Keyword Hybrid Retrieval Query
            </span>
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="e.g. Flight delay compensation rule under European Regulation EC 261 or baggage damaged liability"
                className="flex-1 bg-slate-900/90 border border-slate-700/80 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-sky-500 transition-all shadow-inner"
              />
              <button
                type="submit"
                disabled={searching}
                className="px-6 py-2.5 bg-gradient-to-r from-sky-600 to-cyan-500 hover:from-sky-500 hover:to-cyan-400 text-white text-xs font-semibold rounded-xl shadow-lg shadow-sky-600/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50 cursor-pointer"
              >
                {searching ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                Retrieve Evidence
              </button>
            </div>
          </form>

          {/* Results list */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider font-mono flex items-center gap-2">
              <Layers className="w-3.5 h-3.5 text-sky-400" />
              Retrieved Chunks & Semantic Similarity Scores ({searchResults.length} matches)
            </h3>

            {searchResults.length > 0 ? (
              searchResults.map((source, i) => (
                <div key={i} className="aviation-glass-card rounded-2xl p-5 shadow-sm space-y-3 hover:border-slate-700 transition-all">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2.5 flex-wrap">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/10 text-sky-400 border border-sky-500/20 font-mono">
                        Chunk #{source.chunk_index}
                      </span>
                      <h4 className="font-bold text-white text-xs font-display">{source.document_title}</h4>
                      <span className="text-[11px] text-slate-400">({source.service})</span>
                    </div>
                    <div className="flex items-center gap-2 self-start sm:self-auto">
                      <span className="text-[11px] text-slate-400 font-mono">Similarity:</span>
                      <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                        {source.similarity_score}%
                      </span>
                    </div>
                  </div>

                  <p className="text-xs text-slate-300 font-mono bg-slate-950/80 p-3.5 rounded-xl border border-slate-800/80 whitespace-pre-wrap leading-relaxed shadow-inner">
                    {source.content}
                  </p>
                </div>
              ))
            ) : (
              <div className="p-10 text-center text-slate-400 bg-slate-900/40 rounded-2xl border border-slate-800 text-xs">
                Enter an airline policy query above to test hybrid semantic retrieval across indexed knowledge chunks.
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 3: Grounded Solution Generator */}
      {activeTab === 'troubleshoot' && (
        <div className="space-y-6">
          <div className="aviation-glass-card rounded-2xl p-6 shadow-xl space-y-4">
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider block font-mono flex items-center gap-2">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
              Select Incident Ticket for Evidence-Grounded Troubleshooting
            </span>
            <div className="flex flex-col sm:flex-row gap-3">
              <select
                value={ticketIdInput}
                onChange={(e) => setTicketIdInput(e.target.value)}
                className="flex-1 bg-slate-900/90 border border-slate-700/80 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-sky-500"
              >
                <option value="">-- Choose a passenger ticket to synthesize --</option>
                {ticketsList.map((t) => (
                  <option key={t.id} value={t.id}>
                    #{t.id} - {t.title} ({t.affected_service || t.category}) [{t.status}]
                  </option>
                ))}
              </select>
              <button
                onClick={() => handleGenerateSolution()}
                disabled={generatingSolution || !ticketIdInput}
                className="px-6 py-2.5 bg-gradient-to-r from-sky-600 via-sky-500 to-cyan-500 hover:from-sky-500 hover:to-cyan-400 text-white text-xs font-semibold rounded-xl shadow-lg shadow-sky-600/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50 cursor-pointer"
              >
                {generatingSolution ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                Generate RAG Solution
              </button>
            </div>

            {solutionError && (
              <div className="p-3.5 bg-rose-950/40 border border-rose-500/30 text-rose-300 text-xs rounded-xl flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
                <span>{solutionError}</span>
              </div>
            )}
          </div>

          {/* Grounded Solution Display Card */}
          {groundedSolution && (
            <div className="aviation-glass-card rounded-2xl p-6 md:p-8 shadow-2xl space-y-6 animate-fade-in-up">
              {/* Header & Quality Pill */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
                <div>
                  <div className="flex items-center gap-3 flex-wrap">
                    <span className="text-xs font-mono font-bold bg-sky-500/10 text-sky-400 px-2.5 py-0.5 rounded border border-sky-500/20">
                      Ticket #{groundedSolution.ticket_id} Solution
                    </span>
                    <span
                      className={`text-xs font-bold px-2.5 py-0.5 rounded border font-mono ${
                        groundedSolution.evidence_quality === 'HIGH'
                          ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                          : groundedSolution.evidence_quality === 'MODERATE'
                          ? 'bg-sky-500/20 text-sky-300 border-sky-500/30'
                          : 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                      }`}
                    >
                      Evidence Quality: {groundedSolution.evidence_quality}
                    </span>
                  </div>
                  <h2 className="text-lg font-bold text-white mt-2 font-display">{groundedSolution.problem_summary}</h2>
                </div>

                <div className="flex items-center gap-3 text-xs bg-slate-950/80 px-4 py-3 rounded-xl border border-slate-800">
                  <span className="text-slate-400 font-mono">Solution Confidence:</span>
                  <span className="font-mono font-bold text-base text-emerald-400">
                    {groundedSolution.solution_confidence}%
                  </span>
                </div>
              </div>

              {/* Safety Approval Banner if required */}
              {groundedSolution.requires_human_approval && (
                <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-500/30 text-amber-200 text-xs flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
                  <div className="space-y-1">
                    <span className="font-bold">Human Supervisor Approval Mandated</span>
                    <p className="text-amber-300/90 leading-relaxed">
                      {groundedSolution.approval_reason ||
                        'Potentially high-value financial compensation or policy discretion requires station manager sign-off.'}
                    </p>
                  </div>
                </div>
              )}

              {/* Problem & Likely Root Cause */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-slate-950/70 rounded-xl border border-slate-800/80 space-y-1.5">
                  <span className="text-[10px] font-bold text-slate-400 block uppercase tracking-wider font-mono">
                    Likely Root Cause
                  </span>
                  <p className="text-xs text-slate-200 leading-relaxed">{groundedSolution.likely_root_cause}</p>
                </div>

                <div className="p-4 bg-slate-950/70 rounded-xl border border-slate-800/80 space-y-1.5">
                  <span className="text-[10px] font-bold text-slate-400 block uppercase tracking-wider font-mono">
                    Proposed Solution Overview
                  </span>
                  <p className="text-xs text-slate-200 leading-relaxed">{groundedSolution.proposed_solution}</p>
                </div>
              </div>

              {/* Step-by-Step Remediation */}
              <div className="space-y-2">
                <span className="text-xs font-bold text-slate-300 uppercase tracking-wider block font-mono">
                  Step-by-Step Passenger Remediation Instructions
                </span>
                <div className="bg-slate-950/80 rounded-xl p-4 border border-slate-800 space-y-2.5 text-xs">
                  {groundedSolution.step_by_step_instructions.map((step, idx) => (
                    <div key={idx} className="flex items-start gap-2.5 text-slate-200">
                      <span className="font-mono text-cyan-400 font-bold shrink-0">{idx + 1}.</span>
                      <span className="leading-relaxed">{step}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Risks & Rollback */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="p-4 bg-slate-950/70 rounded-xl border border-slate-800/80 space-y-2">
                  <span className="font-bold text-slate-400 uppercase tracking-wider block font-mono text-[10px]">
                    Risks & Airline Prerequisites
                  </span>
                  <ul className="list-disc list-inside text-slate-300 space-y-1">
                    {groundedSolution.risks_and_prerequisites.map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                </div>

                <div className="p-4 bg-slate-950/70 rounded-xl border border-slate-800/80 space-y-2">
                  <span className="font-bold text-slate-400 uppercase tracking-wider block font-mono text-[10px]">
                    Verification & Station Rollback
                  </span>
                  <p className="text-slate-300 leading-relaxed font-mono text-[11px]">
                    {groundedSolution.rollback_instructions}
                  </p>
                </div>
              </div>

              {/* Traceable Supporting Citations */}
              <div className="pt-4 border-t border-slate-800 space-y-3">
                <span className="text-xs font-bold text-slate-300 uppercase tracking-wider block flex items-center gap-2 font-mono">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  Verified Airline Policy Citations ({groundedSolution.supporting_citations.length})
                </span>

                {groundedSolution.supporting_citations.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {groundedSolution.supporting_citations.map((cite, i) => (
                      <div
                        key={i}
                        className="p-3.5 bg-slate-950/80 rounded-xl border border-slate-800 text-xs space-y-2 hover:border-slate-700 transition-colors"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-white text-xs font-display">{cite.document_title}</span>
                          <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                            {cite.relevance_score}% Match
                          </span>
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono">
                          Chunk Index: {cite.chunk_index}
                        </div>
                        <p className="text-slate-300 font-mono text-[11px] bg-slate-900/90 p-2.5 rounded border border-slate-800/80 leading-relaxed italic">
                          "{cite.quote_or_excerpt}"
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl text-xs text-amber-300">
                    No verified runbook citations available in knowledge base.
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Document Chunks Inspector Modal */}
      {selectedDocDetails && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="aviation-glass-card rounded-2xl max-w-3xl w-full p-6 shadow-2xl space-y-4 max-h-[85vh] flex flex-col border border-sky-500/30 animate-fade-in-up">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="font-bold text-white text-base font-display">{selectedDocDetails.title}</h3>
                <p className="text-xs text-slate-400">
                  {selectedDocDetails.service} • {selectedDocDetails.doc_type} • {selectedDocDetails.chunk_count} indexed chunks
                </p>
              </div>
              <button
                onClick={() => setSelectedDocDetails(null)}
                className="text-slate-400 hover:text-white text-lg px-2 py-1 rounded transition-colors cursor-pointer"
              >
                &times;
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-3 pr-2">
              {selectedDocDetails.chunks?.map((ch: any) => (
                <div key={ch.id} className="p-4 bg-slate-950/80 rounded-xl border border-slate-800 text-xs space-y-2">
                  <div className="flex items-center justify-between text-slate-400 font-mono text-[11px]">
                    <span className="text-sky-400 font-bold">Chunk #{ch.chunk_index}</span>
                    <span>Context: {ch.metadata?.header_context || 'General'}</span>
                  </div>
                  <pre className="text-slate-300 whitespace-pre-wrap font-mono leading-relaxed selection:bg-sky-500/30">
                    {ch.content}
                  </pre>
                </div>
              ))}
            </div>

            <div className="pt-3 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setSelectedDocDetails(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold rounded-xl transition-colors cursor-pointer"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Document Ingestion Modal */}
      {uploadModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="aviation-glass-card rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4 border border-sky-500/30 animate-fade-in-up">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-white text-base flex items-center gap-2 font-display">
                <Upload className="w-4 h-4 text-sky-400" />
                Ingest Airline Policy or Runbook
              </h3>
              <button
                onClick={() => setUploadModalOpen(false)}
                className="text-slate-400 hover:text-white text-lg px-2 py-1 rounded transition-colors cursor-pointer"
              >
                &times;
              </button>
            </div>

            {uploadError && (
              <div className="p-3 bg-rose-950/40 border border-rose-500/30 text-rose-300 text-xs rounded-xl">
                {uploadError}
              </div>
            )}

            <form onSubmit={handleUploadSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 font-semibold mb-1">Document Title</label>
                <input
                  type="text"
                  required
                  value={uploadTitle}
                  onChange={(e) => setUploadTitle(e.target.value)}
                  placeholder="e.g. EC 261 Flight Delay Compensation Policy & Disruption Protocol"
                  className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-sky-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Doc Type</label>
                  <select
                    value={uploadDocType}
                    onChange={(e) => setUploadDocType(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-sky-500"
                  >
                    <option value="Policy">Policy</option>
                    <option value="Procedure">Procedure</option>
                    <option value="Guidance">Guidance</option>
                    <option value="Runbook">Runbook</option>
                    <option value="FAQ">FAQ</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Category</label>
                  <select
                    value={uploadCategory}
                    onChange={(e) => setUploadCategory(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-sky-500"
                  >
                    {CATEGORIES.filter((c) => c !== 'All').map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Target Service</label>
                  <input
                    type="text"
                    required
                    value={uploadService}
                    onChange={(e) => setUploadService(e.target.value)}
                    placeholder="e.g. Flight Operations, Baggage, Ground Services"
                    className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-sky-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Owner Team</label>
                  <input
                    type="text"
                    required
                    value={uploadOwner}
                    onChange={(e) => setUploadOwner(e.target.value)}
                    placeholder="e.g. Passenger Support & Compliance"
                    className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-sky-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">
                  Select File (.pdf, .md, .txt, .docx, .json)
                </label>
                <input
                  type="file"
                  required
                  accept=".pdf,.md,.txt,.json,.log,.docx"
                  onChange={(e) => setUploadFile(e.target.files ? e.target.files[0] : null)}
                  className="w-full bg-slate-900 border border-slate-700/80 rounded-xl p-2 text-slate-300 text-xs focus:outline-none focus:border-sky-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setUploadModalOpen(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl cursor-pointer transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading}
                  className="px-4 py-2 bg-gradient-to-r from-sky-600 to-cyan-500 hover:from-sky-500 hover:to-cyan-400 text-white font-semibold rounded-xl shadow-lg shadow-sky-600/20 disabled:opacity-50 cursor-pointer transition-all"
                >
                  {uploading ? 'Chunking & Indexing...' : 'Upload & Index'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
