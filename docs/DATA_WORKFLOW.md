# Data workflow

> Stub — expanded in `docs(all)` task (Task 34).

Planned flow: upload or select asset → security scan → EDA → analysis (ML/SQL/business) → insights → export.

## Pest control demo workflow

Use `temp_assets/pest_control_sample.csv` for an end-to-end pest control analytics
demo:

1. Open **Sample datasets** and select `pest_control_sample.csv`.
2. Open **Business analytics** for the selected file.
3. Click **Apply pest control preset** to map:
   - `job_date` as the date column
   - `revenue` as the revenue column
   - `cost` as the cost column
4. Click **Calculate KPIs** to review revenue, cost, gross margin, margin %, and
   monthly revenue.
5. Generate **AI insights** from the KPI report, then export the full analysis
   from the scan/export workflow.

See [TASKS.md](./TASKS.md) for implementation order.
