# Repository Guidelines

## Project Structure & Module Organization

- `src/cli`, `src/analysis`, `src/db`, `src/lib`, and `src/types` contain runtime code; extend existing modules before creating new packages.
- Tests mirror this layout: put fast specs in `tests/unit/**` and boundary checks plus SQLite fixtures in `tests/integration/**`.
- `scripts/` hosts maintenance tooling, `docs/` stores long-form references, while generated artifacts belong in `output/` or `local/` and must stay untracked.

## Build, Test, and Development Commands

- Install dependencies via `poetry install`, then use `poetry run ...` or `poetry shell` for all commands.
- Inspect the CLI with `poetry run onsendo --help` and scenario-specific subcommands such as `poetry run onsendo location add`.
- Run quick feedback loops with `poetry run pytest -q -m "not integration"`; execute the full suite with `poetry run pytest`.
- Lint with `poetry run pylint src tests` and audit riskier patches using `poetry run coverage run -m pytest` followed by `poetry run coverage report`.

## Coding Style & Naming Conventions

- Follow 4-space indentation, comprehensive type hints, snake_case functions, PascalCase classes, and UPPER_SNAKE_CASE constants.
- Centralize shared logic in `src/lib` or `src/analysis` and rely on `paths.py` instead of ad-hoc path joins.
- Prefer pure functions for calculations, log through `loguru`, and remove temporary files you create under `output/`.

## Testing Guidelines

- Name test files `test_*.py` as enforced by `pytest.ini`; keep unit assertions focused and deterministic.
- Mark broader scenarios with `@pytest.mark.integration` so reviewers can run `-m "not integration"` during iteration.
- Reuse fixtures from `tests/conftest.py`, extend mock builders instead of hard-coding data, and add regression cases for every bug fix.

## Commit & Pull Request Guidelines

- Use Conventional Commits (`feat:`, `fix:`, `refactor:`, `chore:`) in present tense and under 72 characters, referencing issues in the body when relevant.
- Summaries should state intent, list local verification (`pytest`, `pylint`, optional `coverage`), and include CLI screenshots or transcripts for UX changes.
- Keep branches rebased on `main`, avoid unrelated formatting churn, and request review only after checks pass.

## Key Features & Systems

- **Onsen Tracking**: Record visits with ratings, health metrics, logistics, and optional notes
- **Heart Rate Monitoring**: Import from CSV, JSON, Apple Health; link to visits with SHA-256 integrity
- **Exercise Tracking**: Import from GPX, TCX, Apple Health; GPS routes, pace/elevation validation, weekly stats for challenge targets
- **Smart Recommendations**: Distance-based filtering using Haversine formula, availability checking, visit history personalization
- **Rules Management**: Track Onsendo Challenge compliance with weekly review workflow and revision history
- **Database Migrations**: Alembic-based schema evolution without data loss

## Data & Environment Notes

- SQLite databases belong in `data/`; never commit secrets or large personal exports.
- Organize exercise/heart rate files in `data/exercise/` and `data/heart_rate/` with format-specific subdirectories.
- Confirm Python 3.12+ via `poetry env info`. For Selenium tasks, document driver requirements alongside the relevant script in `scripts/`.
