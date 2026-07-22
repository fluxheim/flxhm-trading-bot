# FLXHM Trading Bot — Setup

## What you're setting up
A bot that checks AAPL, TSLA, and SPY once a day, trades on a 20/50-day moving
average crossover, executes on your Alpaca **paper** account (fake money), and
logs results for the dashboard to read. Fully automated once it's running.

## Steps

### 1. Create a GitHub repo
- New repo (public or private, either works) — call it something like `flxhm-trading-bot`
- Upload these 3 files, keeping the folder structure:
  - `bot.py`
  - `.github/workflows/daily-trade.yml`
  - `data/history.json`

### 2. Add your Alpaca keys as GitHub Secrets
In your repo: **Settings → Secrets and variables → Actions → New repository secret**
- Add `ALPACA_API_KEY` = your Alpaca paper API key
- Add `ALPACA_SECRET_KEY` = your Alpaca paper secret key

(Get these from your Alpaca dashboard → paper trading → API Keys.)

### 3. Turn on Actions
Go to the **Actions** tab in your repo → you should see "Daily Trading Bot Run"
→ click **Enable workflow** if it asks.

### 4. Test it manually (don't wait for the schedule)
Actions tab → "Daily Trading Bot Run" → **Run workflow** button → run it once
manually to confirm it works. Check the run logs for errors, and check that
`data/history.json` got updated with a new entry after it finishes.

### 5. Connect the dashboard
- Go to `data/history.json` in your repo on GitHub → click **Raw**
- Copy that URL (it'll look like `https://raw.githubusercontent.com/YOURNAME/flxhm-trading-bot/main/data/history.json`)
- Paste it into the dashboard artifact's input box → hit Connect

From here it runs itself daily on weekdays after market close (9:05pm UTC /
4:05pm ET). Refresh the dashboard anytime to see the latest state.

## Notes
- Everything trades on Alpaca's **paper** account — no real money, ever, unless you
  deliberately swap the base URL to the live trading endpoint (don't do this
  without a lot more testing).
- Starts with 1 share per trade to keep things simple. Easy to adjust `QTY` in `bot.py`.
- History caps at the last 180 runs so the file doesn't grow forever.
