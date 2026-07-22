import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { CopilotComponent } from './copilot';
import { CopilotService } from '../../services/copilot.service';

describe('CopilotComponent', () => {
  let component: CopilotComponent;
  let fixture: ComponentFixture<CopilotComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CopilotComponent],
      providers: [{
        provide: CopilotService,
        useValue: {
          sendMessage: () => of({
            user_id: 1,
            question: 'What is my top category?',
            intent: 'TOP_CATEGORY',
            answer: 'Flights is your top category.',
            data: { category: 'Flights', amount: 72000, percentage: 40.11 },
            suggestions: [],
            sources: [],
            generated_by: 'FINANCE_COPILOT_RULES_V1'
          })
        }
      }]
    }).compileComponents();

    fixture = TestBed.createComponent(CopilotComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
