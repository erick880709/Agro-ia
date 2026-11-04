import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

/** Fuente de notificaciones no leídas. API pública consumida por otros equipos. */
@Injectable({ providedIn: 'root' })
export class NotificationFeed {
  private readonly unread = new BehaviorSubject(0);
  readonly unread$: Observable<number> = this.unread.asObservable();

  publish(count: number): void {
    this.unread.next(count);
  }
}
