# NI ED Waiting Times → Telegram Bot

This script polls the NI Hospital Waiting Times ArcGIS FeatureServer and posts formatted updates to a Telegram channel whenever the data changes.

## Files
- `app.py` — main script (polls every 5 minutes by default)
- `requirements.txt` — Python dependencies

## Prerequisites
- Python 3.9+
- A Telegram Bot token and a target channel/chat id
- Internet access

## Install
```bash
pip install -r requirements.txt
```

## Configure
The script is already configured to:
- Use the ArcGIS FeatureServer for NI Hospital Waiting Times
- Post to your provided Telegram `chat_id` using your `bot` token
- Poll every 5 minutes

If you want to change the polling interval, edit `POLL_SECONDS` at the top of `app.py`.

## Run
```bash
python app.py
```
Leave the process running. It prints a message when a change is detected and an update is sent.

## How it works
1. Queries the ArcGIS FeatureServer for records where `Status <> 'Closed'`.
2. Extracts hospital name, status, and wait time (minutes).
3. Sorts the list by wait time (descending) and formats a monospaced message with severity emojis.
4. Computes a digest (hash) of the current snapshot. If unchanged from the last post, skip sending.
5. Sends the message to Telegram when the snapshot changes.

## Windows Task Scheduler (optional)
If you prefer periodic runs rather than a persistent process:
1. Create a batch file `run_bot.bat`:
   ```bat
   @echo off
   cd /d "%~dp0"
   python app.py
   ```
2. Open Task Scheduler → Create Task…
3. Triggers → New… → Repeat task every: 5 minutes → for a duration of: Indefinitely
4. Actions → New… → Start a program → Program/script: `run_bot.bat`
5. Conditions/Settings: adjust as needed (Run whether user is logged on or not, etc.)

## Notes
- Source: ArcGIS FeatureServer used by NI Direct dashboard.
- If the raw field `WaitTimeInt` is ever unavailable, the script falls back to the average wait per hospital.
- Keep your bot token secure. Since this is local-only, it is embedded directly in `app.py` per your request.
