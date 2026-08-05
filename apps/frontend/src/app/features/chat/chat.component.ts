import { Component } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { FormsModule } from '@angular/forms';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [
    MatCardModule, MatInputModule, MatButtonModule,
    MatIconModule, MatListModule, FormsModule,
  ],
  template: `
    <h1>Agente IA — Consultas Agronómicas</h1>

    <mat-card class="chat-container">
      <mat-card-content>
        <div class="messages">
          @for (msg of messages; track $index) {
            <div [class]="'message ' + msg.role">
              <strong>{{ msg.role === 'user' ? '👤 Tú' : '🤖 AgroIA' }}:</strong>
              <p>{{ msg.content }}</p>
            </div>
          }
        </div>
      </mat-card-content>
      <mat-card-actions class="chat-input">
        <mat-form-field appearance="outline" class="input-field">
          <input matInput [(ngModel)]="newMessage" placeholder="Pregunta sobre cultivos, suelo, recomendaciones..."
                 (keyup.enter)="sendMessage()">
        </mat-form-field>
        <button mat-fab color="primary" (click)="sendMessage()" [disabled]="!newMessage.trim()">
          <mat-icon>send</mat-icon>
        </button>
      </mat-card-actions>
    </mat-card>
  `,
  styles: [
    `
      h1 { margin-bottom: 24px; color: #2e7d32; }
      .chat-container { max-width: 700px; display: flex; flex-direction: column; }
      .messages { flex: 1; min-height: 400px; max-height: 500px; overflow-y: auto; padding: 16px; }
      .message { margin-bottom: 12px; padding: 8px 12px; border-radius: 8px; }
      .message.user { background: #e3f2fd; text-align: right; }
      .message.assistant { background: #f1f8e9; }
      .chat-input { display: flex; gap: 12px; padding: 16px; align-items: center; }
      .input-field { flex: 1; }
    `,
  ],
})
export class ChatComponent {
  messages: ChatMessage[] = [
    { role: 'assistant', content: '¡Hola! Soy el agente IA de AgroIA. Puedo ayudarte con consultas sobre cultivos, análisis de suelo, recomendaciones agronómicas y más. ¿En qué puedo ayudarte?' },
  ];
  newMessage = '';

  sendMessage(): void {
    const text = this.newMessage.trim();
    if (!text) return;

    this.messages.push({ role: 'user', content: text });
    this.newMessage = '';

    // Simular respuesta del agente RAG
    setTimeout(() => {
      this.messages.push({
        role: 'assistant',
        content: 'Gracias por tu consulta. Como agente IA de AgroIA, estoy procesando información de la base de conocimiento agronómico. Para consultas específicas sobre cultivos y suelo, te recomiendo usar la sección de Recomendaciones donde obtendrás un análisis basado en ML + reglas agronómicas de UPRA/Cenicafé.',
      });
    }, 1000);
  }
}
