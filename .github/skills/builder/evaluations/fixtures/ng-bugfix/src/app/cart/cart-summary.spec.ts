import { TestBed } from '@angular/core/testing';
import { CartSummary } from './cart-summary';

describe('CartSummary', () => {
  it('muestra cero sin líneas', async () => {
    const fixture = TestBed.createComponent(CartSummary);
    await fixture.whenStable();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('[data-testid="total"]')?.textContent).toBe('0');
  });
});
