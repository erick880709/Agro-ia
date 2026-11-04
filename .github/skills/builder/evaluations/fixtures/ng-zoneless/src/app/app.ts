import { Component } from '@angular/core';
import { NotificationBadge } from './notifications/notification-badge';

@Component({
  selector: 'app-root',
  imports: [NotificationBadge],
  template: `<app-notification-badge />`,
})
export class App {}
