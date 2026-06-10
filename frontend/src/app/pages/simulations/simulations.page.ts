import { Component } from '@angular/core';
import { SimulationCardComponent } from '../../components/simulation-card/simulation-card.component';
import { SimulationScenario } from '../../core/models/simulation.model';

@Component({
  selector: 'app-simulations',
  standalone: true,
  imports: [SimulationCardComponent],
  templateUrl: './simulations.page.html'
})
export class SimulationsPage {
  testScenario: SimulationScenario = {
    id: 1,
    title: 'Cache MISS — RefLab FHIR Bundle',
    description: 'First request with ONC001 (non-performable exam).',
    tag: 'Cache MISS',
    payload: {}
  };
}
