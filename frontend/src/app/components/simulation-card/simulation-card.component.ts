import { Component, EventEmitter, Input, Output } from '@angular/core';
import { Card } from 'primeng/card';
import { Tag } from 'primeng/tag';
import { Button } from 'primeng/button';
import { SimulationScenario } from '../../core/models/simulation.model';

@Component({
  selector: 'app-simulation-card',
  standalone: true,
  imports: [Card, Tag, Button],
  templateUrl: './simulation-card.component.html'
})
export class SimulationCardComponent {
  @Input({ required: true }) scenario!: SimulationScenario;
  @Input() disabled = false;
  @Output() run = new EventEmitter<SimulationScenario>();

  getTagSeverity(): 'info' | 'success' | 'danger' | 'warning' {
    switch (this.scenario.tag) {
      case 'Cache HIT':
        return 'success';
      case 'Error':
        return 'danger';
      case 'Contract':
        return 'warning';
      default:
        return 'info';
    }
  }
}
