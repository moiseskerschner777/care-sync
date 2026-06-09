import { Component, EventEmitter, Input, Output } from '@angular/core';
import { DatePipe, PercentPipe } from '@angular/common';
import { Tag } from 'primeng/tag';
import { Button } from 'primeng/button';
import { ErrorReport } from '../../core/models/error-report.model';

@Component({
  selector: 'app-error-summary-row',
  standalone: true,
  imports: [Tag, Button, DatePipe, PercentPipe],
  templateUrl: './error-summary-row.component.html',
  styleUrl: './error-summary-row.component.css'
})
export class ErrorSummaryRowComponent {
  @Input({ required: true }) report!: ErrorReport;
  @Output() openDetail = new EventEmitter<ErrorReport>();

  getStatusSeverity(): 'warning' | 'success' | 'secondary' {
    switch (this.report.status) {
      case 'fixed':
        return 'success';
      case 'dismissed':
        return 'secondary';
      default:
        return 'warning';
    }
  }

  getStatusColor(): string {
    switch (this.report.status) {
      case 'fixed':
        return '#22c55e';
      case 'dismissed':
        return '#9ca3af';
      default:
        return '#f59e0b';
    }
  }
}
