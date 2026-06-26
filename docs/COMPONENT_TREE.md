# React component tree — predictive-security-analytics-lab

> Phase 0 planning document (0.4). All components in `frontend/src/`; data fetching only in `hooks/` and `api/`.

## Route map

```
/                     → HomePage
/login                → LoginPage
/register             → RegisterPage (conditional)
/dashboard            → DashboardPage (auth)
/upload               → UploadPage (Analyst+)
/assets               → AssetsPage (Analyst+)
/files/:fileId        → FileDetailPage
  /eda                → EDADashboard (nested or tab)
  /sql                → SQLAnalysisPage
  /models             → ModelWorkbenchPage
  /business           → BusinessDashboardPage (pest workflow)
  /security           → SecurityScanPanel
  /versions           → VersionHistoryPage
  /export             → ExportPage
/jobs/:jobId          → JobProgressPage
/admin/users          → AdminUsersPage (Admin)
/admin/audit          → AuditLogPage (Admin)
/health               → HealthStatusPage (public dev panel)
*                     → NotFoundPage
```

## Component tree

```
App
├── AppProviders
│   ├── AuthProvider          # auth context: user, token, login/logout
│   ├── ThemeProvider         # optional light/dark
│   └── QueryClientProvider   # if react-query adopted; else custom hooks
├── AppLayout
│   ├── SkipLink
│   ├── AppHeader
│   │   ├── Logo
│   │   ├── MainNav                 # links: Dashboard, Upload, Assets, Health
│   │   └── UserMenu                # data: user from useAuth()
│   ├── AppSidebar (desktop)        # file-scoped nav when fileId in route
│   └── AppFooter
├── ErrorBoundary
└── AppRoutes
    ├── PublicRoute
    │   ├── LoginPage
    │   │   ├── LoginForm             # data: useLogin() → api/auth
    │   │   └── FormErrorAlert
    │   └── RegisterPage
    │       └── RegisterForm          # data: useRegister()
    ├── ProtectedRoute                # redirects if !token
    │   ├── DashboardPage
    │   │   ├── PageHeader
    │   │   ├── RecentUploadsList     # data: useUploads()
    │   │   ├── RecentJobsList        # data: useJobs()
    │   │   └── QuickActionsCard
    │   ├── UploadPage
    │   │   ├── UploadForm            # data: useUpload()
    │   │   │   ├── FileInput         # client .csv validation
    │   │   │   ├── UploadProgressBar
    │   │   │   └── UploadErrorList
    │   │   └── ScannerResultPanel    # props: scanResult { status, issues, risk_score }
    │   │       ├── ScanStatusBadge   # safe | warning | blocked
    │   │       └── IssuesList          # escaped text only
    │   ├── AssetsPage
    │   │   ├── AssetsFileList        # data: useAssets()
    │   │   └── AssetSelectButton     # data: useSelectAsset()
    │   ├── FileDetailPage
    │   │   ├── FileMetadataCard      # data: useFile(fileId)
    │   │   ├── FileTabNav
    │   │   ├── SecurityScanPanel     # data: useScan(fileId)
    │   │   ├── BlockedAnalysisGate   # blocks child routes if status=blocked
    │   │   └── Outlet / tabs:
    │   │       ├── EDADashboard
    │   │       │   ├── EDASummaryCards       # rows, cols, duplicates, missing
    │   │       │   ├── ColumnTypeTable       # data: eda.columns
    │   │       │   ├── QualityWarningsList
    │   │       │   ├── SuggestedAnalysesChips # data: useTaskDetection()
    │   │       │   └── EDAChartGrid
    │   │       │       ├── HistogramChart      # charts/ — props: chartData
    │   │       │       ├── BarChart
    │   │       │       ├── ScatterChart
    │   │       │       ├── LineChart
    │   │       │       ├── MissingValuesChart
    │   │       │       ├── CorrelationHeatmap
    │   │       │       ├── ValueCountChart
    │   │       │       └── TimeSeriesPreviewChart
    │   │       ├── SQLAnalysisPage
    │   │       │   ├── SQLPresetList         # data: useSQLPresets()
    │   │       │   ├── SQLQueryEditor
    │   │       │   └── SQLResultsTable       # PaginatedTable
    │   │       ├── ModelWorkbenchPage
    │   │       │   ├── TaskDetectionPanel    # data: useDetectTasks()
    │   │       │   ├── ModelTypeSelector     # regression | classification | …
    │   │       │   ├── ColumnPicker          # target + features from eda
    │   │       │   ├── AlgorithmSelect
    │   │       │   ├── RunAnalysisButton     # data: useRunModel()
    │   │       │   └── ModelResultsView
    │   │       │       ├── MetricsTable
    │   │       │       ├── ConfusionMatrixChart
    │   │       │       ├── ActualVsPredictedChart
    │   │       │       ├── ResidualsChart
    │   │       │       ├── ClusterScatterChart
    │   │       │       ├── PCAVarianceChart
    │   │       │       ├── ForecastChart
    │   │       │       ├── FeatureImportanceChart
    │   │       │       ├── ShapSummaryPanel
    │   │       │       ├── ConfidenceScoresTable
    │   │       │       └── PredictionsTable    # PaginatedTable
    │   │       ├── BusinessDashboardPage       # pest control workflow
    │   │       │   ├── BusinessColumnMapper    # map revenue, cost, date cols
    │   │       │   ├── KPICardGrid
    │   │       │   │   └── KPICard             # props: label, value, trend, direction
    │   │       │   ├── RevenueByMonthChart
    │   │       │   ├── JobsByTechnicianChart
    │   │       │   ├── PestTypeBreakdownChart
    │   │       │   └── BusinessInsightsPanel
    │   │       ├── VersionHistoryPage
    │   │       │   ├── VersionTimeline         # data: useFileVersions()
    │   │       │   └── VersionCompareView      # data: useVersionCompare()
    │   │       └── ExportPage
    │   │           ├── ExportFormatSelector    # json | csv | pdf
    │   │           ├── ExportOptionsForm
    │   │           └── ExportDownloadButton    # data: useExport()
    │   ├── JobProgressPage
    │   │   ├── JobProgressBar            # data: useJobProgress() polling
    │   │   ├── JobStageLabel
    │   │   ├── CancelJobButton           # data: useCancelJob()
    │   │   └── JobErrorPanel
    │   └── AdminUsersPage
    │       ├── UsersTable
    │       └── UserRoleEditor
    ├── AuditLogPage
    │   ├── AuditFilters
    │   └── AuditLogTable               # PaginatedTable
    ├── HealthStatusPage
    │   ├── HealthStatusPanel           # data: useHealth()
    │   └── MetricsSummaryCards         # data: useMetrics()
    └── NotFoundPage
```

## Shared components (`components/`)

| Component | Parent usage | Data consumed |
|-----------|--------------|---------------|
| `PaginatedTable` | SQL, predictions, audit | `columns`, `rows`, `page`, `onPageChange` |
| `LoadingSpinner` | global | `label?` |
| `EmptyState` | lists | `message`, `action?` |
| `FormErrorAlert` | forms | `error` string |
| `ScanStatusBadge` | scanner panels | `status: safe\|warning\|blocked` |
| `TrendIndicator` | KPICard | `direction: up\|down\|neutral` |
| `InsightsPanel` | results, business | `summary`, `source` |
| `PageHeader` | all pages | `title`, `subtitle?`, `actions?` |
| `ProtectedRoute` | routes | `roles?[]` from auth |
| `BlockedAnalysisGate` | file detail | `scanStatus` |

## Chart components (`charts/`)

Pure presentation — no API calls; receive serialised chart data from parent/hooks.

| Chart | Props (summary) |
|-------|-----------------|
| `HistogramChart` | `data: { bin, count }[]`, `title`, `xLabel` |
| `BarChart` | `data: { label, value }[]`, `title` |
| `ScatterChart` | `data: { x, y }[]`, `title` |
| `LineChart` | `data: { x, y }[]`, `title` |
| `MissingValuesChart` | `data: { column, missing_pct }[]` |
| `CorrelationHeatmap` | `matrix`, `labels[]` |
| `ValueCountChart` | `data: { category, count }[]` |
| `TimeSeriesPreviewChart` | `data: { date, value }[]` |
| `ActualVsPredictedChart` | `data: { actual, predicted }[]` |
| `ResidualsChart` | `data: { predicted, residual }[]` |
| `ConfusionMatrixChart` | `matrix[][]`, `labels[]` |
| `ClusterScatterChart` | `data: { x, y, cluster }[]` |
| `PCAVarianceChart` | `data: { component, variance }[]` |
| `ForecastChart` | `historical[]`, `forecast[]` |
| `FeatureImportanceChart` | `data: { feature, importance }[]` |
| `ShapSummaryPanel` | `shapValues`, `features[]` |
| `RevenueByMonthChart` | business time series |
| `JobsByTechnicianChart` | categorical breakdown |

## Hooks (`hooks/`)

| Hook | API modules | Returns |
|------|-------------|---------|
| `useAuth` | `api/auth` | user, token, login, logout, isAuthenticated |
| `useLogin` | `api/auth` | mutate, loading, error |
| `useRegister` | `api/auth` | mutate, loading, error |
| `useHealth` | `api/monitoring` | health status |
| `useMetrics` | `api/monitoring` | metrics |
| `useUpload` | `api/uploads` | uploadFile, progress, error |
| `useUploads` | `api/uploads` | list, pagination |
| `useFile` | `api/uploads` | metadata |
| `useAssets` | `api/assets` | file list |
| `useSelectAsset` | `api/assets` | select, loading |
| `useScan` | `api/scans` | scan result, rescan |
| `useEDA` | `api/eda` | eda response, runEDA |
| `useTaskDetection` | `api/models` | suggestions |
| `useSQLPresets` | `api/sql` | presets, runPreset |
| `useRunModel` | `api/models` | start job, result |
| `useJob` | `api/jobs` | status |
| `useJobProgress` | `api/jobs` | polling progress |
| `useCancelJob` | `api/jobs` | cancel |
| `useBusinessAnalytics` | `api/business` | report, kpis |
| `useInsights` | `api/insights` | summary |
| `useExport` | `api/export` | download blob |
| `useFileVersions` | `api/uploads` | versions |
| `useVersionCompare` | `api/uploads` | diff |
| `useAuditLogs` | `api/audit` | logs (admin) |

## API modules (`api/`)

| Module | Responsibility |
|--------|----------------|
| `client.js` | base URL, fetch wrapper, auth header, error parsing |
| `auth.js` | login, register, refresh, logout, me |
| `uploads.js` | upload, list, delete, preview, versions |
| `assets.js` | list, select |
| `scans.js` | run, get |
| `eda.js` | run, get, column detail |
| `sql.js` | import, query, presets |
| `models.js` | regression, classification, clustering, pca, timeseries, similarity |
| `jobs.js` | list, get, progress, cancel, result |
| `business.js` | analyze, kpis |
| `insights.js` | generate, get |
| `export.js` | json, csv, pdf download |
| `monitoring.js` | health, metrics |
| `audit.js` | list |
| `users.js` | admin CRUD |

## Types (`types/`)

| File | Contents |
|------|----------|
| `auth.ts` | User, TokenResponse, Role |
| `upload.ts` | UploadResponse, FileMetadata |
| `scan.ts` | ScanResult, ScanStatus |
| `eda.ts` | EDAResponse, ColumnSummary |
| `models.ts` | RegressionResult, ClassificationResult, … |
| `business.ts` | KPICard, BusinessReport |
| `jobs.ts` | JobStatus, JobProgress |
| `insights.ts` | InsightResponse |
| `api.ts` | StandardError, PaginatedResponse |

## State flow diagram

```
User action → Page component → custom hook → api/* → FastAPI
                    ↑                │
                    └──── setState / poll job progress
Chart components ← plain props ← hook normalises API payload
```

## Accessibility & UX cross-cutting

- All interactive elements: `aria-label` or visible label.
- `prefers-reduced-motion`: disable chart animations via Recharts props.
- Keyboard: focus trap in modals; tab order in forms.
- Status colours: green (safe), amber (warning), red (blocked) — WCAG AA contrast.

## File size limits (enforced in planning)

- No component file > 200 lines; split e.g. `ModelResultsView` → per-model subviews.
- No fetch outside `api/`.
