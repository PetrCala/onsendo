# Strava Integration Technical Specification

**Version**: 1.0
**Date**: 2025-10-23
**Status**: Planning

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Component Specifications](#component-specifications)
4. [API Integration Details](#api-integration-details)
5. [Data Models](#data-models)
6. [User Interface Flows](#user-interface-flows)
7. [Implementation Phases](#implementation-phases)
8. [Testing Strategy](#testing-strategy)
9. [Security Considerations](#security-considerations)
10. [Error Handling](#error-handling)
11. [Configuration](#configuration)
12. [File Organization](#file-organization)

---

## Overview

### Purpose

Integrate Strava API to enable users to browse, download, import, and link Strava activities (workouts and heart rate data) to onsen visits through an interactive CLI workflow.

### Goals

- **Seamless Integration**: Minimal friction between Strava activity and onsen visit linking
- **Data Completeness**: Import both workout metrics AND heart rate data
- **User Control**: Allow review and manual override at each step
- **Offline Capability**: Downloaded files work independently of API access
- **Format Compatibility**: Support standard formats (GPX, JSON, CSV)

### Non-Goals

- Real-time activity syncing (webhook-based)
- Web UI for Strava authentication
- Direct Strava publishing from Onsendo
- Social features (comments, kudos, segments)

---

## System Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI Commands Layer                      │
│  (strava browse, strava download, strava sync, etc.)        │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                  Strava Integration Layer                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ StravaClient │  │ Strava       │  │ Interactive  │      │
│  │ (API calls)  │  │ Converter    │  │ Browser      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│              Existing Onsendo Core Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Exercise     │  │ HeartRate    │  │ Database     │      │
│  │ Manager      │  │ Manager      │  │ Models       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Strava API → StravaClient → StravaConverter → Local Files
                                                    ↓
                          ExerciseDataImporter ←───┘
                          HeartRateDataImporter
                                    ↓
                          Database (ExerciseSession, HeartRateData)
                                    ↓
                          Linked to OnsenVisit
```

---

## Component Specifications

### 1. StravaClient (`src/lib/strava_client.py`)

#### Responsibilities

- OAuth2 authentication flow
- Token management (storage, refresh)
- API request handling with rate limiting
- Activity listing and filtering
- Activity detail fetching
- Stream data fetching (GPS, HR, cadence, etc.)

#### Class Structure

```python
@dataclass
class StravaCredentials:
    """Strava OAuth2 credentials."""
    client_id: str
    client_secret: str
    redirect_uri: str = "http://localhost:8080/strava/callback"

@dataclass
class StravaToken:
    """Strava access token with refresh capability."""
    access_token: str
    refresh_token: str
    expires_at: int  # Unix timestamp

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now().timestamp() >= self.expires_at

@dataclass
class StravaActivitySummary:
    """Summary of a Strava activity (list view)."""
    id: int
    name: str
    activity_type: str
    start_date: datetime
    distance_m: Optional[float]
    moving_time_s: int
    elapsed_time_s: int
    total_elevation_gain_m: Optional[float]
    has_heartrate: bool
    average_heartrate: Optional[float]
    max_heartrate: Optional[float]

@dataclass
class StravaActivityDetail:
    """Detailed activity data including all available fields."""
    # Basic info
    id: int
    name: str
    activity_type: str
    sport_type: str
    start_date: datetime
    start_date_local: datetime
    timezone: str

    # Metrics
    distance_m: Optional[float]
    moving_time_s: int
    elapsed_time_s: int
    total_elevation_gain_m: Optional[float]
    calories: Optional[int]

    # Heart rate
    has_heartrate: bool
    average_heartrate: Optional[float]
    max_heartrate: Optional[float]

    # Location
    start_latlng: Optional[tuple[float, float]]
    end_latlng: Optional[tuple[float, float]]

    # Performance
    average_speed: Optional[float]
    max_speed: Optional[float]
    average_cadence: Optional[float]
    average_watts: Optional[float]

    # Weather (if available)
    average_temp: Optional[float]

    # Description
    description: Optional[str]

    # Gear
    gear_id: Optional[str]

@dataclass
class StravaStream:
    """Time-series stream data."""
    stream_type: str  # "latlng", "heartrate", "altitude", "cadence", etc.
    data: list  # Type varies by stream_type
    original_size: int
    resolution: str  # "low", "medium", "high"

class StravaClient:
    """Client for Strava API v3."""

    BASE_URL = "https://www.strava.com/api/v3"
    AUTH_URL = "https://www.strava.com/oauth/authorize"
    TOKEN_URL = "https://www.strava.com/oauth/token"

    # Rate limiting: 100 requests per 15 minutes, 1000 per day
    RATE_LIMIT_15MIN = 100
    RATE_LIMIT_DAILY = 1000

    def __init__(self, credentials: StravaCredentials, token_path: str):
        """Initialize Strava client with credentials and token storage."""
        self.credentials = credentials
        self.token_path = Path(token_path)
        self.token: Optional[StravaToken] = None
        self._load_token()

        # Rate limiting tracking
        self._requests_15min = 0
        self._requests_daily = 0
        self._reset_15min = datetime.now()
        self._reset_daily = datetime.now()

    def authenticate(self) -> bool:
        """
        Perform OAuth2 authorization flow.

        Opens browser for user authorization, starts local server
        to receive callback, exchanges code for token.

        Returns:
            True if authentication successful
        """
        pass

    def _load_token(self) -> bool:
        """Load token from disk if exists and valid."""
        pass

    def _save_token(self, token: StravaToken) -> None:
        """Save token to disk."""
        pass

    def _refresh_token_if_needed(self) -> None:
        """Refresh access token if expired."""
        pass

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None
    ) -> dict:
        """
        Make authenticated API request with rate limiting.

        Handles:
        - Token refresh
        - Rate limit checking
        - Error responses
        - Retries with exponential backoff
        """
        pass

    def list_activities(
        self,
        after: Optional[datetime] = None,
        before: Optional[datetime] = None,
        page: int = 1,
        per_page: int = 30
    ) -> list[StravaActivitySummary]:
        """
        List athlete activities with optional filtering.

        Args:
            after: Start date for activity filter
            before: End date for activity filter
            page: Page number for pagination
            per_page: Activities per page (max 200)

        Returns:
            List of activity summaries
        """
        pass

    def get_activity(self, activity_id: int) -> StravaActivityDetail:
        """
        Get detailed information about a specific activity.

        Args:
            activity_id: Strava activity ID

        Returns:
            Detailed activity data
        """
        pass

    def get_activity_streams(
        self,
        activity_id: int,
        stream_types: list[str] = None
    ) -> dict[str, StravaStream]:
        """
        Get stream data for an activity.

        Args:
            activity_id: Strava activity ID
            stream_types: Types of streams to fetch. Defaults to:
                ["time", "latlng", "altitude", "heartrate", "cadence",
                 "distance", "velocity_smooth"]

        Returns:
            Dictionary mapping stream type to StravaStream
        """
        pass

    def check_rate_limit_status(self) -> dict:
        """
        Check current rate limit usage.

        Returns:
            Dict with 15min and daily usage stats
        """
        pass
```

#### Authentication Flow

```
1. User runs: poetry run onsendo strava auth
2. CLI generates authorization URL with scopes
3. Opens browser to Strava authorization page
4. User approves access
5. Strava redirects to http://localhost:8080/strava/callback?code=...
6. Local server (started by CLI) receives code
7. Exchange code for access token + refresh token
8. Save tokens to local/strava/token.json
9. Display success message
```

**Required Scopes**:
- `read` - Read public activity data
- `activity:read_all` - Read all activity data including private
- `profile:read_all` - Read athlete profile

#### Rate Limiting Strategy

- Track requests in 15-minute window and daily window
- Before each request, check if limits exceeded
- If exceeded, sleep until window resets
- Display progress bar for long operations
- Allow user to cancel during sleep

---

### 2. StravaConverter (`src/lib/strava_converter.py`)

#### Responsibilities

- Convert Strava API responses to Onsendo data models
- Map Strava activity types to ExerciseType enum
- Extract GPS data as ExercisePoint objects
- Extract heart rate data as HeartRatePoint objects
- Export to standard file formats (GPX, JSON, CSV)

#### Class Structure

```python
class StravaActivityTypeMapper:
    """Maps Strava activity types to Onsendo exercise types."""

    TYPE_MAPPING: dict[str, ExerciseType] = {
        "Run": ExerciseType.RUNNING,
        "TrailRun": ExerciseType.RUNNING,
        "VirtualRun": ExerciseType.RUNNING,
        "Ride": ExerciseType.CYCLING,
        "VirtualRide": ExerciseType.CYCLING,
        "MountainBikeRide": ExerciseType.CYCLING,
        "GravelRide": ExerciseType.CYCLING,
        "EBikeRide": ExerciseType.CYCLING,
        "Hike": ExerciseType.HIKING,
        "Walk": ExerciseType.WALKING,
        "Swim": ExerciseType.SWIMMING,
        "Yoga": ExerciseType.YOGA,
        "WeightTraining": ExerciseType.GYM,
        "Workout": ExerciseType.GYM,
        "Crossfit": ExerciseType.GYM,
        "StairStepper": ExerciseType.GYM,
        "Elliptical": ExerciseType.GYM,
        "Rowing": ExerciseType.GYM,
    }

    @classmethod
    def map_type(cls, strava_type: str) -> ExerciseType:
        """Map Strava activity type to Onsendo ExerciseType."""
        return cls.TYPE_MAPPING.get(strava_type, ExerciseType.OTHER)

class StravaToExerciseConverter:
    """Converts Strava activities to ExerciseSession objects."""

    @classmethod
    def convert(
        cls,
        activity: StravaActivityDetail,
        streams: Optional[dict[str, StravaStream]] = None,
        save_path: Optional[str] = None
    ) -> ExerciseSession:
        """
        Convert Strava activity to ExerciseSession.

        Args:
            activity: Strava activity detail
            streams: Optional stream data (GPS, HR, etc.)
            save_path: Optional path to save raw data

        Returns:
            ExerciseSession object ready for database storage
        """
        pass

    @classmethod
    def _build_data_points(
        cls,
        streams: dict[str, StravaStream]
    ) -> list[ExercisePoint]:
        """
        Build ExercisePoint objects from Strava streams.

        Combines time, latlng, altitude, heartrate, and velocity
        streams into unified data points.
        """
        pass

    @classmethod
    def _calculate_elevation_gain(
        cls,
        altitude_stream: StravaStream
    ) -> float:
        """Calculate total elevation gain from altitude data."""
        pass

class StravaToHeartRateConverter:
    """Converts Strava activities to HeartRateSession objects."""

    @classmethod
    def convert(
        cls,
        activity: StravaActivityDetail,
        hr_stream: StravaStream,
        save_path: Optional[str] = None
    ) -> HeartRateSession:
        """
        Convert Strava activity with HR data to HeartRateSession.

        Args:
            activity: Strava activity detail
            hr_stream: Heart rate stream data
            save_path: Optional path to save raw data

        Returns:
            HeartRateSession object ready for database storage
        """
        pass

    @classmethod
    def _build_hr_points(
        cls,
        time_stream: StravaStream,
        hr_stream: StravaStream,
        start_time: datetime
    ) -> list[HeartRatePoint]:
        """Build HeartRatePoint objects from time and HR streams."""
        pass

class StravaFileExporter:
    """Exports Strava activities to standard file formats."""

    @classmethod
    def export_to_gpx(
        cls,
        activity: StravaActivityDetail,
        streams: dict[str, StravaStream],
        output_path: str
    ) -> None:
        """
        Export activity to GPX format.

        Includes GPS track, elevation, and heart rate in extensions.
        """
        pass

    @classmethod
    def export_to_json(
        cls,
        activity: StravaActivityDetail,
        streams: Optional[dict[str, StravaStream]],
        output_path: str
    ) -> None:
        """
        Export activity to comprehensive JSON format.

        Includes all metadata and stream data.
        """
        pass

    @classmethod
    def export_hr_to_csv(
        cls,
        activity: StravaActivityDetail,
        hr_stream: StravaStream,
        output_path: str
    ) -> None:
        """
        Export heart rate data to CSV format.

        Format compatible with HeartRateDataImporter.
        """
        pass
```

#### Activity Type Mapping Details

| Strava Type | Onsendo Type | Notes |
|-------------|--------------|-------|
| Run, TrailRun, VirtualRun | RUNNING | All running variants |
| Ride, VirtualRide, MountainBikeRide, GravelRide, EBikeRide | CYCLING | All cycling variants |
| Hike | HIKING | Hiking |
| Walk | WALKING | Walking |
| Swim | SWIMMING | All swimming |
| Yoga | YOGA | Yoga and stretching |
| WeightTraining, Workout, Crossfit | GYM | Strength training |
| StairStepper, Elliptical, Rowing | GYM | Cardio machines |
| Others | OTHER | Catch-all |

---

### 3. Interactive Browser (`src/lib/strava_browser.py`)

#### Responsibilities

- Display paginated activity list
- Handle user input for filtering and selection
- Provide activity detail view
- Manage workflow state (download, import, link)

#### Class Structure

```python
@dataclass
class ActivityFilter:
    """Filter criteria for activity browsing."""
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    activity_type: Optional[str] = None  # "Run", "Ride", etc.
    name_contains: Optional[str] = None
    has_heartrate: Optional[bool] = None
    min_distance_km: Optional[float] = None
    page_size: int = 20

@dataclass
class BrowserState:
    """State management for interactive browser."""
    current_page: int = 1
    total_activities: int = 0
    filter: ActivityFilter = field(default_factory=ActivityFilter)
    selected_activities: list[int] = field(default_factory=list)
    activities_cache: dict[int, StravaActivitySummary] = field(default_factory=dict)

class StravaActivityBrowser:
    """Interactive browser for Strava activities."""

    def __init__(self, client: StravaClient, db_session: Session):
        """Initialize browser with Strava client and database."""
        self.client = client
        self.db_session = db_session
        self.state = BrowserState()

    def run(self) -> None:
        """
        Start interactive browsing session.

        Main loop that handles user input and displays UI.
        """
        pass

    def _show_welcome(self) -> None:
        """Display welcome screen and initial filter prompt."""
        pass

    def _prompt_filter_criteria(self) -> ActivityFilter:
        """Interactive prompt for filter criteria."""
        pass

    def _fetch_and_display_page(self, page: int) -> None:
        """Fetch activities for current page and display."""
        pass

    def _display_activity_list(
        self,
        activities: list[StravaActivitySummary]
    ) -> None:
        """
        Display formatted activity list.

        Format:
        ┌─────────────────────────────────────────────────────────────┐
        │ Your Strava Activities (Page 1 of 5)                       │
        ├─────────────────────────────────────────────────────────────┤
        │  1. Morning Run              2025-10-20  5.2km    ♥ 156bpm │
        │  2. Evening Trail            2025-10-19  8.1km    ♥ 148bpm │
        │  3. Lunch Ride               2025-10-18  22.4km   ♥ 132bpm │
        │  ...                                                        │
        ├─────────────────────────────────────────────────────────────┤
        │ Commands: [s]elect | [d]etails | [n]ext | [p]rev | [f]ilter│
        │           [a]ctions | [q]uit                                │
        └─────────────────────────────────────────────────────────────┘
        """
        pass

    def _show_activity_details(self, activity_id: int) -> None:
        """
        Display detailed activity information.

        Fetches full activity data and streams summary.
        """
        pass

    def _handle_selection(self) -> None:
        """Handle activity selection (single or multiple)."""
        pass

    def _handle_actions(self) -> None:
        """
        Handle actions for selected activities.

        Options:
        1. Download only (save to file)
        2. Download + import as exercise
        3. Download + import as heart rate
        4. Download + import + auto-link to visit
        5. Download + import + manual link to visit
        """
        pass

    def _download_activity(
        self,
        activity_id: int,
        formats: list[str]
    ) -> dict[str, str]:
        """
        Download activity in specified formats.

        Args:
            activity_id: Strava activity ID
            formats: List of formats ("gpx", "json", "hr_csv")

        Returns:
            Dict mapping format to file path
        """
        pass

    def _import_as_exercise(
        self,
        file_path: str,
        visit_id: Optional[int] = None
    ) -> Optional[int]:
        """
        Import downloaded file as exercise session.

        Returns:
            Exercise session ID if successful
        """
        pass

    def _import_as_heart_rate(
        self,
        file_path: str,
        visit_id: Optional[int] = None
    ) -> Optional[int]:
        """
        Import downloaded file as heart rate data.

        Returns:
            Heart rate record ID if successful
        """
        pass

    def _suggest_visit_links(
        self,
        activity_time: datetime
    ) -> list[tuple[int, str]]:
        """
        Suggest onsen visits to link based on activity time.

        Searches for visits within ±2 hours of activity end time.

        Returns:
            List of (visit_id, description) tuples
        """
        pass

    def _prompt_visit_selection(
        self,
        suggestions: list[tuple[int, str]]
    ) -> Optional[int]:
        """
        Interactive prompt for visit selection.

        Displays suggestions and allows manual ID entry.
        """
        pass

    def _check_if_already_imported(
        self,
        activity_id: int
    ) -> Optional[dict]:
        """
        Check if activity already imported.

        Returns:
            Dict with exercise_id/hr_id if found, None otherwise
        """
        pass
```

---

### 4. CLI Commands (`src/cli/commands/strava/`)

#### Command Structure

```
src/cli/commands/strava/
├── __init__.py          # Command group registration
├── auth.py              # Authentication command
├── status.py            # Status check command
├── browse.py            # Interactive browser
├── download.py          # Quick download command
├── sync.py              # Batch sync command
├── link.py              # Link existing imports
└── config.py            # Configuration management
```

#### Command Specifications

##### `strava auth`

```python
def cmd_strava_auth(args, db_session):
    """
    Authenticate with Strava API.

    Opens browser for OAuth2 authorization flow.
    Saves access token for future use.

    Usage:
        poetry run onsendo strava auth
        poetry run onsendo strava auth --reauth  # Force re-authentication
    """
    pass
```

##### `strava status`

```python
def cmd_strava_status(args, db_session):
    """
    Check Strava API connection status.

    Displays:
    - Authentication status
    - Token expiration
    - Rate limit usage
    - Recent sync statistics

    Usage:
        poetry run onsendo strava status
        poetry run onsendo strava status --verbose
    """
    pass
```

##### `strava browse`

```python
def cmd_strava_browse(args, db_session):
    """
    Launch interactive activity browser.

    Allows filtering, selection, and actions on Strava activities.

    Usage:
        poetry run onsendo strava browse
        poetry run onsendo strava browse --days 30
        poetry run onsendo strava browse --type running
        poetry run onsendo strava browse --date-from 2025-10-01
        poetry run onsendo strava browse --has-hr

    Arguments:
        --days N: Show activities from last N days
        --type TYPE: Filter by activity type
        --date-from DATE: Start date (YYYY-MM-DD)
        --date-to DATE: End date (YYYY-MM-DD)
        --has-hr: Only show activities with heart rate data
        --min-distance KM: Minimum distance in kilometers
    """
    pass
```

##### `strava download`

```python
def cmd_strava_download(args, db_session):
    """
    Download specific activity by ID.

    Usage:
        poetry run onsendo strava download 12345678
        poetry run onsendo strava download 12345678 --format gpx
        poetry run onsendo strava download 12345678 --format json --import
        poetry run onsendo strava download 12345678 --import --link-visit 42

    Arguments:
        activity_id: Strava activity ID
        --format FORMAT: Output format (gpx, json, hr_csv, all)
        --import: Import after downloading
        --link-visit ID: Link to specific visit after import
        --auto-link: Auto-link to nearby visit based on timestamp
    """
    pass
```

##### `strava sync`

```python
def cmd_strava_sync(args, db_session):
    """
    Batch sync recent activities.

    Downloads and optionally imports multiple activities.

    Usage:
        poetry run onsendo strava sync
        poetry run onsendo strava sync --days 7
        poetry run onsendo strava sync --auto-import
        poetry run onsendo strava sync --auto-import --auto-link
        poetry run onsendo strava sync --type running --days 30

    Arguments:
        --days N: Sync activities from last N days (default: 7)
        --type TYPE: Only sync specific activity type
        --auto-import: Automatically import downloaded activities
        --auto-link: Automatically link to nearby visits
        --dry-run: Show what would be synced without downloading
    """
    pass
```

##### `strava link`

```python
def cmd_strava_link(args, db_session):
    """
    Link already-imported Strava activity to visit.

    Usage:
        poetry run onsendo strava link --exercise 42 --visit 123
        poetry run onsendo strava link --heart-rate 10 --visit 123
        poetry run onsendo strava link --exercise 42 --auto-match

    Arguments:
        --exercise ID: Exercise session ID to link
        --heart-rate ID: Heart rate record ID to link
        --visit ID: Visit ID to link to
        --auto-match: Auto-suggest nearby visits based on timestamp
    """
    pass
```

---

## API Integration Details

### Strava API v3 Endpoints

#### Authentication

**Authorization URL**:
```
GET https://www.strava.com/oauth/authorize
  ?client_id={CLIENT_ID}
  &redirect_uri={REDIRECT_URI}
  &response_type=code
  &scope=read,activity:read_all,profile:read_all
```

**Token Exchange**:
```
POST https://www.strava.com/oauth/token
  client_id={CLIENT_ID}
  client_secret={CLIENT_SECRET}
  code={AUTHORIZATION_CODE}
  grant_type=authorization_code

Response:
{
  "token_type": "Bearer",
  "expires_at": 1568775134,
  "expires_in": 21600,
  "refresh_token": "...",
  "access_token": "..."
}
```

**Token Refresh**:
```
POST https://www.strava.com/oauth/token
  client_id={CLIENT_ID}
  client_secret={CLIENT_SECRET}
  refresh_token={REFRESH_TOKEN}
  grant_type=refresh_token
```

#### Activity Endpoints

**List Activities**:
```
GET /athlete/activities
  ?before={timestamp}
  &after={timestamp}
  &page={page}
  &per_page={per_page}

Response: Array of activity summaries
```

**Get Activity Detail**:
```
GET /activities/{id}

Response: Detailed activity object
```

**Get Activity Streams**:
```
GET /activities/{id}/streams
  ?keys=time,latlng,altitude,heartrate,cadence,distance,velocity_smooth
  &key_by_type=true

Response: Object mapping stream types to arrays
```

### Rate Limiting

- **15-minute limit**: 100 requests
- **Daily limit**: 1000 requests
- **Headers returned**:
  - `X-RateLimit-Limit`: Daily limit
  - `X-RateLimit-Usage`: Current daily usage

**Handling Strategy**:
1. Track usage locally
2. Before request, check if limit exceeded
3. If exceeded, calculate wait time
4. Display progress: "Rate limit reached, waiting 5m 23s..."
5. Allow user to cancel

---

## Data Models

### Database Schema Updates

**Option 1: No Schema Changes** (Recommended)
- Use existing `ExerciseSession.data_source = "strava"`
- Use existing `HeartRateData.data_format = "strava"`
- Store Strava activity ID in notes or activity_name field

**Option 2: Add Strava Metadata** (Optional Enhancement)
```python
# In ExerciseSession model
strava_activity_id = Column(BigInteger, nullable=True, unique=True)
strava_sync_timestamp = Column(DateTime, nullable=True)

# In HeartRateData model
strava_activity_id = Column(BigInteger, nullable=True, unique=True)
```

**Migration Required**: If Option 2 chosen
```bash
poetry run onsendo database migrate-generate "Add Strava activity ID tracking"
poetry run onsendo database migrate-upgrade
```

### File Format Specifications

#### GPX Export Format

```xml
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Onsendo">
  <metadata>
    <name>Morning Run</name>
    <time>2025-10-20T06:30:00Z</time>
  </metadata>
  <trk>
    <name>Morning Run</name>
    <type>running</type>
    <trkseg>
      <trkpt lat="33.2794" lon="131.5006">
        <ele>10.5</ele>
        <time>2025-10-20T06:30:00Z</time>
        <extensions>
          <gpxtpx:TrackPointExtension>
            <gpxtpx:hr>142</gpxtpx:hr>
            <gpxtpx:cad>88</gpxtpx:cad>
          </gpxtpx:TrackPointExtension>
        </extensions>
      </trkpt>
      <!-- More points... -->
    </trkseg>
  </trk>
</gpx>
```

#### JSON Export Format

```json
{
  "metadata": {
    "source": "strava",
    "strava_activity_id": 12345678,
    "exported_at": "2025-10-23T10:30:00Z",
    "onsendo_version": "1.0.0"
  },
  "activity": {
    "name": "Morning Run",
    "type": "Run",
    "sport_type": "Run",
    "start_time": "2025-10-20T06:30:00Z",
    "start_time_local": "2025-10-20T15:30:00+09:00",
    "timezone": "Asia/Tokyo",
    "distance_m": 5234.5,
    "moving_time_s": 1823,
    "elapsed_time_s": 1920,
    "elevation_gain_m": 42.3,
    "calories": 345,
    "average_heartrate": 156.0,
    "max_heartrate": 178.0,
    "average_speed_mps": 2.87,
    "max_speed_mps": 4.12,
    "description": "Great morning run!"
  },
  "streams": {
    "time": [0, 5, 10, 15, ...],
    "latlng": [[33.2794, 131.5006], [33.2795, 131.5007], ...],
    "altitude": [10.5, 10.8, 11.2, ...],
    "heartrate": [142, 145, 148, ...],
    "distance": [0, 14.3, 28.7, ...],
    "velocity_smooth": [2.5, 2.8, 2.9, ...]
  }
}
```

#### Heart Rate CSV Format

```csv
timestamp,heart_rate
2025-10-20 06:30:00,142
2025-10-20 06:30:05,145
2025-10-20 06:30:10,148
...
```

---

## User Interface Flows

### Flow 1: First-Time Setup

```
1. User runs: poetry run onsendo strava auth

2. Display:
   ┌────────────────────────────────────────────────────────┐
   │ Strava Authentication                                  │
   ├────────────────────────────────────────────────────────┤
   │ This will open your browser to authorize Onsendo to   │
   │ access your Strava activities.                         │
   │                                                        │
   │ Required permissions:                                  │
   │ • Read your activity data                             │
   │ • Read your profile information                       │
   │                                                        │
   │ Your credentials will be stored securely in:          │
   │ local/strava/token.json                               │
   └────────────────────────────────────────────────────────┘

   Press Enter to continue or Ctrl+C to cancel...

3. Open browser → Strava authorization page

4. User clicks "Authorize"

5. Display:
   ✓ Authorization successful!
   ✓ Token saved to local/strava/token.json
   ✓ Token expires: 2025-10-24 06:00:00

   You can now use Strava commands:
   • poetry run onsendo strava browse
   • poetry run onsendo strava sync --days 7
```

### Flow 2: Interactive Browsing

```
1. User runs: poetry run onsendo strava browse --days 7

2. Display filter confirmation:
   ┌────────────────────────────────────────────────────────┐
   │ Filter Settings                                        │
   ├────────────────────────────────────────────────────────┤
   │ Date range: 2025-10-16 to 2025-10-23                 │
   │ Activity type: All                                     │
   │ Heart rate data: Not required                         │
   └────────────────────────────────────────────────────────┘

   Fetching activities... ━━━━━━━━━━━━━━━━━━━━━━ 100%

3. Display activity list:
   ┌─────────────────────────────────────────────────────────────┐
   │ Your Strava Activities (15 found, Page 1 of 1)             │
   ├─────────────────────────────────────────────────────────────┤
   │  1. Morning Run              2025-10-20  5.2km    ♥ 156bpm │
   │     06:30 → 07:01 (31m)                         ▲ 42m      │
   │  2. Evening Trail            2025-10-19  8.1km    ♥ 148bpm │
   │     18:45 → 19:32 (47m)                         ▲ 125m     │
   │  3. Lunch Ride               2025-10-18  22.4km   ♥ 132bpm │
   │     12:00 → 12:53 (53m)                         ▲ 78m      │
   │  4. Recovery Run             2025-10-17  3.5km    ♥ 142bpm │
   │     07:00 → 07:22 (22m)                         ▲ 15m      │
   │  5. Gym Session              2025-10-16  --       ♥ 138bpm │
   │     19:00 → 20:15 (1h 15m)                      --         │
   ├─────────────────────────────────────────────────────────────┤
   │ Commands:                                                   │
   │ [number] - View details    | [s]elect multiple             │
   │ [d] - Download selected    | [i] - Import & link           │
   │ [f] - Change filter        | [q] - Quit                    │
   └─────────────────────────────────────────────────────────────┘

   Enter command: 1

4. Display activity details:
   ┌─────────────────────────────────────────────────────────────┐
   │ Activity Details: Morning Run                               │
   ├─────────────────────────────────────────────────────────────┤
   │ Strava ID: 12345678                                        │
   │ Type: Running (Outdoor)                                     │
   │ Date: 2025-10-20 06:30:00 → 07:01:23                       │
   │                                                             │
   │ Distance:      5.23 km                                      │
   │ Duration:      31m 23s (moving: 30m 23s)                   │
   │ Pace:          5:48 /km                                     │
   │ Elevation:     +42m / -38m                                 │
   │ Calories:      345 kcal                                     │
   │                                                             │
   │ Heart Rate:    avg 156 bpm (max 178 bpm)                   │
   │ Cadence:       avg 168 spm                                  │
   │                                                             │
   │ GPS Data:      ✓ Available (1,124 points)                  │
   │ HR Stream:     ✓ Available (375 points)                    │
   │                                                             │
   │ Description:                                                │
   │ "Great morning run through Beppu! Perfect weather."        │
   ├─────────────────────────────────────────────────────────────┤
   │ Actions:                                                    │
   │ [d] - Download only          | [e] - Download & import     │
   │ [l] - Download, import, link | [b] - Back to list          │
   └─────────────────────────────────────────────────────────────┘

   Enter action: l

5. Download & import:
   Downloading activity 12345678...
   ✓ Saved JSON: data/strava/activities/12345678.json
   ✓ Saved GPX: data/strava/activities/12345678.gpx

   Importing as exercise session...
   ✓ Exercise session created (ID: 42)

   Finding nearby visits...
   ┌─────────────────────────────────────────────────────────────┐
   │ Suggested Visits                                            │
   ├─────────────────────────────────────────────────────────────┤
   │  1. Beppu Onsen (Ban #123)                                 │
   │     Visit time: 2025-10-20 07:30:00 (29 min after run)    │
   │     Rating: 9/10 | Hot: 8/10 | Crowded: 3/10              │
   │                                                             │
   │  2. Kannawa Jigoku Onsen (Ban #234)                        │
   │     Visit time: 2025-10-20 12:00:00 (5h after run)        │
   │     Rating: 8/10 | Hot: 9/10 | Crowded: 5/10              │
   └─────────────────────────────────────────────────────────────┘

   Select visit to link (1-2, or 'm' for manual ID, 's' to skip): 1

   ✓ Linked exercise session 42 to visit 123

   Continue browsing? [y/n]: n

   Done! Session summary:
   • Downloaded: 1 activity
   • Imported: 1 exercise session
   • Linked: 1 visit
```

### Flow 3: Quick Sync

```
1. User runs: poetry run onsendo strava sync --days 7 --auto-import --auto-link

2. Display:
   ┌─────────────────────────────────────────────────────────────┐
   │ Strava Sync                                                 │
   ├─────────────────────────────────────────────────────────────┤
   │ Date range: 2025-10-16 to 2025-10-23                       │
   │ Auto-import: Yes                                            │
   │ Auto-link: Yes                                              │
   └─────────────────────────────────────────────────────────────┘

   Fetching activities... ━━━━━━━━━━━━━━━━━━━━━━ 15/15

   Found 15 activities:
   • Already imported: 8
   • New activities: 7

   Proceed with sync? [y/n]: y

   Syncing activities...
   [1/7] Morning Run (12345678)        ━━━━━━━━━━ Downloaded
   [1/7] Morning Run (12345678)        ━━━━━━━━━━ Imported (exercise #42)
   [1/7] Morning Run (12345678)        ━━━━━━━━━━ Linked to visit #123
   [2/7] Evening Trail (12345679)      ━━━━━━━━━━ Downloaded
   [2/7] Evening Trail (12345679)      ━━━━━━━━━━ Imported (exercise #43)
   [2/7] Evening Trail (12345679)      ━━━━━━━━━━ No nearby visits
   ...

   ✓ Sync complete!

   Summary:
   • Downloaded: 7 activities
   • Imported: 7 exercise sessions
   • Auto-linked: 4 to visits
   • Skipped (no match): 3

   Unlinked activities can be linked later with:
   poetry run onsendo exercise link <id> --auto-match
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1)

**Goal**: Basic authentication and API connectivity

**Tasks**:
1. Create `StravaCredentials` and `StravaToken` dataclasses
2. Implement OAuth2 authentication flow
3. Create `StravaClient` class with basic methods:
   - `authenticate()`
   - `_load_token()` / `_save_token()`
   - `_refresh_token_if_needed()`
   - `_make_request()` with rate limiting
4. Implement CLI commands:
   - `strava auth`
   - `strava status`
5. Add environment variables to `.env.example`
6. Create directory structure (`data/strava/`, `local/strava/`)

**Deliverables**:
- User can authenticate with Strava
- Token stored and auto-refreshed
- Status command shows connection state

**Testing**:
- Manual test: Complete OAuth flow
- Verify token saved correctly
- Verify rate limiting works

---

### Phase 2: Activity Listing (Week 2)

**Goal**: Fetch and display Strava activities

**Tasks**:
1. Create `StravaActivitySummary` dataclass
2. Implement `StravaClient.list_activities()`
3. Create `ActivityFilter` dataclass
4. Implement basic filtering logic
5. Create CLI command: `strava browse` (list-only view)
6. Add pagination support

**Deliverables**:
- User can list activities with filtering
- Activities displayed in formatted table
- Pagination works correctly

**Testing**:
- Test with various filter combinations
- Test pagination with large activity count
- Verify date range filtering

---

### Phase 3: Data Conversion (Week 3)

**Goal**: Convert Strava data to Onsendo formats

**Tasks**:
1. Create `StravaActivityDetail` dataclass
2. Implement `StravaClient.get_activity()`
3. Implement `StravaClient.get_activity_streams()`
4. Create `StravaActivityTypeMapper`
5. Implement `StravaToExerciseConverter`
6. Implement `StravaToHeartRateConverter`
7. Implement `StravaFileExporter` (GPX, JSON, CSV)

**Deliverables**:
- Strava activities convert to `ExerciseSession`
- Strava activities convert to `HeartRateSession`
- Export to standard file formats works

**Testing**:
- Unit tests for type mapping
- Integration tests with real Strava data
- Verify GPX/JSON format validity
- Test with activities with/without GPS
- Test with activities with/without HR

---

### Phase 4: Interactive Browser (Week 4)

**Goal**: Full interactive browsing experience

**Tasks**:
1. Create `BrowserState` dataclass
2. Implement `StravaActivityBrowser` class
3. Add interactive filter prompts
4. Add activity detail view
5. Add multi-selection support
6. Implement download workflow
7. Implement import workflow
8. Implement visit linking workflow

**Deliverables**:
- Full interactive browsing works
- User can download/import/link in one flow
- Visit suggestions work correctly

**Testing**:
- Manual testing of all workflows
- Test with edge cases (no GPS, no HR, etc.)
- Test visit suggestion algorithm
- Test error handling

---

### Phase 5: Quick Commands (Week 5)

**Goal**: Non-interactive batch operations

**Tasks**:
1. Implement `strava download` command
2. Implement `strava sync` command
3. Implement `strava link` command
4. Add deduplication logic (check if already imported)
5. Add dry-run mode for sync
6. Add progress bars for batch operations

**Deliverables**:
- Quick download command works
- Batch sync works with auto-import/link
- Deduplication prevents duplicate imports

**Testing**:
- Test sync with various date ranges
- Test deduplication logic
- Test auto-linking accuracy
- Test dry-run mode

---

### Phase 6: Polish & Documentation (Week 6)

**Goal**: Production-ready release

**Tasks**:
1. Add comprehensive error handling
2. Add retry logic with exponential backoff
3. Create Makefile targets
4. Write user documentation (README section)
5. Write technical documentation (this spec + docstrings)
6. Add example workflows
7. Create troubleshooting guide
8. Performance optimization

**Deliverables**:
- Robust error handling
- Complete documentation
- Makefile integration
- Example workflows

**Testing**:
- End-to-end testing of all workflows
- Error scenario testing
- Performance testing with large activity counts
- Documentation review

---

## Testing Strategy

### Unit Tests

**Location**: `tests/unit/test_strava_*.py`

**Coverage**:
1. `test_strava_type_mapper.py`
   - Test all activity type mappings
   - Test unknown types default to OTHER

2. `test_strava_converter.py`
   - Test ExerciseSession conversion
   - Test HeartRateSession conversion
   - Test with missing data (no GPS, no HR)
   - Test elevation calculation
   - Test data point building

3. `test_strava_exporter.py`
   - Test GPX export format
   - Test JSON export format
   - Test CSV export format
   - Validate against format specs

4. `test_strava_token.py`
   - Test token expiration checking
   - Test token serialization

### Integration Tests

**Location**: `tests/integration/test_strava_integration.py`

**Coverage**:
1. OAuth flow (mocked)
2. API request handling (mocked Strava responses)
3. End-to-end download → convert → save workflow
4. Database import workflow
5. Visit linking workflow

**Mocking Strategy**:
- Mock Strava API responses using `responses` library
- Create fixture files with real Strava API response examples
- Mock browser opening in auth flow

### Manual Testing Checklist

- [ ] Complete OAuth flow with real Strava account
- [ ] List activities with various filters
- [ ] Download activity in all formats
- [ ] Import GPX file from Strava
- [ ] Import JSON file from Strava
- [ ] Auto-link activity to visit
- [ ] Manual link activity to visit
- [ ] Batch sync with auto-import
- [ ] Handle rate limiting (trigger by many requests)
- [ ] Handle expired token (force expiration)
- [ ] Handle network errors (disconnect wifi)
- [ ] Handle invalid activity ID
- [ ] Handle activity with no GPS data
- [ ] Handle activity with no HR data

---

## Security Considerations

### Credential Storage

**Client Credentials**:
- Stored in `.env` file (gitignored)
- Never committed to repository
- User must obtain from Strava

**Access Tokens**:
- Stored in `local/strava/token.json` (gitignored)
- File permissions: `chmod 600` on save
- Contains refresh token (long-lived)

**Best Practices**:
```python
def _save_token(self, token: StravaToken) -> None:
    """Save token with secure file permissions."""
    token_path = Path(self.token_path)
    token_path.parent.mkdir(parents=True, exist_ok=True)

    # Write token data
    with open(token_path, 'w') as f:
        json.dump(token.to_dict(), f, indent=2)

    # Set restrictive permissions (owner read/write only)
    os.chmod(token_path, 0o600)
```

### API Key Protection

**Environment Variables**:
```bash
# .env (never commit)
STRAVA_CLIENT_ID=12345
STRAVA_CLIENT_SECRET=abcdef123456
```

**Validation**:
```python
def load_credentials() -> StravaCredentials:
    """Load and validate Strava credentials from environment."""
    client_id = os.getenv("STRAVA_CLIENT_ID")
    client_secret = os.getenv("STRAVA_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError(
            "Strava credentials not found. "
            "Please set STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET "
            "in your .env file."
        )

    return StravaCredentials(
        client_id=client_id,
        client_secret=client_secret
    )
```

### Rate Limit Compliance

**Respect Strava's Limits**:
- Never bypass rate limits
- Implement exponential backoff on errors
- Display clear messages to user when rate limited
- Allow user to cancel long waits

### Data Privacy

**Downloaded Data**:
- Stored locally only
- User controls what data is downloaded
- Files can be deleted manually
- No data sent to third parties

**Database Storage**:
- Only metadata stored in database
- Full activity data in local files
- User can delete imported records

---

## Error Handling

### Error Categories

#### 1. Authentication Errors

**Scenario**: Token expired or invalid

**Handling**:
```python
try:
    response = self._make_request("GET", "/athlete/activities")
except StravaAuthenticationError as e:
    logger.warning("Authentication failed, attempting token refresh")
    try:
        self._refresh_token()
        response = self._make_request("GET", "/athlete/activities")
    except StravaAuthenticationError:
        logger.error("Token refresh failed, re-authentication required")
        print("Your Strava authentication has expired.")
        print("Please run: poetry run onsendo strava auth")
        sys.exit(1)
```

#### 2. Rate Limit Errors

**Scenario**: API rate limit exceeded

**Handling**:
```python
def _handle_rate_limit(self, response: requests.Response) -> None:
    """Handle rate limit response."""
    retry_after = int(response.headers.get("Retry-After", 900))

    print(f"Rate limit exceeded. Waiting {retry_after} seconds...")
    print("Press Ctrl+C to cancel")

    try:
        # Show progress bar while waiting
        for remaining in range(retry_after, 0, -1):
            mins, secs = divmod(remaining, 60)
            print(f"\rWaiting: {mins:02d}:{secs:02d}", end="")
            time.sleep(1)
        print("\nResuming...")
    except KeyboardInterrupt:
        print("\nCancelled by user")
        sys.exit(0)
```

#### 3. Network Errors

**Scenario**: Network timeout or connection error

**Handling**:
```python
def _make_request_with_retry(
    self,
    method: str,
    endpoint: str,
    max_retries: int = 3
) -> dict:
    """Make request with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            return self._make_request(method, endpoint)
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(
                    f"Request timeout, retrying in {wait_time}s "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(wait_time)
            else:
                raise StravaNetworkError(
                    "Request failed after multiple retries"
                )
        except requests.exceptions.ConnectionError as e:
            raise StravaNetworkError(
                f"Network connection failed: {e}"
            )
```

#### 4. Data Validation Errors

**Scenario**: Activity data missing required fields

**Handling**:
```python
def convert(self, activity: StravaActivityDetail) -> ExerciseSession:
    """Convert with validation."""
    try:
        exercise_type = StravaActivityTypeMapper.map_type(
            activity.activity_type
        )

        # Validate required fields
        if not activity.start_date:
            raise ValueError("Activity missing start_date")

        if not activity.moving_time_s:
            raise ValueError("Activity missing moving_time")

        # Build session...

    except ValueError as e:
        logger.error(f"Invalid activity data: {e}")
        raise StravaConversionError(
            f"Cannot convert activity {activity.id}: {e}"
        )
```

#### 5. File System Errors

**Scenario**: Cannot write to disk

**Handling**:
```python
def _download_activity(self, activity_id: int) -> str:
    """Download with file system error handling."""
    output_dir = Path("data/strava/activities")

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        raise StravaFileError(
            f"Permission denied: Cannot create directory {output_dir}"
        )

    output_path = output_dir / f"{activity_id}.json"

    try:
        with open(output_path, 'w') as f:
            json.dump(activity_data, f, indent=2)
    except IOError as e:
        raise StravaFileError(
            f"Failed to write file {output_path}: {e}"
        )

    return str(output_path)
```

### Custom Exceptions

```python
class StravaError(Exception):
    """Base exception for Strava integration."""
    pass

class StravaAuthenticationError(StravaError):
    """Authentication or authorization failed."""
    pass

class StravaRateLimitError(StravaError):
    """API rate limit exceeded."""
    pass

class StravaNetworkError(StravaError):
    """Network connection or timeout error."""
    pass

class StravaConversionError(StravaError):
    """Data conversion failed."""
    pass

class StravaFileError(StravaError):
    """File system operation failed."""
    pass

class StravaActivityNotFoundError(StravaError):
    """Activity ID not found."""
    pass
```

---

## Configuration

### Environment Variables

**`.env.example` Template**:
```bash
# ============================================================================
# Strava API Configuration
# ============================================================================

# Strava OAuth2 Credentials
# Get these from: https://www.strava.com/settings/api
# 1. Go to https://www.strava.com/settings/api
# 2. Create an application (if you haven't already)
# 3. Note your Client ID and Client Secret
STRAVA_CLIENT_ID=your_client_id_here
STRAVA_CLIENT_SECRET=your_client_secret_here

# OAuth2 Redirect URI
# For local development, use localhost callback
# This must match the "Authorization Callback Domain" in your Strava app settings
STRAVA_REDIRECT_URI=http://localhost:8080/strava/callback

# Token Storage Path
# Where access/refresh tokens will be stored (gitignored)
STRAVA_TOKEN_PATH=local/strava/token.json

# Sync Settings
# Default number of days to sync when running 'strava sync'
STRAVA_DEFAULT_SYNC_DAYS=7

# Download Settings
# Default format for downloads: "gpx", "json", "all"
STRAVA_DEFAULT_DOWNLOAD_FORMAT=all

# Activity Storage
# Where downloaded activity files are stored
STRAVA_ACTIVITY_DIR=data/strava/activities

# ============================================================================
# Strava Setup Instructions
# ============================================================================

# 1. Create Strava API Application:
#    - Go to https://www.strava.com/settings/api
#    - Click "Create an App" (if you don't have one)
#    - Fill in details:
#      * Application Name: "Onsendo Personal"
#      * Category: "Other"
#      * Club: Leave blank
#      * Website: http://localhost (for personal use)
#      * Authorization Callback Domain: localhost
#
# 2. Copy credentials to .env:
#    - Copy this file to .env
#    - Replace your_client_id_here with your Client ID
#    - Replace your_client_secret_here with your Client Secret
#
# 3. Authenticate:
#    poetry run onsendo strava auth
#    # Browser will open for authorization
#    # After approval, token saved to local/strava/token.json
#
# 4. Test connection:
#    poetry run onsendo strava status
#
# 5. Start using:
#    poetry run onsendo strava browse
#    poetry run onsendo strava sync --days 7

# Security Notes:
# - Never commit .env to git (already in .gitignore)
# - Keep your Client Secret private
# - Token expires after 6 hours but auto-refreshes
# - Refresh token is long-lived (use carefully)
```

### Settings Class

```python
@dataclass
class StravaSettings:
    """Strava integration settings."""

    client_id: str
    client_secret: str
    redirect_uri: str = "http://localhost:8080/strava/callback"
    token_path: str = "local/strava/token.json"
    default_sync_days: int = 7
    default_download_format: str = "all"
    activity_dir: str = "data/strava/activities"

    @classmethod
    def from_env(cls) -> "StravaSettings":
        """Load settings from environment variables."""
        return cls(
            client_id=os.getenv("STRAVA_CLIENT_ID", ""),
            client_secret=os.getenv("STRAVA_CLIENT_SECRET", ""),
            redirect_uri=os.getenv(
                "STRAVA_REDIRECT_URI",
                "http://localhost:8080/strava/callback"
            ),
            token_path=os.getenv(
                "STRAVA_TOKEN_PATH",
                "local/strava/token.json"
            ),
            default_sync_days=int(os.getenv("STRAVA_DEFAULT_SYNC_DAYS", "7")),
            default_download_format=os.getenv(
                "STRAVA_DEFAULT_DOWNLOAD_FORMAT",
                "all"
            ),
            activity_dir=os.getenv(
                "STRAVA_ACTIVITY_DIR",
                "data/strava/activities"
            ),
        )

    def validate(self) -> None:
        """Validate settings."""
        if not self.client_id:
            raise ValueError("STRAVA_CLIENT_ID not set")
        if not self.client_secret:
            raise ValueError("STRAVA_CLIENT_SECRET not set")
```

---

## File Organization

### Directory Structure

```
onsendo/
├── data/
│   └── strava/
│       └── activities/           # Downloaded activity files
│           ├── 12345678.json    # Full activity data
│           ├── 12345678.gpx     # GPS route (if available)
│           └── 12345678_hr.csv  # Heart rate data (if available)
│
├── local/                        # Gitignored secrets
│   └── strava/
│       ├── credentials.json     # OAuth2 credentials (optional)
│       └── token.json          # Access/refresh tokens
│
├── src/
│   ├── lib/
│   │   ├── strava_client.py    # Strava API client
│   │   ├── strava_converter.py # Data conversion
│   │   └── strava_browser.py   # Interactive browser
│   │
│   ├── cli/
│   │   └── commands/
│   │       └── strava/
│   │           ├── __init__.py
│   │           ├── auth.py
│   │           ├── status.py
│   │           ├── browse.py
│   │           ├── download.py
│   │           ├── sync.py
│   │           └── link.py
│   │
│   └── types/
│       └── strava.py           # Strava-specific type definitions
│
├── tests/
│   ├── unit/
│   │   ├── test_strava_client.py
│   │   ├── test_strava_converter.py
│   │   ├── test_strava_type_mapper.py
│   │   └── test_strava_exporter.py
│   │
│   ├── integration/
│   │   └── test_strava_integration.py
│   │
│   └── fixtures/
│       └── strava/
│           ├── activity_summary.json
│           ├── activity_detail.json
│           └── activity_streams.json
│
├── docs/
│   ├── strava_integration_spec.md  # This document
│   └── strava_troubleshooting.md   # User troubleshooting guide
│
├── .env.example                 # Template with Strava config
└── .gitignore                   # Includes local/, .env
```

### File Naming Conventions

**Activity Files**:
- Format: `{strava_activity_id}.{extension}`
- Examples:
  - `12345678.json` - Full activity data
  - `12345678.gpx` - GPS route
  - `12345678_hr.csv` - Heart rate only

**Token File**:
- Location: `local/strava/token.json`
- Format:
  ```json
  {
    "access_token": "...",
    "refresh_token": "...",
    "expires_at": 1634567890,
    "token_type": "Bearer"
  }
  ```

---

## Appendix A: Strava API Response Examples

### Activity Summary Response

```json
[
  {
    "id": 12345678,
    "name": "Morning Run",
    "distance": 5234.5,
    "moving_time": 1823,
    "elapsed_time": 1920,
    "total_elevation_gain": 42.3,
    "type": "Run",
    "sport_type": "Run",
    "start_date": "2025-10-20T06:30:00Z",
    "start_date_local": "2025-10-20T15:30:00Z",
    "timezone": "(GMT+09:00) Asia/Tokyo",
    "start_latlng": [33.2794, 131.5006],
    "end_latlng": [33.2801, 131.5012],
    "achievement_count": 2,
    "kudos_count": 5,
    "comment_count": 1,
    "athlete_count": 1,
    "photo_count": 0,
    "trainer": false,
    "commute": false,
    "manual": false,
    "private": false,
    "flagged": false,
    "workout_type": 0,
    "average_speed": 2.87,
    "max_speed": 4.12,
    "has_heartrate": true,
    "average_heartrate": 156.0,
    "max_heartrate": 178.0,
    "elev_high": 25.4,
    "elev_low": 10.2,
    "pr_count": 0,
    "total_photo_count": 0
  }
]
```

### Activity Detail Response

```json
{
  "id": 12345678,
  "external_id": "garmin_push_12345678",
  "upload_id": 13579246,
  "athlete": {
    "id": 987654
  },
  "name": "Morning Run",
  "distance": 5234.5,
  "moving_time": 1823,
  "elapsed_time": 1920,
  "total_elevation_gain": 42.3,
  "type": "Run",
  "sport_type": "Run",
  "start_date": "2025-10-20T06:30:00Z",
  "start_date_local": "2025-10-20T15:30:00Z",
  "timezone": "(GMT+09:00) Asia/Tokyo",
  "utc_offset": 32400.0,
  "start_latlng": [33.2794, 131.5006],
  "end_latlng": [33.2801, 131.5012],
  "average_speed": 2.87,
  "max_speed": 4.12,
  "average_cadence": 84.2,
  "has_heartrate": true,
  "average_heartrate": 156.0,
  "max_heartrate": 178.0,
  "heartrate_opt_out": false,
  "calories": 345.0,
  "description": "Great morning run through Beppu!",
  "gear_id": "g123456",
  "device_name": "Garmin Forerunner 945",
  "embed_token": "...",
  "splits_metric": [...],
  "laps": [...],
  "photos": {...},
  "stats_visibility": [{...}],
  "hide_from_home": false,
  "device_watts": false,
  "has_kudoed": false
}
```

### Streams Response

```json
{
  "time": {
    "data": [0, 5, 10, 15, 20, ...],
    "series_type": "time",
    "original_size": 375,
    "resolution": "high"
  },
  "latlng": {
    "data": [
      [33.2794, 131.5006],
      [33.2795, 131.5007],
      [33.2796, 131.5008],
      ...
    ],
    "series_type": "distance",
    "original_size": 1124,
    "resolution": "high"
  },
  "altitude": {
    "data": [10.5, 10.8, 11.2, 11.5, ...],
    "series_type": "distance",
    "original_size": 1124,
    "resolution": "high"
  },
  "heartrate": {
    "data": [142, 145, 148, 151, ...],
    "series_type": "time",
    "original_size": 375,
    "resolution": "high"
  },
  "distance": {
    "data": [0.0, 14.3, 28.7, 43.1, ...],
    "series_type": "distance",
    "original_size": 1124,
    "resolution": "high"
  },
  "velocity_smooth": {
    "data": [2.5, 2.8, 2.9, 2.85, ...],
    "series_type": "distance",
    "original_size": 1124,
    "resolution": "high"
  }
}
```

---

## Appendix B: Makefile Integration

Add to `Makefile`:

```makefile
# ============================================================================
# Strava Integration
# ============================================================================

.PHONY: strava-auth
strava-auth:  ## Authenticate with Strava API
	$(POETRY_RUN) onsendo strava auth

.PHONY: strava-status
strava-status:  ## Check Strava connection status
	$(POETRY_RUN) onsendo strava status

.PHONY: strava-browse
strava-browse:  ## Browse Strava activities interactively
	$(POETRY_RUN) onsendo strava browse $(if $(DAYS),--days $(DAYS),)

.PHONY: strava-sync
strava-sync:  ## Sync recent Strava activities
	$(POETRY_RUN) onsendo strava sync \
		$(if $(DAYS),--days $(DAYS),) \
		$(if $(AUTO_IMPORT),--auto-import,) \
		$(if $(AUTO_LINK),--auto-link,)

.PHONY: strava-download
strava-download:  ## Download specific Strava activity
	@if [ -z "$(ID)" ]; then \
		echo "Error: Activity ID required. Usage: make strava-download ID=12345678"; \
		exit 1; \
	fi
	$(POETRY_RUN) onsendo strava download $(ID) \
		$(if $(FORMAT),--format $(FORMAT),) \
		$(if $(IMPORT),--import,)

# Examples:
# make strava-auth
# make strava-browse DAYS=30
# make strava-sync DAYS=7 AUTO_IMPORT=1 AUTO_LINK=1
# make strava-download ID=12345678 FORMAT=gpx IMPORT=1
```

---

## Appendix C: README Section

Add to `README.md` under **Advanced Features**:

```markdown
### Strava Integration

Import workout and heart rate data directly from your Strava account.

#### Setup

1. **Create Strava API Application**:
   - Go to https://www.strava.com/settings/api
   - Click "Create an App"
   - Fill in details (use `localhost` for personal use)
   - Note your Client ID and Client Secret

2. **Configure credentials**:
   ```bash
   # Add to .env
   STRAVA_CLIENT_ID=your_client_id
   STRAVA_CLIENT_SECRET=your_client_secret
   ```

3. **Authenticate**:
   ```bash
   poetry run onsendo strava auth
   # Browser opens for authorization
   # Token saved to local/strava/token.json
   ```

#### Interactive Browsing

Browse and import activities with visual interface:

```bash
# Browse recent activities
poetry run onsendo strava browse

# Filter by date range
poetry run onsendo strava browse --days 30

# Filter by activity type
poetry run onsendo strava browse --type running

# Only show activities with heart rate data
poetry run onsendo strava browse --has-hr
```

**Interactive workflow**:
1. Filter activities by date, type, or name
2. Select activity to view details
3. Download, import, and link to visit in one flow
4. Auto-suggest nearby visits based on timestamps

#### Quick Commands

```bash
# Download specific activity
poetry run onsendo strava download 12345678 --format gpx

# Download and import
poetry run onsendo strava download 12345678 --import

# Download, import, and auto-link
poetry run onsendo strava download 12345678 --import --auto-link

# Batch sync recent activities
poetry run onsendo strava sync --days 7 --auto-import --auto-link
```

#### Makefile Commands

```bash
# Authenticate
make strava-auth

# Check connection status
make strava-status

# Browse activities (last 30 days)
make strava-browse DAYS=30

# Weekly sync with auto-import and linking
make strava-sync DAYS=7 AUTO_IMPORT=1 AUTO_LINK=1

# Download specific activity
make strava-download ID=12345678 FORMAT=all IMPORT=1
```

#### File Organization

Downloaded activities are stored in:
- `data/strava/activities/{id}.json` - Full activity data
- `data/strava/activities/{id}.gpx` - GPS route (if available)
- `data/strava/activities/{id}_hr.csv` - Heart rate data (if available)

#### Features

- **Smart Linking**: Auto-suggest visits within ±2 hours of activity
- **Dual Import**: Activities with HR can be imported as both workout and HR data
- **Offline Mode**: Downloaded files work with standard import commands
- **Deduplication**: Prevents importing same activity multiple times
- **Rate Limiting**: Automatic handling of Strava API limits
- **Format Flexibility**: Export to GPX, JSON, or CSV

#### Troubleshooting

**"Authentication failed"**:
- Token may have expired, run `poetry run onsendo strava auth`

**"Rate limit exceeded"**:
- Strava limits: 100 requests per 15 minutes, 1000 per day
- Wait for rate limit to reset (displayed in message)

**"Activity has no GPS data"**:
- Indoor activities don't have GPS routes
- Import as exercise without route data

See [docs/strava_troubleshooting.md](docs/strava_troubleshooting.md) for more details.
```

---

**End of Specification Document**

This specification provides a complete technical blueprint for implementing Strava integration in Onsendo. It covers all aspects from authentication to data conversion, user workflows, error handling, testing, and documentation.
