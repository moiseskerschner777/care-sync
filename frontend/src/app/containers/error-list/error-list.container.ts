import { Component } from '@angular/core';
import { Button } from 'primeng/button';
import { ErrorSummaryRowComponent } from '../../components/error-summary-row/error-summary-row.component';
import { ErrorDetailModalComponent } from '../../components/error-detail-modal/error-detail-modal.component';
import { ErrorReport } from '../../core/models/error-report.model';

const MOCK_REPORTS: ErrorReport[] = [
  {
    id: 'err-001',
    created_at: '2025-06-09T08:15:00Z',
    system_target: 'RefLab',
    operation: 'create_order',
    origin: 'ORIGIN_B',
    confidence: 0.85,
    evidence: 'Mismatch in required fields validation',
    suggestion: 'Retry with corrected payload structure',
    payload_sent: '{"patient_id": "123", "test": "CBC"}',
    raw_error: '{"status": 400, "detail": "Invalid field format"}',
    audit_event_id: 'audit-001',
    payload_hash: 'ph1',
    raw_error_hash: 'reh1',
    status: 'pending'
  },
  {
    id: 'err-002',
    created_at: '2025-06-09T09:30:00Z',
    system_target: 'VitaCare',
    operation: 'validate_coverage',
    origin: 'CONTRATO',
    confidence: 0.45,
    evidence: 'Contract number not found in system',
    suggestion: null,
    payload_sent: '{"contract": "CT-999"}',
    raw_error: '{"status": 404, "detail": "Contract not found"}',
    audit_event_id: 'audit-002',
    payload_hash: 'ph2',
    raw_error_hash: 'reh2',
    status: 'pending'
  },
  {
    id: 'err-003',
    created_at: '2025-06-08T14:00:00Z',
    system_target: 'LabCore',
    operation: 'update_order',
    origin: 'INFRA',
    confidence: 0.92,
    evidence: 'Connection timeout after 30s',
    suggestion: 'Retry with exponential backoff',
    payload_sent: '{"order_id": "ORD-456"}',
    raw_error: '{"status": 504, "detail": "Gateway timeout"}',
    audit_event_id: null,
    payload_hash: 'ph3',
    raw_error_hash: 'reh3',
    status: 'fixed'
  }
];

@Component({
  selector: 'app-error-list',
  standalone: true,
  imports: [Button, ErrorSummaryRowComponent, ErrorDetailModalComponent],
  templateUrl: './error-list.container.html'
})
export class ErrorListContainer {
  reports: ErrorReport[] = MOCK_REPORTS;
  selectedReport: ErrorReport | null = null;
  modalVisible = false;

  onOpenDetail(report: ErrorReport): void {
    this.selectedReport = report;
    this.modalVisible = true;
  }

  onCloseModal(): void {
    this.modalVisible = false;
  }
}
