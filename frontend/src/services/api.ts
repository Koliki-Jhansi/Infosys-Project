import axios from 'axios';
import {
  User,
  Ticket,
  TicketClassification,
  DashboardSummary,
  AppSetting,
  KnowledgeDocument,
  RetrievedSource,
  GroundedSolution,
  WorkflowExecutionRecord,
  JiraRecord,
  JiraProject,
  JiraIssue,
  JiraComment,
  JiraTransition,
  JiraIssueListResponse,
  JiraStatus,
  TicketNote,
  AiSolutionResult
} from '../types';

const rawBaseUrl = (import.meta.env.VITE_API_BASE_URL as string) || 'http://127.0.0.1:8081';
const normalizedBaseUrl = rawBaseUrl.endsWith('/') ? rawBaseUrl.slice(0, -1) : rawBaseUrl;
export const API_BASE_URL = normalizedBaseUrl.endsWith('/api') ? normalizedBaseUrl : `${normalizedBaseUrl}/api`;

export const getApiErrorMessage = (err: any, fallback: string = 'Operation failed'): string => {
  if (!err) return fallback;
  if (err.response?.data) {
    const data = err.response.data;
    if (typeof data.detail === 'string') return data.detail;
    if (Array.isArray(data.detail)) {
      return data.detail.map((item: any) => {
        if (typeof item === 'string') return item;
        const field = item.loc ? item.loc.filter((p: any) => p !== 'body').join('.') : '';
        return field ? `${field}: ${item.msg}` : (item.msg || JSON.stringify(item));
      }).join('; ');
    }
    if (typeof data.message === 'string') return data.message;
    if (typeof data.error === 'string') return data.error;
  }
  if (err.message) {
    if (err.message.includes('Network Error')) {
      return 'Unable to reach backend server at http://127.0.0.1:8081. Please ensure the backend is running.';
    }
    return err.message;
  }
  return fallback;
};

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('aero_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('aero_token');
      localStorage.removeItem('aero_user');
      if (window.location.pathname !== '/login' && window.location.pathname !== '/register' && window.location.pathname !== '/welcome' && window.location.pathname !== '/') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: async (credentials: any) => {
    const res = await api.post<{ access_token: string; user: User }>('/auth/login', credentials);
    return res.data;
  },
  register: async (payload: any) => {
    const res = await api.post<{ access_token: string; user: User }>('/auth/register', payload);
    return res.data;
  },
  getMe: async () => {
    const res = await api.get<User>('/auth/me');
    return res.data;
  },
  logout: async () => {
    localStorage.removeItem('aero_token');
    localStorage.removeItem('aero_user');
    try {
      await api.post('/auth/logout');
    } catch {
      // Ignore network errors on logout
    }
  }
};

export const ticketsApi = {
  create: async (data: any) => {
    const res = await api.post<Ticket>('/tickets', data);
    return res.data;
  },
  createWithAttachment: async (formData: FormData) => {
    const res = await api.post<Ticket>('/tickets/with-attachment', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  list: async (params?: any) => {
    const res = await api.get<{ items: Ticket[]; total: number; page: number; size: number; pages: number }>('/tickets', { params });
    return res.data;
  },
  getEscalated: async (params?: any) => {
    const res = await api.get<{ items: Ticket[]; total: number; page: number; size: number; pages: number }>('/tickets/escalated', { params });
    return res.data;
  },
  getById: async (id: number) => {
    const res = await api.get<Ticket>(`/tickets/${id}`);
    return res.data;
  },
  patch: async (id: number, data: any) => {
    const res = await api.patch<Ticket>(`/tickets/${id}`, data);
    return res.data;
  },
  addNote: async (id: number, note: { content: string; message_type?: string }) => {
    const res = await api.post<TicketNote>(`/tickets/${id}/notes`, note);
    return res.data;
  },
  resolve: async (id: number, payload?: { response?: string }) => {
    const res = await api.post<Ticket>(`/tickets/${id}/resolve`, payload);
    return res.data;
  },
  escalate: async (id: number, payload?: { reason?: string }) => {
    const res = await api.post<Ticket>(`/tickets/${id}/escalate`, payload);
    return res.data;
  },
  getHistory: async (id: number) => {
    const res = await api.get<any>(`/tickets/${id}/history`);
    return res.data;
  },
  classify: async (id: number) => {
    const res = await api.post<TicketClassification>(`/tickets/${id}/classify`);
    return res.data;
  },
};

export const aiSolutionApi = {
  resolve: async (ticketId: number, customInstructions?: string, forceCategory?: string) => {
    const res = await api.post<AiSolutionResult>(`/ai/resolve/${ticketId}`, {
      custom_instructions: customInstructions,
      force_category: forceCategory
    });
    return res.data;
  },
  getResults: async (ticketId: number) => {
    const res = await api.get<any>(`/ai/results/${ticketId}`);
    return res.data;
  },
  validate: async (ticketId: number, responseText: string) => {
    const res = await api.post<any>(`/ai/validate/${ticketId}`, { response_text: responseText });
    return res.data;
  }
};

export const reviewsApi = {
  getQueue: async () => {
    const res = await api.get<Ticket[]>('/reviews');
    return res.data;
  },
  reviewTicket: async (ticketId: number, payload: { action: 'APPROVE' | 'REJECT' | 'OVERRIDE'; notes?: string; override_category?: string; override_priority?: string }) => {
    const res = await api.post<{ success: boolean; ticket_id: number; new_status: string; message: string }>(`/tickets/${ticketId}/review`, payload);
    return res.data;
  },
};

export const dashboardApi = {
  getSummary: async () => {
    const res = await api.get<DashboardSummary>('/dashboard/summary');
    return res.data;
  },
  getAnalytics: async () => {
    const res = await api.get<any>('/dashboard/analytics');
    return res.data;
  },
  getRecentTickets: async () => {
    const res = await api.get<Ticket[]>('/dashboard/recent-tickets');
    return res.data;
  }
};

export const settingsApi = {
  getAll: async () => {
    const res = await api.get<AppSetting[]>('/settings');
    return res.data;
  },
  update: async (key: string, value: string) => {
    const res = await api.put<AppSetting>(`/settings/${key}`, { value });
    return res.data;
  },
};

export const knowledgeApi = {
  listDocuments: async () => {
    const res = await api.get<KnowledgeDocument[]>('/knowledge/documents');
    return res.data;
  },
  uploadDocument: async (formData: FormData) => {
    const res = await api.post<KnowledgeDocument>('/knowledge/documents', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  getDocument: async (id: number) => {
    const res = await api.get<KnowledgeDocument>(`/knowledge/documents/${id}`);
    return res.data;
  },
  deleteDocument: async (id: number) => {
    const res = await api.delete(`/knowledge/documents/${id}`);
    return res.data;
  },
  reindexDocument: async (id: number) => {
    const res = await api.post(`/knowledge/documents/${id}/reindex`);
    return res.data;
  },
  searchKnowledge: async (query: string, service?: string, category?: string) => {
    const res = await api.post<{ sources: RetrievedSource[]; count: number }>('/knowledge/search', { query, service, category });
    return res.data;
  },
  generateSolution: async (ticketId: number) => {
    const res = await api.post<GroundedSolution>(`/tickets/${ticketId}/solution`);
    return res.data;
  },
  getSolution: async (ticketId: number) => {
    const res = await api.get<GroundedSolution>(`/tickets/${ticketId}/solution`);
    return res.data;
  },
};

export const workflowApi = {
  runForTicket: async (ticketId: number) => {
    const res = await api.post<WorkflowExecutionRecord>(`/workflows/run/${ticketId}`);
    return res.data;
  },
  execute: async (ticketId: number) => {
    const res = await api.post<WorkflowExecutionRecord>(`/tickets/${ticketId}/workflow`);
    return res.data;
  },
  getForTicket: async (ticketId: number) => {
    const res = await api.get<WorkflowExecutionRecord>(`/tickets/${ticketId}/workflow`);
    return res.data;
  },
  getTicketWorkflows: async (ticketId: number) => {
    const res = await api.get<WorkflowExecutionRecord[]>(`/tickets/${ticketId}/workflows`);
    return res.data;
  },
  getById: async (workflowId: number) => {
    const res = await api.get<WorkflowExecutionRecord>(`/workflows/${workflowId}`);
    return res.data;
  },
  resume: async (workflowId: number) => {
    const res = await api.post<WorkflowExecutionRecord>(`/workflows/${workflowId}/resume`);
    return res.data;
  },
  cancel: async (workflowId: number) => {
    const res = await api.post<WorkflowExecutionRecord>(`/workflows/${workflowId}/cancel`);
    return res.data;
  },
  approve: async (workflowId: number, notes?: string) => {
    const res = await api.post<WorkflowExecutionRecord>(`/workflows/${workflowId}/approve`, { notes });
    return res.data;
  },
  reject: async (workflowId: number, notes?: string) => {
    const res = await api.post<WorkflowExecutionRecord>(`/workflows/${workflowId}/reject`, { notes });
    return res.data;
  },
};

export const jiraApi = {
  getStatus: async () => {
    const res = await api.get<JiraStatus>('/integrations/jira/status');
    return res.data;
  },
  testConnection: async () => {
    const res = await api.post<{ success: boolean; mode: string; message: string; user?: string; email?: string; project_key?: string; project_count?: number; error?: string }>('/integrations/jira/test');
    return res.data;
  },
  getProjects: async () => {
    const res = await api.get<JiraProject[]>('/integrations/jira/projects');
    return res.data;
  },
  getIssues: async (params?: { project_key?: string; search?: string; status?: string; priority?: string; jql?: string; page?: number; size?: number }) => {
    const res = await api.get<JiraIssueListResponse>('/integrations/jira/issues', { params });
    return res.data;
  },
  getIssue: async (issueKey: string) => {
    const res = await api.get<JiraIssue>(`/integrations/jira/issues/${issueKey}`);
    return res.data;
  },
  createIssue: async (payload: { project_key?: string; summary: string; description: string; priority?: string; issue_type?: string; assignee?: string; idempotency_key?: string }) => {
    const res = await api.post<JiraIssue>('/integrations/jira/issues', payload);
    return res.data;
  },
  updateIssue: async (issueKey: string, payload: { summary?: string; description?: string }) => {
    const res = await api.put<JiraIssue>(`/integrations/jira/issues/${issueKey}`, payload);
    return res.data;
  },
  getTransitions: async (issueKey: string) => {
    const res = await api.get<JiraTransition[]>(`/integrations/jira/issues/${issueKey}/transitions`);
    return res.data;
  },
  transitionIssue: async (issueKey: string, payload: { transition_id: string; comment?: string }) => {
    const res = await api.post<JiraIssue>(`/integrations/jira/issues/${issueKey}/transitions`, payload);
    return res.data;
  },
  getComments: async (issueKey: string) => {
    const res = await api.get<JiraComment[]>(`/integrations/jira/issues/${issueKey}/comments`);
    return res.data;
  },
  addComment: async (issueKey: string, comment: string) => {
    const res = await api.post<JiraComment>(`/integrations/jira/issues/${issueKey}/comments`, { comment });
    return res.data;
  },
  createTicketIssue: async (ticketId: number) => {
    const res = await api.post<JiraRecord>(`/tickets/${ticketId}/jira`);
    return res.data;
  },
  refreshTicketJira: async (ticketId: number) => {
    const res = await api.post<JiraRecord>(`/tickets/${ticketId}/jira/refresh`);
    return res.data;
  },
};

export const analyticsApi = {
  getObservabilityMetrics: async () => {
    const res = await api.get<any>('/analytics/metrics');
    return res.data;
  },
  getOverview: async (params?: any) => {
    const res = await api.get<any>('/analytics/overview', { params });
    return res.data;
  },
  getConfidenceDistribution: async (params?: any) => {
    const res = await api.get<any>('/analytics/confidence-distribution', { params });
    return res.data;
  },
  getResolutionTrends: async (params?: any) => {
    const res = await api.get<any>('/analytics/resolution-trends', { params });
    return res.data;
  },
  getCategoryPerformance: async (params?: any) => {
    const res = await api.get<any>('/analytics/category-performance', { params });
    return res.data;
  },
  getModelComparison: async () => {
    const res = await api.get<any>('/analytics/model-comparison');
    return res.data;
  },
  getAgentPerformance: async () => {
    const res = await api.get<any>('/analytics/agent-performance');
    return res.data;
  },
  getEvaluations: async (params?: any) => {
    const res = await api.get<{ items: any[]; total: number; page: number; size: number; pages: number }>('/analytics/evaluations', { params });
    return res.data;
  },
  getErrors: async (params?: any) => {
    const res = await api.get<any>('/analytics/errors', { params });
    return res.data;
  },
  submitFeedback: async (payload: { evaluation_id: number; ticket_id: number; accuracy_label: string; source_grounding_rating?: number; notes?: string }) => {
    const res = await api.post<any>('/analytics/feedback', payload);
    return res.data;
  },
  exportCsv: async (params?: any) => {
    const res = await api.get('/analytics/export', { params, responseType: 'blob' });
    return res.data;
  }
};

export default api;
