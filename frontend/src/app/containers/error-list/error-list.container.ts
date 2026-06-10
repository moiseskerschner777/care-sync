import { Component, OnInit } from '@angular/core';
import { Button } from 'primeng/button';
import { Toast } from 'primeng/toast';
import { ProgressSpinner } from 'primeng/progressspinner';
import { MessageService } from 'primeng/api';
import { ErrorSummaryRowComponent } from '../../components/error-summary-row/error-summary-row.component';
import { ErrorDetailModalComponent } from '../../components/error-detail-modal/error-detail-modal.component';
import { ErrorReport } from '../../core/models/error-report.model';
import { ErrorReportService } from '../../core/services/error-report.service';

@Component({
  selector: 'app-error-list',
  standalone: true,
  imports: [Button, Toast, ProgressSpinner, ErrorSummaryRowComponent, ErrorDetailModalComponent],
  templateUrl: './error-list.container.html'
})
export class ErrorListContainer implements OnInit {
  reports: ErrorReport[] = [];
  selectedReport: ErrorReport | null = null;
  modalVisible = false;
  loading = true;

  constructor(
    private errorReportService: ErrorReportService,
    private messageService: MessageService
  ) {}

  ngOnInit(): void {
    this.loadReports();
  }

  loadReports(): void {
    this.loading = true;
    this.errorReportService.getReports().subscribe({
      next: (reports) => {
        this.reports = reports;
        this.loading = false;
      },
      error: (err) => {
        this.loading = false;
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: err.message || 'Failed to load error reports'
        });
      }
    });
  }

  onOpenDetail(report: ErrorReport): void {
    this.selectedReport = report;
    this.modalVisible = true;
  }

  onConfirmFix(id: string): void {
    this.errorReportService.confirmFix(id).subscribe({
      next: (response) => {
        if (response.status === 'fixed') {
          const report = this.reports.find(r => r.id === id);
          if (report) {
            report.status = 'fixed';
          }
          this.modalVisible = false;
        } else if (response.status === 'pending') {
          this.loadReports();
          this.modalVisible = false;
        }
      },
      error: (err) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: err.message || 'Failed to confirm fix'
        });
      }
    });
  }

  onDismiss(id: string): void {
    this.errorReportService.dismiss(id).subscribe({
      next: () => {
        const report = this.reports.find(r => r.id === id);
        if (report) {
          report.status = 'dismissed';
        }
        this.modalVisible = false;
      },
      error: (err) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: err.message || 'Failed to dismiss report'
        });
      }
    });
  }
}
