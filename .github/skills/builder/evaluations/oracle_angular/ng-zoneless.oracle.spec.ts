import { provideZonelessChangeDetection } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { BehaviorSubject } from 'rxjs';
import { NotificationBadge } from './notifications/notification-badge';
import { NotificationFeed } from './notifications/notification-feed';

describe('Oracle NotificationBadge (zoneless)', () => {
  it('refleja cada emisión y libera la suscripción al destruirse', async () => {
    const unread = new BehaviorSubject(0);
    TestBed.configureTestingModule({
      providers: [
        provideZonelessChangeDetection(),
        { provide: NotificationFeed, useValue: { unread$: unread.asObservable(), publish: (n: number) => unread.next(n) } },
      ],
    });
    const fixture = TestBed.createComponent(NotificationBadge);
    await fixture.whenStable();
    const badge = () => (fixture.nativeElement as HTMLElement).querySelector('[data-testid="badge"]')?.textContent?.trim();
    expect(badge()).toBe('0');
    unread.next(3);
    await fixture.whenStable();
    expect(badge()).toBe('3');
    unread.next(7);
    await fixture.whenStable();
    expect(badge()).toBe('7');
    fixture.destroy();
    expect(unread.observed).toBe(false);
  });
});
