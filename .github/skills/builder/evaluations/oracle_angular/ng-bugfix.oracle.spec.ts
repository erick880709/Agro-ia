import { TestBed } from '@angular/core/testing';
import { CartSummary } from './cart/cart-summary';

async function render(lines: { sku: string; unitPrice: number; quantity: number }[], discountPct: number) {
  const fixture = TestBed.createComponent(CartSummary);
  fixture.componentRef.setInput('lines', lines);
  fixture.componentRef.setInput('discountPct', discountPct);
  await fixture.whenStable();
  const el: HTMLElement = fixture.nativeElement;
  return {
    total: el.querySelector('[data-testid="total"]')?.textContent?.trim(),
    count: el.querySelector('[data-testid="count"]')?.textContent?.trim(),
  };
}

describe('Oracle CartSummary', () => {
  it('multiplica por cantidad y aplica el descuento sobre la suma', async () => {
    const r = await render([{ sku: 'A', unitPrice: 1000, quantity: 3 }, { sku: 'B', unitPrice: 500, quantity: 2 }], 10);
    expect(r.total).toBe('3600');
    expect(r.count).toBe('2');
  });
  it('sin descuento', async () => {
    expect((await render([{ sku: 'A', unitPrice: 250, quantity: 4 }], 0)).total).toBe('1000');
  });
  it('lista vacía', async () => {
    const r = await render([], 20);
    expect(r.total).toBe('0');
    expect(r.count).toBe('0');
  });
  it('redondea el descuento al centavo', async () => {
    expect((await render([{ sku: 'A', unitPrice: 333, quantity: 1 }], 10)).total).toBe('300');
  });
  it('reacciona a cambios de entrada', async () => {
    const fixture = TestBed.createComponent(CartSummary);
    fixture.componentRef.setInput('lines', [{ sku: 'A', unitPrice: 100, quantity: 1 }]);
    await fixture.whenStable();
    fixture.componentRef.setInput('lines', [{ sku: 'A', unitPrice: 100, quantity: 5 }]);
    await fixture.whenStable();
    expect((fixture.nativeElement as HTMLElement).querySelector('[data-testid="total"]')?.textContent?.trim()).toBe('500');
  });
});
