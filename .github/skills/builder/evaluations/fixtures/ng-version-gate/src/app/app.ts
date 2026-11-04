import { Component } from '@angular/core';
import { ProfileForm } from './profile/profile-form';

@Component({
  selector: 'app-root',
  imports: [ProfileForm],
  template: `<app-profile-form (saved)="onSaved($event)" />`,
})
export class App {
  onSaved(value: unknown): void {
    console.log(value);
  }
}
