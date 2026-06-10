import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { Toast } from 'primeng/toast';
import { Dialog } from 'primeng/dialog';
import { Button } from 'primeng/button';
import { MessageService } from 'primeng/api';
import { SimulationCardComponent } from '../../components/simulation-card/simulation-card.component';
import { SimulationScenario } from '../../core/models/simulation.model';
import { SIMULATION_SCENARIOS } from '../../core/data/simulations.data';
import { ErrorReportService } from '../../core/services/error-report.service';

@Component({
  selector: 'app-simulations',
  standalone: true,
  imports: [Toast, Dialog, Button, SimulationCardComponent],
  templateUrl: './simulations.page.html'
})
export class SimulationsPage {
  scenarios: SimulationScenario[] = SIMULATION_SCENARIOS;
  running = false;
  successVisible = false;
  lastRan: SimulationScenario | null = null;

  private errorReportService = inject(ErrorReportService);
  private messageService = inject(MessageService);
  private router = inject(Router);

  onRun(scenario: SimulationScenario): void {
    this.running = true;
    this.errorReportService.runSimulation(scenario.payload).subscribe({
      next: () => {
        this.lastRan = scenario;
        this.successVisible = true;
        this.running = false;
      },
      error: (err) => {
        this.running = false;
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: err.message || 'Failed to run simulation'
        });
      }
    });
  }

  navigateToReports(): void {
    this.successVisible = false;
    this.router.navigate(['/']);
  }
}
