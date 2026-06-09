import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ErrorReport } from '../models/error-report.model';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ErrorReportService {
  private apiBase = environment.apiBase;

  constructor(private http: HttpClient) {}

  getReports(): Observable<ErrorReport[]> {
    return this.http.get<ErrorReport[]>(`${this.apiBase}/error-reports`);
  }

  confirmFix(id: string): Observable<{ status: string }> {
    return this.http.post<{ status: string }>(`${this.apiBase}/error-reports/${id}/confirm-fix`, {});
  }

  dismiss(id: string): Observable<void> {
    return this.http.post<void>(`${this.apiBase}/error-reports/${id}/dismiss`, {});
  }
}
