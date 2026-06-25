/**
 * alerts.ts — minimal alert sink for monitor.ts.
 * Webhook (Slack/Discord/Telegram) if ALERT_WEBHOOK is set, else logs to stdout.
 * One-line JSON per alert, matching the contract in skill/monitoring.md §3.
 */
export type Level = "GREEN" | "YELLOW" | "RED";

export interface Alert {
  ts: string;
  level: Level;
  message: string;
}

export interface PositionSignal {
  position: string;
  lowerBinId: number;
  upperBinId: number;
  activeBinId: number;
  level: Level;
  drift: number;
  feeBps?: number;
}

export class WebhookAlerts {
  constructor(private webhook?: string) {}

  async send(a: Alert): Promise<void> {
    const line = `${a.ts} | ${a.level} | ${a.message}`;
    if (this.webhook) {
      try {
        await fetch(this.webhook, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: line }), // Slack-style; Discord accepts {content}
        });
      } catch (e) {
        console.error(`[alerts] webhook failed, falling back to log:`, e);
        console.log(line);
      }
    } else {
      console.log(line);
    }
  }
}
