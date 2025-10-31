# Strava Integration Troubleshooting Guide

This guide helps you resolve common issues with the Strava integration.

## Table of Contents

1. [Authentication Issues](#authentication-issues)
2. [API Rate Limiting](#api-rate-limiting)
3. [Network Errors](#network-errors)
4. [Import Errors](#import-errors)
5. [File Export Errors](#file-export-errors)
6. [Missing Data Issues](#missing-data-issues)
7. [Auto-Link Not Working](#auto-link-not-working)
8. [Performance Issues](#performance-issues)
9. [Configuration Problems](#configuration-problems)

---

## Authentication Issues

### Problem: "You are not authenticated with Strava"

**Symptoms**:

```
You are not authenticated with Strava.
Please run: poetry run onsendo strava auth
```

**Solution**:

1. Run the authentication command:

   ```bash
   poetry run onsendo strava auth
   ```

2. Your browser will open to Strava's authorization page
3. Click "Authorize" to grant access
4. Token will be saved to `local/strava/token.json`

**Still not working?**

- Check that `.env` file has correct `STRAVA_CLIENT_ID` and `STRAVA_CLIENT_SECRET`
- Verify redirect URI matches: `http://localhost:8080/strava/callback`
- Check that port 8080 is not in use by another application

---

### Problem: "Token expired" or authentication fails

**Symptoms**:

```
Error: Authentication failed
```

**Solution**:

1. Force re-authentication:

   ```bash
   poetry run onsendo strava auth --reauth
   ```

2. Delete old token and re-authenticate:

   ```bash
   rm local/strava/token.json
   poetry run onsendo strava auth
   ```

**Root Cause**: Strava access tokens expire after 6 hours. The system automatically refreshes tokens, but if the refresh token is also invalid, re-authentication is required.

---

### Problem: Browser doesn't open during auth

**Symptoms**:

```
Opening browser for authentication...
[Browser doesn't open]
```

**Solution**:

1. Check the terminal output for the authorization URL
2. Manually copy and paste the URL into your browser
3. After authorizing, you'll be redirected to `http://localhost:8080/strava/callback`
4. The CLI will automatically detect the callback and save the token

**Alternative**: If running on a headless server, you can:

1. Run auth on your local machine
2. Copy `local/strava/token.json` to the server

---

## API Rate Limiting

### Problem: "Rate limit exceeded"

**Symptoms**:

```
Error: Rate limit exceeded. Waiting 900 seconds...
```

**Strava Rate Limits**:

- **15-minute window**: 100 requests
- **Daily window**: 1000 requests

**Solution**:

1. **Wait it out**: The system will automatically wait and retry
2. **Reduce sync frequency**: Use longer `--days` intervals
3. **Download only needed formats**: Use `--format gpx` instead of `all`

**Monitoring Rate Limits**:

```bash
poetry run onsendo strava status --verbose
```

Output shows:

```
Rate Limits:
  15-min usage: 45/100
  Daily usage: 234/1000
```

**Best Practices**:

- Sync once per day with `--days 1`
- Use dry-run first to see how many activities will be synced
- Download in batches instead of all at once

---

## Network Errors

### Problem: "Connection timeout" or "Network error"

**Symptoms**:

```
Error fetching activity: Connection timeout
```

**Solution**:

1. **Check internet connection**: Verify you can access `https://www.strava.com`
2. **Retry**: The system has built-in retry logic with exponential backoff
3. **Check firewall**: Ensure outbound HTTPS is allowed

**Automatic Retry**: The client automatically retries failed requests up to 3 times with exponential backoff (1s, 2s, 4s).

---

### Problem: "SSL certificate verification failed"

**Symptoms**:

```
Error: SSL: CERTIFICATE_VERIFY_FAILED
```

**Solution**:

1. **macOS**: Install certificates:

   ```bash
   /Applications/Python\ 3.12/Install\ Certificates.command
   ```

2. **Linux**: Update CA certificates:

   ```bash
   sudo apt-get update && sudo apt-get install ca-certificates
   ```

3. **Corporate proxy**: Configure proxy settings in `.env`:

   ```bash
   HTTPS_PROXY=http://proxy.company.com:8080
   ```

---

## Import Errors

### Problem: "Failed to import as exercise"

**Symptoms**:

```
✓ Downloaded: activity.gpx
✗ Import failed: Invalid data
```

**Common Causes**:

1. **Missing GPS data**: Activity has no GPS route (indoor activities)
2. **Corrupted stream data**: API returned incomplete data
3. **Unsupported activity type**: Activity type not mapped

**Solution**:

**1. Check activity details**:

```bash
poetry run onsendo strava download <activity_id>
# Open the JSON file and inspect the data
```

**2. Import as heart rate instead** (if no GPS):

```bash
poetry run onsendo strava download <activity_id> --import-hr
```

**3. Check logs** for detailed error:

```bash
# Logs show the full stack trace
tail -f logs/onsendo.log
```

---

### Problem: "Activity type not recognized"

**Symptoms**:

```
✓ Downloaded
✗ Import failed: Unknown activity type 'VirtualRun'
```

**Solution**:
Activity types are mapped in `src/lib/strava_converter.py`. If a type is missing:

1. **Check supported types**:

   ```python
   # See StravaActivityTypeMapper.TYPE_MAPPING
   Run, Ride, Hike, Swim, Yoga, WeightTraining, etc.
   ```

2. **Unsupported types default to `OTHER`**: The activity will still import, just with generic type.

3. **Request support**: Open an issue with the activity type you need.

---

## File Export Errors

### Problem: "Failed to write GPX file"

**Symptoms**:

```
Error exporting files: Permission denied
```

**Solution**:

1. **Check directory permissions**:

   ```bash
   ls -la data/strava/activities/
   chmod 755 data/strava/activities/
   ```

2. **Check disk space**:

   ```bash
   df -h
   ```

3. **Create directory manually**:

   ```bash
   mkdir -p data/strava/activities
   ```

---

### Problem: "GPX export requires 'time' and 'latlng' streams"

**Symptoms**:

```
Error: GPX export requires 'time' and 'latlng' streams
```

**Root Cause**: Activity has no GPS data (e.g., indoor treadmill run).

**Solution**:

1. **Export JSON instead**:

   ```bash
   poetry run onsendo strava download <id> --format json
   ```

2. **Check if activity has GPS** in Strava web interface

3. **Import only heart rate** if available:

   ```bash
   poetry run onsendo strava download <id> --format hr_csv --import-hr
   ```

---

## Missing Data Issues

### Problem: Activity downloads but has no heart rate data

**Symptoms**:

```
✓ Downloaded: activity.gpx
⚠ Activity does not have heart rate data
```

**Root Cause**: Activity was recorded without a heart rate monitor.

**Solution**:

- This is expected if you didn't record HR during the activity
- Only activities with HR sensors will have heart rate data
- Check Strava activity on web to verify HR availability

---

### Problem: Downloaded file is empty or corrupted

**Symptoms**:

```
✓ Downloaded: activity.gpx
[File is 0 bytes or unreadable]
```

**Solution**:

1. **Re-download**:

   ```bash
   rm data/strava/activities/activity.gpx
   poetry run onsendo strava download <id>
   ```

2. **Check Strava API status**: Visit <https://status.strava.com/>

3. **Verify activity exists**:

   ```bash
   poetry run onsendo strava browse --days 30
   ```

---

## Auto-Link Not Working

### Problem: "No nearby visits found"

**Symptoms**:

```
Linking to visit...
  No nearby visits found (±2 hours)
```

**Root Cause**: No onsen visits within ±2 hours of activity start time.

**Solution**:

1. **Check visit times**:

   ```bash
   poetry run onsendo visit list
   ```

2. **Verify activity time**:

   ```bash
   poetry run onsendo strava download <id>
   # Check "Date:" field
   ```

3. **Manual link if outside window**:

   ```bash
   poetry run onsendo strava download <id> --import
   poetry run onsendo strava link --exercise <ex_id> --visit <visit_id>
   ```

**Time Window**: Auto-link searches ±2 hours from activity start time. If your onsen visit was >2 hours before/after, manual linking is required.

---

### Problem: Auto-link chooses wrong visit

**Symptoms**:

```
Using suggestion: Visit ID 15
[But you wanted visit ID 14]
```

**Root Cause**: Auto-link uses closest visit by timestamp.

**Solution**:

1. **Use manual linking**:

   ```bash
   # Import without auto-link
   poetry run onsendo strava download <id> --import

   # Link to correct visit
   poetry run onsendo strava link --exercise <ex_id> --visit <correct_visit_id>
   ```

2. **Unlink and re-link** if already linked:

   ```bash
   # Unlink
   poetry run onsendo exercise unlink <ex_id>

   # Link to correct visit
   poetry run onsendo strava link --exercise <ex_id> --visit <visit_id>
   ```

---

## Performance Issues

### Problem: Sync is very slow

**Symptoms**:

```
[1/100] Activity 1... [takes 10+ seconds per activity]
```

**Causes**:

1. **Large number of activities**: 100+ activities
2. **Multiple formats**: Exporting to GPX + JSON + CSV
3. **Network latency**: Slow connection to Strava API

**Solutions**:

1. **Use single format**:

   ```bash
   make strava-sync DAYS=30 FORMAT=gpx IMPORT=true
   ```

2. **Sync in batches**:

   ```bash
   # Week 1
   make strava-sync DAYS=7 IMPORT=true

   # Week 2
   make strava-sync DAYS=14 IMPORT=true
   ```

3. **Skip already downloaded** (automatic):
   - Sync detects existing GPX files and skips them
   - Use `--auto-import` to force re-processing

---

### Problem: Interactive browser is laggy

**Symptoms**:

- Slow to fetch pages
- Slow to display activity details

**Solution**:

1. **Reduce page size**:

   ```
   Activities per page (default 10): 5
   ```

2. **Use non-interactive commands** for batch operations:

   ```bash
   make strava-sync DAYS=7 IMPORT=true LINK=true
   ```

3. **Check network connection**: Interactive browser makes real-time API calls

---

## Configuration Problems

### Problem: ".env file not found" or "Missing configuration"

**Symptoms**:

```
Error loading Strava settings: Missing STRAVA_CLIENT_ID
```

**Solution**:

1. **Create .env file** from template:

   ```bash
   cp .env.example .env
   ```

2. **Add Strava credentials** to `.env`:

   ```bash
   STRAVA_CLIENT_ID=your_client_id_here
   STRAVA_CLIENT_SECRET=your_client_secret_here
   STRAVA_REDIRECT_URI=http://localhost:8080/strava/callback
   STRAVA_TOKEN_PATH=local/strava/token.json
   ```

3. **Get Strava API credentials**:
   - Go to <https://www.strava.com/settings/api>
   - Create an application
   - Copy Client ID and Client Secret

---

### Problem: "Invalid redirect URI"

**Symptoms**:

```
Error: redirect_uri_mismatch
```

**Solution**:

1. **Check Strava API settings**:
   - Go to <https://www.strava.com/settings/api>
   - Authorization Callback Domain: `localhost`

2. **Verify .env setting**:

   ```bash
   STRAVA_REDIRECT_URI=http://localhost:8080/strava/callback
   ```

3. **Must match exactly**: Including `http://` and port `:8080`

---

### Problem: Token file permissions error

**Symptoms**:

```
Error: Permission denied: local/strava/token.json
```

**Solution**:

1. **Fix permissions**:

   ```bash
   chmod 600 local/strava/token.json
   ```

2. **Create directory** if missing:

   ```bash
   mkdir -p local/strava
   chmod 700 local/strava
   ```

---

## Getting Help

### Check Logs

Detailed error logs are available in `logs/onsendo.log`:

```bash
tail -f logs/onsendo.log
```

### Verify Installation

Check that all dependencies are installed:

```bash
poetry install
poetry run python -c "from src.lib.strava_client import StravaClient; print('OK')"
```

### Check Strava API Status

Visit <https://status.strava.com/> to see if Strava is experiencing issues.

### Report Issues

If you're still having problems:

1. Check existing issues: <https://github.com/anthropics/onsendo/issues>
2. Create a new issue with:
   - Full error message
   - Steps to reproduce
   - Logs (remove sensitive data like tokens)
   - System info (OS, Python version)

---

## Common Workflows Checklist

### First-Time Setup

- [ ] Create Strava API application at <https://www.strava.com/settings/api>
- [ ] Copy `.env.example` to `.env`
- [ ] Add `STRAVA_CLIENT_ID` and `STRAVA_CLIENT_SECRET` to `.env`
- [ ] Run `poetry run onsendo strava auth`
- [ ] Verify with `poetry run onsendo strava status`

### Daily Sync

- [ ] Run `make strava-sync DAYS=1 IMPORT=true LINK=true`
- [ ] Or use cron job for automation

### Bulk Import

- [ ] Test with dry-run: `make strava-sync DAYS=30 DRY_RUN=true`
- [ ] Review output
- [ ] Run actual sync: `make strava-sync DAYS=30 IMPORT=true LINK=true`
- [ ] Verify imports: `poetry run onsendo exercise list --date-range <start>,<end>`

---

## Performance Tips

1. **Use GPX only** for most cases: `--format gpx`
2. **Sync frequently** in small batches: `--days 1` daily
3. **Use auto-link** to save time: `--auto-link`
4. **Monitor rate limits**: `poetry run onsendo strava status -v`
5. **Cache activities**: Files are automatically deduplicated

---

## Security Best Practices

1. **Never commit tokens**: `.gitignore` includes `local/` and `token.json`
2. **Secure token file**: Permissions should be `600` (owner read/write only)
3. **Rotate credentials** if compromised
4. **Use separate Strava app** for development vs production
5. **Review API scopes**: Only grant necessary permissions

---

**Last Updated**: 2025-10-24
**Strava API Version**: v3
