import { Component } from '@angular/core';
import { Toast } from 'primeng/toast';
import { ErrorListContainer } from '../../containers/error-list/error-list.container';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [Toast, ErrorListContainer],
  templateUrl: './dashboard.page.html'
})
export class DashboardPage {}
