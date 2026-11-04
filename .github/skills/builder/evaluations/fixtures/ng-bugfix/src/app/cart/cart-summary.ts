import { Component, computed, input } from '@angular/core';
import { CartLine } from './cart-line.model';

@Component({
  selector: 'app-cart-summary',
  template: `
    <p>Líneas: <span data-testid="count">{{ count() }}</span></p>
    <p>Total: <span data-testid="total">{{ total() }}</span></p>
  `,
})
export class CartSummary {
  readonly lines = input<CartLine[]>([]);
  readonly discountPct = input(0);

  protected readonly count = computed(() => this.lines().length);
  protected readonly total = computed(() => {
    const sum = this.lines().reduce((acc, line) => acc + line.unitPrice, 0);
    return sum - Math.round((sum * this.discountPct()) / 100);
  });
}
