import { Component, EventEmitter, Input, Output } from '@angular/core';
import { Dialog } from 'primeng/dialog';
import { Button } from 'primeng/button';
import { DatePipe } from '@angular/common';
import { ErrorReport } from '../../core/models/error-report.model';

@Component({
  selector: 'app-error-detail-modal',
  standalone: true,
  imports: [Dialog, Button, DatePipe],
  templateUrl: './error-detail-modal.component.html'
})
export class ErrorDetailModalComponent {
  @Input() report: ErrorReport | null = null;
  @Input() visible = false;
  @Output() close = new EventEmitter<void>();
  @Output() confirmFix = new EventEmitter<string>();
  @Output() dismiss = new EventEmitter<string>();

  get showConfirmFix(): boolean {
    return this.report?.status === 'pending' && this.report?.suggestion != null;
  }

  get showDismiss(): boolean {
    return this.report?.status === 'pending';
  }

  onConfirmFix(): void {
    if (this.report) {
      this.confirmFix.emit(this.report.id);
    }
  }

  onDismiss(): void {
    if (this.report) {
      this.dismiss.emit(this.report.id);
    }
  }

  getOriginSeverity(): 'info' | 'warn' | 'danger' | 'secondary' {
    switch (this.report?.origin) {
      case 'INFRA': return 'danger';
      case 'AMBIGUOUS': return 'warn';
      default: return 'info';
    }
  }
}
