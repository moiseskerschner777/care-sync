export interface ErrorReport {
  id: string;
  created_at: string;
  system_target: string;
  operation: string;
  origin: string;
  confidence: number;
  evidence: string;
  suggestion: string | null;
  payload_sent: string;
  raw_error: string;
  audit_event_id: string | null;
  payload_hash: string;
  raw_error_hash: string;
  status: string;
}
