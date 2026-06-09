import { Component } from '@angular/core';
import { ErrorSummaryRowComponent } from '../../components/error-summary-row/error-summary-row.component';
import { ErrorDetailModalComponent } from '../../components/error-detail-modal/error-detail-modal.component';
import { ErrorReport } from '../../core/models/error-report.model';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [ErrorSummaryRowComponent, ErrorDetailModalComponent],
  templateUrl: './dashboard.page.html'
})
export class DashboardPage {
  testReport: ErrorReport = {
    id: 'abc-123',
    created_at: '2025-06-09T10:30:00Z',
    system_target: 'RefLab',
    operation: 'create_order',
    origin: 'ORIGIN_B',
    confidence: 0.85,
    evidence: 'Some evidence text',
    suggestion: 'Retry with corrected payload',
    payload_sent: '{}',
    raw_error: '{}',
    audit_event_id: null,
    payload_hash: 'hash1',
    raw_error_hash: 'hash2',
    status: 'pending'
  };

  modalVisible = true;
}
