import importlib.util
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'evaluate_builder.py'
spec = importlib.util.spec_from_file_location('evaluate_builder_ng', SCRIPT)
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)

CASES = ('ng-bugfix', 'ng-zoneless', 'ng-version-gate', 'ng-interceptor')
HAS_DEPS = shutil.which('node') is not None and harness.requirement_available('angular-deps')
SKIP = 'Requires node and BUILDER_ANGULAR_DEPS (see references/behavioral-evaluation.md)'

CART_OK = '''import { Component, computed, input } from '@angular/core';
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
    const sum = this.lines().reduce((acc, line) => acc + line.unitPrice * line.quantity, 0);
    return sum - Math.round((sum * this.discountPct()) / 100);
  });
}
'''
CART_CHANGES_NEIGHBOUR = CART_OK.replace(
    'computed(() => this.lines().length)',
    'computed(() => this.lines().reduce((acc, line) => acc + line.quantity, 0))')

BADGE_OK = '''import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { NotificationFeed } from './notification-feed';

@Component({
  selector: 'app-notification-badge',
  template: `<span data-testid="badge">{{ count() }}</span>`,
})
export class NotificationBadge {
  protected readonly count = toSignal(inject(NotificationFeed).unread$, { initialValue: 0 });
}
'''
BADGE_LEAKS = '''import { Component, OnInit, inject, signal } from '@angular/core';
import { NotificationFeed } from './notification-feed';

@Component({
  selector: 'app-notification-badge',
  template: `<span data-testid="badge">{{ count() }}</span>`,
})
export class NotificationBadge implements OnInit {
  private readonly feed = inject(NotificationFeed);
  protected readonly count = signal(0);

  ngOnInit(): void {
    this.feed.unread$.subscribe((count) => this.count.set(count));
  }
}
'''
BADGE_STALE = '''import { Component, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { NotificationFeed } from './notification-feed';

@Component({
  selector: 'app-notification-badge',
  template: `<span data-testid="badge">{{ count }}</span>`,
})
export class NotificationBadge {
  protected count = 0;

  constructor() {
    inject(NotificationFeed).unread$.pipe(takeUntilDestroyed()).subscribe((count) => (this.count = count));
  }
}
'''

PROFILE_OK = '''import { Component, inject, output } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

export interface Profile {
  name: string;
  email: string;
  phone: string;
}

@Component({
  selector: 'app-profile-form',
  imports: [ReactiveFormsModule],
  template: `
    <form [formGroup]="form" (ngSubmit)="submit()">
      <label>Nombre <input data-testid="name" formControlName="name" /></label>
      <label>Correo <input data-testid="email" type="email" formControlName="email" /></label>
      <label>Teléfono <input data-testid="phone" type="tel" formControlName="phone" /></label>
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
    phone: ['', [Validators.required, Validators.pattern(/^\\d{10}$/)]],
  });

  protected submit(): void {
    if (this.form.invalid) {
      return;
    }
    this.saved.emit(this.form.getRawValue());
  }
}
'''
PROFILE_EXPERIMENTAL = PROFILE_OK.replace(
    "import { NonNullableFormBuilder",
    "import { form as signalForm } from '@angular/forms/signals';\nimport { NonNullableFormBuilder").replace(
    'protected submit(): void {', 'protected readonly unused = signalForm;\n\n  protected submit(): void {')
PROFILE_LOOSE = PROFILE_OK.replace('Validators.pattern(/^\\d{10}$/)', 'Validators.minLength(10)')

INTERCEPTOR_OK = '''import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { API_BASE_URL } from './api-base-url';
import { AuthSession } from './auth-session';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = inject(AuthSession).token();
  const apiOrigin = new URL(inject(API_BASE_URL)).origin;
  if (!token || !isOwnApi(req.url, apiOrigin)) {
    return next(req);
  }
  return next(req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }));
};

function isOwnApi(url: string, apiOrigin: string): boolean {
  if (url === '/api' || url.startsWith('/api/')) {
    return true;
  }
  if (!/^https?:\\/\\//i.test(url)) {
    return false;
  }
  try {
    return new URL(url).origin === apiOrigin;
  } catch {
    return false;
  }
}
'''
INTERCEPTOR_PREFIX = '''import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { API_BASE_URL } from './api-base-url';
import { AuthSession } from './auth-session';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = inject(AuthSession).token();
  const base = inject(API_BASE_URL);
  if (!token || !(req.url.startsWith('/api') || req.url.startsWith(base))) {
    return next(req);
  }
  return next(req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }));
};
'''


class AngularCaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def prepare(self, case):
        path = self.root / case
        harness.prepare(case, path)
        return path

    def write(self, path, relative, text):
        (path / relative).write_text(text, encoding='utf-8')

    def test_prepare_never_copies_oracles_or_dependencies(self):
        for case in CASES:
            with self.subTest(case=case):
                path = self.prepare(case)
                names = {p.name for p in path.rglob('*')}
                self.assertIn('TASK.md', names)
                self.assertFalse(any('oracle' in n for n in names))
                self.assertNotIn('node_modules', names)

    def test_missing_dependencies_are_an_invalid_environment(self):
        path = self.prepare('ng-bugfix')
        with patch.dict(os.environ, {'BUILDER_ANGULAR_DEPS': ''}):
            with self.assertRaises(ValueError):
                harness.check('ng-bugfix', path)

    @unittest.skipUnless(HAS_DEPS, SKIP)
    def test_ng_bugfix(self):
        path = self.prepare('ng-bugfix')
        self.assertFalse(harness.check('ng-bugfix', path)['passed'])
        self.write(path, 'src/app/cart/cart-summary.ts', CART_CHANGES_NEIGHBOUR)
        self.assertFalse(harness.check('ng-bugfix', path)['passed'])
        self.write(path, 'src/app/cart/cart-summary.ts', CART_OK)
        result = harness.check('ng-bugfix', path)
        self.assertTrue(result['passed'], result)

    @unittest.skipUnless(HAS_DEPS, SKIP)
    def test_ng_zoneless(self):
        path = self.prepare('ng-zoneless')
        self.assertFalse(harness.check('ng-zoneless', path)['passed'])
        for wrong in (BADGE_LEAKS, BADGE_STALE):
            self.write(path, 'src/app/notifications/notification-badge.ts', wrong)
            self.assertFalse(harness.check('ng-zoneless', path)['passed'])
        self.write(path, 'src/app/notifications/notification-badge.ts', BADGE_OK)
        result = harness.check('ng-zoneless', path)
        self.assertTrue(result['passed'], result)

    @unittest.skipUnless(HAS_DEPS, SKIP)
    def test_ng_version_gate(self):
        path = self.prepare('ng-version-gate')
        self.assertFalse(harness.check('ng-version-gate', path)['passed'])
        for wrong in (PROFILE_EXPERIMENTAL, PROFILE_LOOSE):
            self.write(path, 'src/app/profile/profile-form.ts', wrong)
            self.assertFalse(harness.check('ng-version-gate', path)['passed'])
        self.write(path, 'src/app/profile/profile-form.ts', PROFILE_OK)
        result = harness.check('ng-version-gate', path)
        self.assertTrue(result['passed'], result)

    @unittest.skipUnless(HAS_DEPS, SKIP)
    def test_ng_interceptor(self):
        path = self.prepare('ng-interceptor')
        self.assertFalse(harness.check('ng-interceptor', path)['passed'])
        self.write(path, 'src/app/core/auth-interceptor.ts', INTERCEPTOR_PREFIX)
        self.assertFalse(harness.check('ng-interceptor', path)['passed'])
        self.write(path, 'src/app/core/auth-interceptor.ts', INTERCEPTOR_OK)
        result = harness.check('ng-interceptor', path)
        self.assertTrue(result['passed'], result)
        config = (path / 'src/app/app.config.ts').read_text(encoding='utf-8')
        self.write(path, 'src/app/app.config.ts', config.replace('withInterceptors([authInterceptor])', ''))
        self.assertFalse(harness.check('ng-interceptor', path)['passed'])


if __name__ == '__main__':
    unittest.main()
