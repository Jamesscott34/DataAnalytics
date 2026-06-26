# Database schema — predictive-security-analytics-lab

> Phase 0 planning document (0.3). SQLAlchemy models in `backend/app/models/`; migrations via Alembic.

## Entity-relationship diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                    users                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ PK  id              INTEGER / UUID                                            │
│     email           VARCHAR(255) UNIQUE NOT NULL                             │
│     hashed_password VARCHAR(255) NOT NULL                                    │
│     full_name       VARCHAR(255)                                             │
│     role            ENUM('admin','analyst','viewer') NOT NULL DEFAULT viewer │
│     is_active       BOOLEAN NOT NULL DEFAULT true                            │
│     created_at      TIMESTAMP TZ NOT NULL                                    │
│     updated_at      TIMESTAMP TZ NOT NULL                                    │
└───────────────┬─────────────────────────────────────────────────────────────┘
                │ 1
                │
                │ *
┌───────────────▼─────────────────────────────────────────────────────────────┐
│                              user_sessions                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ PK  id              INTEGER / UUID                                            │
│ FK  user_id         → users.id ON DELETE CASCADE                              │
│     refresh_token_jti VARCHAR(64) UNIQUE NOT NULL  -- JWT ID for revocation   │
│     expires_at      TIMESTAMP TZ NOT NULL                                    │
│     revoked_at      TIMESTAMP TZ NULL                                        │
│     ip_address      VARCHAR(45)                                              │
│     user_agent      VARCHAR(512)                                             │
│     created_at      TIMESTAMP TZ NOT NULL                                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                               uploaded_files                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ PK  id              INTEGER / UUID                                            │
│ FK  owner_id        → users.id ON DELETE SET NULL                            │
│     original_filename VARCHAR(512) NOT NULL  -- sanitised display name       │
│     stored_path     VARCHAR(1024) NOT NULL    -- relative under upload root   │
│     file_hash       CHAR(64) NOT NULL        -- SHA-256 hex                  │
│     mime_type       VARCHAR(128)                                             │
│     size_bytes      BIGINT NOT NULL                                          │
│     row_count       INTEGER NULL           -- populated after parse          │
│     column_count    INTEGER NULL                                             │
│     source            ENUM('upload','temp_asset') NOT NULL                   │
│     is_active         BOOLEAN DEFAULT true                                   │
│     created_at        TIMESTAMP TZ NOT NULL                                  │
│ UQ  (file_hash)       -- canonical file per hash; versions track re-uploads  │
└───────────────┬─────────────────────────────────────────────────────────────┘
                │ 1
                │
     ┌──────────┼──────────┬──────────────┬──────────────┐
     │ *        │ *        │ *            │ *            │ *
     ▼          ▼          ▼              ▼              ▼
┌─────────┐ ┌─────────┐ ┌────────────┐ ┌─────────────┐ ┌────────────┐
│file_    │ │security_│ │analysis_   │ │audit_logs   │ │csv_data    │
│versions │ │scans    │ │jobs        │ │(optional    │ │(optional   │
└─────────┘ └─────────┘ └─────┬──────┘ │ file link) │ │ import)    │
                                │        └─────────────┘ └────────────┘
                                │ 1
                                │ *
                    ┌───────────┼───────────┐
                    │ *         │ *         │ 1
                    ▼           ▼           ▼
              ┌──────────┐ ┌──────────┐ ┌─────────────┐
              │job_      │ │model_    │ │insights     │
              │progress  │ │results   │ │(generated)  │
              └──────────┘ └──────────┘ └─────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                               file_versions                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ PK  id              INTEGER / UUID                                            │
│ FK  file_id         → uploaded_files.id ON DELETE CASCADE                    │
│ FK  uploaded_by     → users.id ON DELETE SET NULL                            │
│     version_number  INTEGER NOT NULL                                         │
│     upload_event    VARCHAR(64) NOT NULL   -- e.g. re_upload, asset_select   │
│     notes           TEXT NULL                                                │
│     created_at      TIMESTAMP TZ NOT NULL                                  │
│ UQ  (file_id, version_number)                                                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              security_scans                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ PK  id              INTEGER / UUID                                            │
│ FK  file_id         → uploaded_files.id ON DELETE CASCADE                    │
│     status          ENUM('safe','warning','blocked') NOT NULL                 │
│     risk_score      INTEGER NOT NULL DEFAULT 0     -- 0-100                  │
│     issues          JSON NOT NULL DEFAULT []       -- list of issue strings  │
│     recommended_action VARCHAR(512)                                          │
│     file_hash       CHAR(64) NOT NULL                                        │
│     scanned_at      TIMESTAMP TZ NOT NULL                                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              analysis_jobs                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ PK  id              INTEGER / UUID                                            │
│ FK  file_id         → uploaded_files.id ON DELETE CASCADE                    │
│ FK  user_id         → users.id ON DELETE SET NULL                            │
│ FK  file_version_id → file_versions.id ON DELETE SET NULL                    │
│     job_type        VARCHAR(64) NOT NULL   -- eda, regression, business, …   │
│     status          ENUM('queued','running','complete','failed','cancelled') │
│     progress        SMALLINT DEFAULT 0     -- 0-100                          │
│     params          JSON NOT NULL DEFAULT {}                                 │
│     error_message   TEXT NULL                                                │
│     error_trace     TEXT NULL                                                │
│     started_at      TIMESTAMP TZ NULL                                        │
│     completed_at    TIMESTAMP TZ NULL                                        │
│     created_at      TIMESTAMP TZ NOT NULL                                    │
└───────────────┬─────────────────────────────────────────────────────────────┘
                │ 1
                │ 0..1
                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                               job_progress                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ PK  id              INTEGER / UUID                                            │
│ FK  job_id          → analysis_jobs.id ON DELETE CASCADE UNIQUE              │
│     progress        SMALLINT NOT NULL DEFAULT 0                              │
│     stage           VARCHAR(128) NOT NULL    -- e.g. training, exporting     │
│     message         VARCHAR(512)                                             │
│     updated_at      TIMESTAMP TZ NOT NULL                                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                               model_results                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ PK  id              INTEGER / UUID                                            │
│ FK  job_id          → analysis_jobs.id ON DELETE CASCADE UNIQUE              │
│ FK  file_id         → uploaded_files.id ON DELETE CASCADE                    │
│     result_type     VARCHAR(64) NOT NULL                                     │
│     algorithm       VARCHAR(64) NULL                                         │
│     metrics         JSON NOT NULL DEFAULT {}                                   │
│     payload         JSON NOT NULL            -- charts tables, matrices      │
│     explainability  JSON NULL                                                │
│     created_at      TIMESTAMP TZ NOT NULL                                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          generated_insights                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ PK  id              INTEGER / UUID                                            │
│ FK  job_id          → analysis_jobs.id ON DELETE CASCADE                     │
│ FK  result_id       → model_results.id ON DELETE SET NULL                    │
│     summary_text    TEXT NOT NULL                                            │
│     source          ENUM('llm','fallback') NOT NULL                          │
│     prompt_version  VARCHAR(32) NULL                                         │
│     created_at      TIMESTAMP TZ NOT NULL                                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                                 audit_logs                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ PK  id              INTEGER / UUID                                            │
│ FK  user_id         → users.id ON DELETE SET NULL                            │
│ FK  file_id         → uploaded_files.id ON DELETE SET NULL                   │
│ FK  job_id          → analysis_jobs.id ON DELETE SET NULL                    │
│     event_type      VARCHAR(64) NOT NULL   -- upload, scan, analysis, …    │
│     action          VARCHAR(128) NOT NULL                                    │
│     result            VARCHAR(32) NOT NULL   -- success, failure, blocked    │
│     file_hash       CHAR(64) NULL                                            │
│     filename        VARCHAR(512) NULL                                        │
│     ip_address      VARCHAR(45) NULL                                         │
│     metadata        JSON NULL                                                │
│     created_at      TIMESTAMP TZ NOT NULL                                    │
│ IDX (event_type, created_at), (user_id, created_at), (file_hash)           │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                                  csv_data                                    │
│                    (optional — SQL analysis import)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ PK  id              BIGINT                                                    │
│ FK  file_id         → uploaded_files.id ON DELETE CASCADE                    │
│     row_index       INTEGER NOT NULL                                         │
│     data            JSON NOT NULL          -- row as column→value map        │
│     created_at      TIMESTAMP TZ NOT NULL                                    │
│ IDX (file_id, row_index)                                                     │
└─────────────────────────────────────────────────────────────────────────────┘

Alternative for PostgreSQL: dynamic table `csv_import_{file_id}` created per import;
SQLite mode uses `csv_data` JSON rows. Migration notes below.
```

## Indexes (summary)

| Table | Index | Purpose |
|-------|-------|---------|
| `uploaded_files` | `file_hash` | Duplicate detection |
| `uploaded_files` | `owner_id, created_at` | User upload history |
| `analysis_jobs` | `status, created_at` | Active job queries |
| `audit_logs` | `event_type, created_at` | Admin audit UI |
| `user_sessions` | `refresh_token_jti` | Token revocation lookup |

## Alembic migration plan

| Revision | Branch commit | Description |
|----------|---------------|-------------|
| `001_initial` | feat(db) | `users`, `user_sessions` |
| `002_files` | feat(upload) | `uploaded_files` |
| `003_security` | feat(security) | `security_scans` |
| `004_audit` | feat(audit) | `audit_logs` |
| `005_versions` | feat(versioning) | `file_versions`; unique constraint on `uploaded_files.file_hash` |
| `006_jobs` | feat(background) | `analysis_jobs`, `job_progress` |
| `007_results` | feat(eda) + models | `model_results` (EDA stored as result_type `eda`) |
| `008_csv_data` | feat(sql) | `csv_data` |
| `009_insights` | feat(insights) | `generated_insights` |
| `010_indexes` | chore | Performance indexes, slow-query log table optional |

### Migration conventions

- All migrations in `backend/alembic/versions/` with descriptive slugs.
- Never use `Base.metadata.create_all()` in production startup; Docker CMD runs `alembic upgrade head`.
- SQLite: use batch mode for ALTER TABLE; JSON columns as `JSON` type.
- PostgreSQL: enable `UUID` extension if using UUID PKs; `ENUM` via Alembic `sa.Enum` with `create_type=True`.
- Downgrade scripts required for every revision.
- Seed migration (optional): default Admin user only in dev via env flag `SEED_ADMIN=true`.

### Slow query log (monitoring)

Optional table `slow_query_log`:

| Column | Type |
|--------|------|
| id | PK |
| statement_hash | VARCHAR(64) |
| duration_ms | FLOAT |
| logged_at | TIMESTAMP TZ |

Populated by SQLAlchemy event listeners when query duration exceeds threshold.

## Data retention notes

- Deleting `uploaded_files` cascades scans, versions, jobs, results (Admin only).
- Physical file on disk removed only when no `uploaded_files` row references hash (reference counting via versions).
- Audit logs retained even if file deleted (`file_id` SET NULL).

## PostgreSQL vs SQLite

| Concern | SQLite (dev) | PostgreSQL (prod) |
|---------|--------------|-------------------|
| Connection | `sqlite:///./data/app.db` | `DATABASE_URL` env |
| JSON | Native JSON | JSONB preferred |
| Concurrent writes | Limited | Full |
| SQL import | `csv_data` table | Optional dedicated schema |

`database.py` reads `DATABASE_URL` from `config.py`; no models defined in `database.py`.
