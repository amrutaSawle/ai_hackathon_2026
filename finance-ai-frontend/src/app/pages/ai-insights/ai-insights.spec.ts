import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AiInsights } from './ai-insights';

describe('AiInsights', () => {
  let component: AiInsights;
  let fixture: ComponentFixture<AiInsights>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AiInsights],
    }).compileComponents();

    fixture = TestBed.createComponent(AiInsights);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
