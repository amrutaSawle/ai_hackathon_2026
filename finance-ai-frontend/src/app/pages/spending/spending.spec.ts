import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Spending } from './spending';

describe('Spending', () => {
  let component: Spending;
  let fixture: ComponentFixture<Spending>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Spending],
    }).compileComponents();

    fixture = TestBed.createComponent(Spending);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
