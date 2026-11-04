import { Component } from '@angular/core';
import { CartSummary } from './cart/cart-summary';

@Component({
  selector: 'app-root',
  imports: [CartSummary],
  template: `<app-cart-summary [lines]="lines" [discountPct]="10" />`,
})
export class App {
  protected readonly lines = [
    { sku: 'A-1', unitPrice: 1000, quantity: 3 },
    { sku: 'B-2', unitPrice: 500, quantity: 2 },
  ];
}
