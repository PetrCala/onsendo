# Strava Integration - Example Workflows

This document provides real-world examples and workflows for using the Strava integration with Onsendo.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Daily Onsen Visit Workflow](#daily-onsen-visit-workflow)
3. [Weekly Batch Processing](#weekly-batch-processing)
4. [Post-Vacation Catch-Up](#post-vacation-catch-up)
5. [Selective Activity Import](#selective-activity-import)
6. [Manual Review and Linking](#manual-review-and-linking)
7. [Automation with Cron](#automation-with-cron)
8. [Data Backup and Archival](#data-backup-and-archival)

---

## Quick Start

### First-Time Setup (5 minutes)

1. **Create Strava API application**:

   ```
   Visit: https://www.strava.com/settings/api
   Create new application:
     - Application Name: Onsendo
     - Category: Data Importer
     - Website: http://localhost
     - Authorization Callback Domain: localhost
   ```

2. **Configure Onsendo**:

   ```bash
   # Copy environment template
   cp .env.example .env

   # Edit .env and add your credentials
   # STRAVA_CLIENT_ID=your_client_id_from_step_1
   # STRAVA_CLIENT_SECRET=your_client_secret_from_step_1
   ```

3. **Authenticate**:

   ```bash
   make strava-auth
   # Browser opens -> Click "Authorize" -> Done!
   ```

4. **Test connection**:

   ```bash
   make strava-status
   ```

**Expected output**:

```
✓ Authenticated
Token expires: 2025-10-24 18:30:00
Rate Limits:
  15-min usage: 1/100
  Daily usage: 1/1000
```

---

## Daily Onsen Visit Workflow

**Scenario**: You go for a morning run, then visit an onsen. You want to track both activities.

### Step 1: Record Your Run on Strava

- Use Strava app or GPS watch during run
- Activity automatically uploads to Strava

### Step 2: Visit the Onsen

- Complete your onsen visit
- Record visit in Onsendo:

  ```bash
  poetry run onsendo visit add
  ```

### Step 3: Import and Link Your Run

```bash
# Download and import today's run, auto-link to your onsen visit
make strava-sync DAYS=1 IMPORT=true LINK=true
```

**What happens**:

1. Fetches your latest Strava activity
2. Downloads GPX file
3. Imports as exercise session
4. Finds your onsen visit (within ±2 hours)
5. Automatically links them

**Output**:

```
[1/1] Morning Run
  ✓ Downloaded: 20251024_063000_Morning_Run_12345678.gpx
  ✓ Imported (ID: 42)
  ✓ Linked to visit 15 (52 min from activity)

============================================================
Sync Complete
============================================================
Total activities: 1
Downloaded: 1
Imported: 1
Linked to visits: 1
============================================================
```

### Step 4: Verify

```bash
poetry run onsendo visit list --last 1
```

**Output shows**:

```
Visit #15 - 2025-10-24
Onsen: Takegawara Onsen
Exercise: Morning Run (5.2 km, 28:15)
```

---

## Weekly Batch Processing

**Scenario**: You prefer to process all activities once per week instead of daily.

### Sunday Evening Routine

1. **Preview what will be synced**:

   ```bash
   make strava-sync DAYS=7 DRY_RUN=true
   ```

2. **Review the list**:

   ```
   --- Dry Run Mode ---
   The following activities would be synced:

     1. Monday Morning Run
     2. Tuesday Evening Trail
     3. Wednesday Cycling
     4. Thursday Gym Session
     5. Saturday Long Run

   Total: 5 activities
   Would auto-import: YES
   Would auto-link: YES
   ```

3. **Run the sync**:

   ```bash
   make strava-sync DAYS=7 IMPORT=true LINK=true
   ```

4. **Review results in interactive browser**:

   ```bash
   poetry run onsendo strava interactive
   # Filter: last 7 days
   # Review which activities were linked to visits
   ```

---

## Post-Vacation Catch-Up

**Scenario**: You were on a 2-week onsen-hopping vacation and recorded many activities. Now you want to import everything.

### Step 1: Dry-Run to See Activity Count

```bash
make strava-sync DAYS=14 DRY_RUN=true
```

**Output**:

```
Found 23 activities
Total: 23 activities
```

### Step 2: Sync in Batches (Recommended for >20 activities)

**Week 1**:

```bash
# Sync days 8-14 (most recent week)
poetry run onsendo strava sync --days 7 --auto-import --auto-link
```

**Week 2**:

```bash
# Sync days 1-7 (older week)
# Use date range for precision
poetry run onsendo strava sync \
  --days 14 \
  --date-from 2025-10-10 \
  --date-to 2025-10-17 \
  --auto-import \
  --auto-link
```

### Step 3: Manual Review for Edge Cases

Some activities might not auto-link (e.g., >2 hours gap). Review them:

```bash
# List exercises without visits
poetry run onsendo exercise list --unlinked-only
```

**Output**:

```
Exercise #45 - 2025-10-12 06:30:00
  Type: Running
  Distance: 8.5 km
  [NOT LINKED TO VISIT]

Exercise #48 - 2025-10-15 17:00:00
  Type: Hiking
  Distance: 12.2 km
  [NOT LINKED TO VISIT]
```

### Step 4: Manually Link Stragglers

```bash
# Check which visits were on those days
poetry run onsendo visit list --date-range 2025-10-12,2025-10-12

# Link manually
make strava-link EXERCISE_ID=45 VISIT_ID=28
make strava-link EXERCISE_ID=48 VISIT_ID=31
```

---

## Selective Activity Import

**Scenario**: You only want to import running activities, not cycling or gym sessions.

### Option 1: Filter During Sync

```bash
make strava-sync DAYS=30 TYPE=Run IMPORT=true LINK=true
```

### Option 2: Use Interactive Browser

```bash
poetry run onsendo strava interactive
```

**Interactive workflow**:

1. Set filter: `Type: Run`
2. Browse activities
3. Select only the ones you want: `s` → `1,3,5`
4. Perform actions: `a` → `Download + Import + Auto-link`

### Option 3: Download All, Import Selectively

```bash
# Download all activities for backup
make strava-sync DAYS=30 FORMAT=all

# Later, import only running activities
make strava-sync DAYS=30 TYPE=Run IMPORT=true LINK=true
```

---

## Manual Review and Linking

**Scenario**: You want full control over which activities are linked to which visits.

### Workflow 1: Browse and Select in Interactive Mode

```bash
poetry run onsendo strava interactive
```

1. **Filter activities**: Last 7 days, running only
2. **Review details**: Press `d` + number to see full details
3. **Select carefully**: Press `s` + numbers to select specific activities
4. **Manual linking**: Press `a` → Choose "Download + Import + Manual link"
5. **Enter visit IDs**: You specify exact visit IDs

### Workflow 2: Import First, Link Later

**Step 1: Import without linking**:

```bash
make strava-sync DAYS=7 IMPORT=true
```

**Step 2: Review exercises and visits side-by-side**:

```bash
# Terminal 1: List exercises
poetry run onsendo exercise list --last 10

# Terminal 2: List visits
poetry run onsendo visit list --last 10
```

**Step 3: Link each one manually**:

```bash
make strava-link EXERCISE_ID=42 VISIT_ID=15
make strava-link EXERCISE_ID=43 VISIT_ID=16
make strava-link EXERCISE_ID=44 VISIT_ID=17
```

---

## Automation with Cron

**Scenario**: You want activities to automatically sync every night.

### Create Sync Script

**File**: `~/onsendo_daily_sync.sh`

```bash
#!/bin/bash
# Daily Strava sync script

cd /path/to/onsendo

# Activate poetry environment and sync
/usr/local/bin/poetry run onsendo strava sync \
  --days 1 \
  --auto-import \
  --auto-link \
  --format gpx \
  >> logs/strava_sync.log 2>&1

# Report results
echo "Sync completed at $(date)" >> logs/strava_sync.log
```

**Make executable**:

```bash
chmod +x ~/onsendo_daily_sync.sh
```

### Add to Cron

```bash
crontab -e
```

**Add line** (runs at 11 PM daily):

```
0 23 * * * /Users/yourname/onsendo_daily_sync.sh
```

### Monitor Logs

```bash
tail -f /path/to/onsendo/logs/strava_sync.log
```

**Expected output** (daily):

```
[2025-10-24 23:00:01] Sync completed at Thu Oct 24 23:00:01 JST 2025
[2025-10-24 23:00:01] Downloaded: 1
[2025-10-24 23:00:01] Imported: 1
[2025-10-24 23:00:01] Linked to visits: 1
```

### Weekly Summary Email (Optional)

**File**: `~/onsendo_weekly_report.sh`

```bash
#!/bin/bash
# Weekly summary report

cd /path/to/onsendo

# Get exercise stats for the week
/usr/local/bin/poetry run onsendo exercise stats --week $(date +%Y-%m-%d) \
  | mail -s "Onsendo Weekly Report" your.email@example.com
```

**Cron** (runs Sunday at 8 PM):

```
0 20 * * 0 /Users/yourname/onsendo_weekly_report.sh
```

---

## Data Backup and Archival

**Scenario**: You want to backup all your Strava activities as GPX/JSON files for long-term archival.

### Full Historical Backup

**Option 1: Sync Large Time Range**

```bash
# Download last year (no import, just files)
make strava-sync DAYS=365 FORMAT=all
```

**Option 2: Sync by Month**

```bash
# January 2024
poetry run onsendo strava sync \
  --date-from 2024-01-01 \
  --date-to 2024-01-31 \
  --format all

# February 2024
poetry run onsendo strava sync \
  --date-from 2024-02-01 \
  --date-to 2024-02-29 \
  --format all

# Continue for all months...
```

### Organize Downloaded Files

Downloaded files are stored in `data/strava/activities/` with format:

```
20250124_063000_Morning_Run_12345678.gpx
20250124_063000_Morning_Run_12345678.json
20250124_063000_Morning_Run_12345678_hr.csv
```

**Create yearly folders**:

```bash
cd data/strava/activities

# Organize by year
mkdir -p 2024 2025
mv 2024*_* 2024/
mv 2025*_* 2025/

# Organize by month within year
cd 2025
mkdir -p 01 02 03 04 05 06 07 08 09 10 11 12
mv 202501*_* 01/
mv 202502*_* 02/
# etc.
```

### Backup to Cloud

```bash
# Compress activities
cd data/strava
tar -czf activities_2025.tar.gz activities/

# Upload to cloud (example with rclone)
rclone copy activities_2025.tar.gz remote:backups/onsendo/
```

---

## Advanced Workflows

### Workflow: Analyze Running Performance by Onsen Visit

**Goal**: See if onsen visits improve your running performance.

**Steps**:

1. **Sync and link all runs**:

   ```bash
   make strava-sync DAYS=90 TYPE=Run IMPORT=true LINK=true
   ```

2. **Export data**:

   ```bash
   poetry run onsendo analysis run descriptive \
     --data-categories "exercise_sessions,visit_ratings" \
     --visualizations "correlation_matrix"
   ```

3. **Analyze correlation** between:
   - Onsen visit rating
   - Next-day running pace
   - Heart rate during run
   - Recovery time

### Workflow: Track Weekly Exercise Quotas (Rule Compliance)

**Goal**: Ensure you meet your weekly running goals.

**Steps**:

1. **Sync weekly**:

   ```bash
   make strava-sync DAYS=7 TYPE=Run IMPORT=true
   ```

2. **Check weekly stats**:

   ```bash
   poetry run onsendo exercise stats --week 2025-10-20
   ```

3. **Compare to rules**:

   ```bash
   poetry run onsendo rules-print --section 3
   # Check "Exercise Sessions" requirements
   ```

4. **Create rule revision if needed**:

   ```bash
   poetry run onsendo rules-revision-create
   # Include weekly exercise stats in revision
   ```

---

## Tips and Best Practices

### 1. Start Small

- Don't sync years of data at once
- Start with last 7 days
- Gradually increase range once comfortable

### 2. Use Dry-Run First

```bash
make strava-sync DAYS=30 DRY_RUN=true
```

- See what will happen before committing
- Estimate time required based on activity count

### 3. Monitor Rate Limits

```bash
poetry run onsendo strava status -v
```

- Check before large syncs
- Avoid hitting rate limits during important syncs

### 4. Link Review

- Auto-link works great for activities within ±2 hours of visits
- Activities outside this window require manual review
- Use `--auto-match` for suggestions, manual link for precision

### 5. Format Selection

- **GPX only**: Fastest, smallest files, sufficient for most uses
- **All formats**: Best for archival, larger size, slower sync
- **JSON**: Best for custom analysis and complete data preservation

### 6. Backup Before Major Operations

```bash
# Backup database before bulk import
make backup ENV=prod
```

---

## Common Questions

**Q: How often should I sync?**
A: Daily syncs with `DAYS=1` are ideal for most users. Weekly syncs work if you batch-process.

**Q: Can I sync while rate-limited?**
A: Yes, the system will automatically wait and retry. But it's slower.

**Q: What if auto-link picks the wrong visit?**
A: Unlink the exercise (`poetry run onsendo exercise unlink <id>`) and manually link to the correct visit.

**Q: Can I re-import an activity?**
A: Yes, just delete the existing exercise session and re-import. The GPX file is already downloaded.

**Q: How do I update an activity if I edited it on Strava?**
A: Delete the GPX file, then re-download. The system will fetch the updated data.

---

**Last Updated**: 2025-10-24
