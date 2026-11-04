import { Component, OnInit, inject } from '@angular/core';
import { NotificationFeed } from './notification-feed';

@Component({
  selector: 'app-notification-badge',
  template: `<span data-testid="badge">{{ count }}</span>`,
})
export class NotificationBadge implements OnInit {
  private readonly feed = inject(NotificationFeed);
  protected count = 0;

  ngOnInit(): void {
    this.feed.unread$.subscribe((count) => (this.count = count));
  }
}
