export type UserRole = 'ADMIN' | 'SUPPORT_AGENT' | 'SUPPORT_ENGINEER' | 'PASSENGER' | 'REQUESTER';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export type TicketStatus =
  | 'SUBMITTED'
  | 'NEEDS_REVIEW'
  | 'CLASSIFIED'
  | 'IN_PROGRESS'
  | 'RESOLVED'
  | 'CLOSED';

export type PriorityLevel = 'P1 Critical' | 'P2 High' | 'P3 Medium' | 'P4 Low' | 'Low' | 'Medium' | 'High' | 'Urgent';
export type CriticalityLevel = 'Critical' | 'High' | 'Medium' | 'Low';

export interface ConfidenceBreakdown {
  structured_validity?: { score: number; max: number; detail: string };
  input_completeness?: { score: number; max: number; detail: string };
  signal_agreement?: { score: number; max: number; matched_keywords: string[]; category_match: boolean; detail: string };
  diagnostic_consistency?: { score: number; max: number; detail: string };
}

export interface TicketClassification {
  id: number;
  ticket_id: number;
  predicted_category: string;
  priority: PriorityLevel;
  criticality: CriticalityLevel;
  confidence_score: number;
  explanation: string;
  detected_keywords: string[];
  potential_business_impact: string;
  recommended_next_action: string;
  missing_information: string[];
  requires_human_review: boolean;
  review_reason?: string;
  is_reviewed: boolean;
  reviewed_by_id?: number;
  review_notes?: string;
  reviewed_at?: string;
  model_name: string;
  confidence_breakdown?: ConfidenceBreakdown;
  created_at: string;
}

export interface TicketStatusHistory {
  id: number;
  ticket_id: number;
  old_status?: string;
  new_status: string;
  changed_by_id?: number;
  reason?: string;
  created_at: string;
}

export interface TicketNote {
  id: number;
  ticket_id: number;
  author_id?: number;
  author?: User;
  message_type: string;
  content: string;
  created_at: string;
}

export interface Ticket {
  id: number;
  ticket_number?: string;
  title: string;
  description: string;
  affected_service?: string;
  category: string;
  business_impact?: string;
  urgency: string;
  environment?: string;
  affected_users?: number;
  error_logs?: string;
  attachment_filename?: string;
  attachment_path?: string;

  // Airline specific fields
  passenger_name?: string;
  passenger_email?: string;
  booking_reference?: string;  // PNR
  flight_number?: string;
  travel_date?: string;
  assigned_agent_id?: number;
  assigned_agent?: User;
  ai_confidence?: number;
  final_response?: string;
  resolved_at?: string;

  status: TicketStatus;
  reporter_id: number;
  reporter?: User;
  classification?: TicketClassification;
  status_history?: TicketStatusHistory[];
  notes?: TicketNote[];
  jira_records?: JiraRecord[];
  created_at: string;
  updated_at: string;
}

export interface DashboardSummary {
  total_tickets: number;
  open_tickets: number;
  ai_resolved_tickets: number;
  escalated_tickets: number;
  avg_resolution_time: string;
  ai_resolution_rate: number;

  critical_tickets: number;
  awaiting_review_tickets: number;
  eligible_for_automation_tickets: number;
  resolved_tickets: number;

  priority_distribution: { name: string; count: number }[];
  category_distribution: { name: string; count: number }[];
  status_distribution?: { name: string; count: number }[];
  volume_trend: { date: string; count: number }[];
  recent_activity: Ticket[];
}

export interface AppSetting {
  key: string;
  value: string;
  description?: string;
  updated_at: string;
}

export interface KnowledgeDocument {
  id: number;
  title: string;
  doc_type: string;
  service: string;
  category: string;
  version: string;
  owner: string;
  file_name?: string;
  file_size_bytes: number;
  status: string;
  error_message?: string;
  chunk_count: number;
  created_at: string;
}

export interface DocumentChunk {
  id: number;
  document_id: number;
  chunk_index: number;
  content: string;
  metadata_json: Record<string, any>;
  created_at: string;
}

export interface RetrievedSource {
  document_id: number;
  document_title: string;
  chunk_id: number;
  chunk_index: number;
  similarity_score: number;
  content: string;
  service: string;
  category: string;
}

export interface GroundedSolution {
  ticket_id: number;
  problem_summary: string;
  likely_root_cause: string;
  diagnostic_checks: string[];
  step_by_step_instructions: string[];
  proposed_solution: string;
  risks_and_prerequisites: string[];
  verification_steps: string[];
  rollback_instructions: string;
  supporting_citations: {
    document_title: string;
    chunk_index: number;
    quote_or_excerpt: string;
    relevance_score: number;
  }[];
  evidence_quality: 'HIGH' | 'MODERATE' | 'LOW' | 'INSUFFICIENT';
  solution_confidence: number;
  requires_human_approval: boolean;
  approval_reason?: string;
}

export interface AgentExecutionRecord {
  id: number;
  agent_name: string;
  status: string;
  inputs: Record<string, any>;
  outputs: Record<string, any>;
  duration_ms: number;
  error_message?: string;
  created_at: string;
}

export interface WorkflowExecutionRecord {
  id: number;
  ticket_id: number;
  status: string;
  current_agent?: string;
  revision_cycles: number;
  state_payload: Record<string, any>;
  error_details?: string;
  agent_executions: AgentExecutionRecord[];
  created_at: string;
  updated_at: string;
}

export interface JiraRecord {
  id: number;
  ticket_id: number;
  jira_key: string;
  jira_url: string;
  project_key: string;
  issue_type: string;
  summary: string;
  priority: string;
  status: string;
  idempotency_key: string;
  created_at: string;
}

export interface JiraProject {
  id: string;
  key: string;
  name: string;
  project_type_key?: string;
  lead_name?: string;
  avatar_url?: string;
}

export interface JiraComment {
  id: string;
  author: string;
  body: string;
  created_at: string;
}

export interface JiraTransition {
  id: string;
  name: string;
  to_status: string;
}

export interface JiraIssue {
  id: string;
  key: string;
  url: string;
  project_key: string;
  summary: string;
  description: string;
  issue_type: string;
  priority: string;
  status: string;
  assignee_name?: string;
  reporter_name?: string;
  created_at: string;
  updated_at?: string;
  comments: JiraComment[];
  transitions: JiraTransition[];
  idempotency_key?: string;
}

export interface JiraIssueListResponse {
  items: JiraIssue[];
  total: number;
  page: number;
  size: number;
  pages: number;
  project_key?: string;
}

export interface JiraStatus {
  connected: boolean;
  mode: string;
  project_key: string;
  base_url: string;
  default_issue_type: string;
  configured_email?: string;
  is_enabled: boolean;
}

export interface AiSolutionResult {
  evaluation_id?: number;
  ticket_id: number;
  passenger_name: string;
  booking_reference?: string;
  flight_number?: string;
  category: string;
  ai_interpretation: string;
  detected_keywords: string[];
  retrieved_sources: {
    chunk_id: number;
    document_title: string;
    relevance_score: number;
    similarity_percentage: number;
    excerpt: string;
  }[];
  generated_response: string;
  policy_summary: string;
  actionable_steps: string[];
  citations: {
    document_title: string;
    chunk_id: number;
    relevance_score: number;
  }[];
  confidence_score: number;
  threshold: number;
  eligible_for_auto_resolve: boolean;
  latency_ms?: number;
  model_name?: string;
  validation: {
    verdict: string;
    is_valid: boolean;
    validation_checks: { check: string; status: string; detail: string }[];
    rejection_reasons: string[];
    summary: string;
  };
  generated_at: string;
}

export interface AIEvaluationItem {
  id: number;
  ticket_id: number;
  ticket_number: string;
  passenger_name: string;
  booking_reference?: string;
  flight_number?: string;
  category: string;
  subject: string;
  model_name: string;
  confidence_score: number;
  validation_outcome: string;
  final_outcome: string;
  escalation_reason?: string;
  latency_ms: number;
  retrieved_sources_count: number;
  created_at: string;
  human_feedback?: {
    id: number;
    accuracy_label: string;
    rating?: number;
    notes?: string;
  };
}

export interface AnalyticsOverview {
  total_evaluations: number;
  successful_resolutions: number;
  ai_resolution_rate: number;
  escalated_count: number;
  human_escalation_rate: number;
  avg_confidence: number;
  avg_latency_ms: number;
  validation_pass_count: number;
  validation_pass_rate: number;
  ai_error_count: number;
  ai_error_rate: number;
  ground_truth_accuracy: number;
  total_feedback_count: number;
  date_range: string;
}

export interface ConfidenceBucket {
  range: string;
  count: number;
  percentage: number;
  tickets: number[];
  color: string;
}

export interface CategoryMetric {
  category: string;
  total_evaluations: number;
  resolution_rate: number;
  escalation_rate: number;
  avg_confidence: number;
  validation_pass_rate: number;
}

export interface ModelComparisonItem {
  model_name: string;
  evaluations_count: number;
  resolution_rate: number;
  avg_confidence: number;
  validation_pass_rate: number;
  escalation_rate: number;
  avg_latency_ms: number;
  error_rate: number;
}

export interface AgentPerformanceItem {
  agent_name: string;
  total_executions: number;
  successful_executions: number;
  failure_rate: number;
  avg_duration_ms: number;
  retry_count: number;
  specialized_metric: string;
  failure_reasons: string[];
}

