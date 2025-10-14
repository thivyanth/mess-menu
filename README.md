# Mess Menu to Simplenote (GitHub Actions)

Updates a Simplenote note with the latest mess menu from InstiApp on a schedule. The note is rendered in Markdown in Simplenote.

## Files
- `mess.py` - Fetches menu, builds text, upserts Simplenote note
- `requirements.txt` - Python dependencies
- `.github/workflows/mess.yml` - Scheduler and runner

## Configuration
Schedule: every 30 minutes (UTC). Credentials are stored as GitHub Secrets. Edit `.github/workflows/mess.yml` to change:
- `HOSTEL_NAME`
- `NOTE_TITLE`
- `NOTE_TAG`
- `cron` schedule

## Run Locally
```bash
python -m venv .venv
# Windows PowerShell
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:SIMPLENOTE_EMAIL="you@example.com"
$env:SIMPLENOTE_PASSWORD="app-password"
python .\mess.py
```

## Secrets
```bash
gh auth login
gh secret set SIMPLENOTE_EMAIL --body "you@example.com"
gh secret set SIMPLENOTE_PASSWORD --body "APP_PASSWORD"
```

## Markdown in Simplenote
The script sets `systemTags: ["markdown"]` when creating/updating the note so Simplenote renders the content as Markdown. See Simplenote help for Markdown support.



## Notes
- Cron runs in UTC; the script uses Asia/Kolkata to determine the current slot.
- Open Simplenote once so sync is active; then pin the note widget.
- Widget refresh depends on Simplenote sync cadence.

## Trigger Github Action
```bash
gh workflow run
```