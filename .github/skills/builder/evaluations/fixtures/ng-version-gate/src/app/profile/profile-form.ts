import { Component, inject, output } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

export interface Profile {
  name: string;
  email: string;
}

@Component({
  selector: 'app-profile-form',
  imports: [ReactiveFormsModule],
  template: `
    <form [formGroup]="form" (ngSubmit)="submit()">
      <label>Nombre <input data-testid="name" formControlName="name" /></label>
      <label>Correo <input data-testid="email" type="email" formControlName="email" /></label>
      <button type="submit" [disabled]="form.invalid">Guardar</button>
    </form>
  `,
})
export class ProfileForm {
  private readonly fb = inject(NonNullableFormBuilder);
  readonly saved = output<Profile>();

  protected readonly form = this.fb.group({
    name: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
  });

  protected submit(): void {
    if (this.form.invalid) {
      return;
    }
    this.saved.emit(this.form.getRawValue());
  }
}
