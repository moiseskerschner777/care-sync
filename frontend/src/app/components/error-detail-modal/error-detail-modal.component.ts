import { Component, EventEmitter, Input, OnChanges, Output, SimpleChanges } from '@angular/core';
import { Dialog } from 'primeng/dialog';
import { Button } from 'primeng/button';
import { Divider } from 'primeng/divider';
import { Tag } from 'primeng/tag';
import { ErrorReport } from '../../core/models/error-report.model';
import { operationLabel, originLabel } from '../../core/utils/display-labels';

@Component({
  selector: 'app-error-detail-modal',
  standalone: true,
  imports: [Dialog, Button, Divider, Tag],
  templateUrl: './error-detail-modal.component.html'
})
export class ErrorDetailModalComponent implements OnChanges {

  @Input() report: ErrorReport | null = null;
  @Input() visible = false;
  @Output() visibleChange = new EventEmitter<boolean>();
  @Output() confirmFix = new EventEmitter<string>();
  @Output() dismiss = new EventEmitter<string>();

  dialogVisible = false;
  showRaw = false;

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['visible']) {
      this.dialogVisible = changes['visible'].currentValue;
      if (!changes['visible'].currentValue) {
        this.showRaw = false;
      }
    }
  }

  onHide(): void {
    this.visibleChange.emit(false);
  }

  formatJson(value: string): string {
    try {
      return JSON.stringify(JSON.parse(value), null, 2);
    } catch {
      return value;
    }
  }

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

  getParagraphs(text: string): string[] {
    if (!text) return [];
    return text.split(/\n\n+/);
  }

  getOperationLabel(): string {
    return this.report ? operationLabel(this.report.operation) : '';
  }

  getOriginLabel(): string {
    return this.report ? originLabel(this.report.origin) : '';
  }

  getOriginSeverity(): 'info' | 'warn' | 'danger' | 'secondary' {
    switch (this.report?.origin) {
      case 'INFRA': return 'danger';
      case 'AMBIGUOUS': return 'warn';
      default: return 'info';
    }
  }
}
