# Train Seat Monitor (Django + Celery + Redis + PostgreSQL)

A small self-hosted monitor for **12571, BLP → ANVT, 13 Dec 2026, 3A, General quota**.
It checks every three hours and sends a Telegram message when numeric availability is **20 or fewer**.

> RailCore is an independent third-party API, not IRCTC or Indian Railways. Confirm availability on IRCTC before booking. The app does not book tickets.

## 1. Prerequisites

- Docker Engine and Docker Compose plugin on your Ubuntu VPS
- A RailCore API key with `availability:read` scope
- A Telegram bot token and your Telegram chat ID

The RailCore free plan currently lists 2,000 requests/month, 300/day and 20/minute; this monitor uses about 240 checks/month at 3-hour intervals. Free plan terms say personal projects/evaluation only. Check current provider pricing/terms before relying on it:
- API docs: https://railcore.tech/docs/api/seat-availability
- Pricing: https://railcore.tech/pricing

## 2. Configure

```bash
cp .env.example .env
vim .env
```

Fill in at least:
- `SECRET_KEY`
- `POSTGRES_PASSWORD`
- `RAILCORE_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Journey is preconfigured:
- Train: `12571`
- From: `BLP` (Balrampur)
- To: `ANVT` (Anand Vihar Terminal)
- Date: `2026-12-13`
- Class: `3A`
- Quota: `GN` (General)
- Threshold: `20`

The route codes are the station codes. Verify them before first use.

## 3. Create Telegram bot

1. Open Telegram and message `@BotFather`.
2. Run `/newbot`, follow the steps, and copy the bot token.
3. Open your new bot and send it `/start`.
4. Get your chat ID by opening this URL in a browser (replace TOKEN):
   `https://api.telegram.org/botTOKEN/getUpdates`
5. Copy `message.chat.id` into `TELEGRAM_CHAT_ID`.

Do not share your bot token or commit `.env` to Git.

## 4. Start services

```bash
docker compose up -d --build
docker compose ps
```

View logs:

```bash
docker compose logs -f worker beat
```

The Beat schedule runs at 00:00, 03:00, 06:00 ... 21:00 in Asia/Kolkata.

## 5. Run first check manually

```bash
docker compose exec worker python manage.py shell -c \
'from monitor.tasks import check_seat_availability; print(check_seat_availability())'
```

If the first successful check already finds 20 or fewer seats, it sends the alert immediately. Otherwise it saves the latest baseline. It alerts once while availability remains at/below 20; if seats later rise above 20, the alert state resets and a later drop to 20 or fewer can alert again.

## 6. API for your React client

- `GET http://YOUR_SERVER:8000/api/status/` — current state, latest check, error, alert state.
- `POST http://YOUR_SERVER:8000/api/check-now/` — queue an immediate check.

Protect the POST endpoint before exposing it to the public internet. Add authentication or restrict it at Nginx/firewall level. Do not expose Django port 8000 publicly in production; proxy it through your existing Nginx and add TLS.

Example response from status:

```json
{
  "train_number": "12571",
  "from": "BLP",
  "to": "ANVT",
  "journey_date": "2026-12-13",
  "class": "3A",
  "quota": "GN",
  "threshold": 20,
  "available_count": 309,
  "alert_sent": false
}
```

## 7. Common commands

```bash
docker compose logs -f web
docker compose logs -f worker
docker compose logs -f beat
docker compose restart worker beat
docker compose down
```

`docker compose down -v` deletes database and Redis volumes. Do not run it unless you intentionally want to delete stored data.

## Notes

- The provider may return an older upstream reading; the response includes `last_updated_at`. Check it in `/api/status/`.
- A missing numeric count is treated as an error, never as zero seats.
- Failed API checks do not generate false low-seat alerts.
- This starter stores only the latest availability reading, not a permanent history.
- Schedule ends only when you stop the stack. Stop it after the journey date if no longer needed.
