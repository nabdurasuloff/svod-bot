#!/usr/bin/env bash
# Ishlatish: TELEGRAM_TOKEN=... WEBHOOK_SECRET=... ./scripts/set_webhook.sh https://svod-bot-xxxx.a.run.app
set -e
curl -sS "https://api.telegram.org/bot${TELEGRAM_TOKEN}/setWebhook" \
  -d "url=$1/webhook" -d "secret_token=${WEBHOOK_SECRET}" -d "allowed_updates=[\"message\"]"
