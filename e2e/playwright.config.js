import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { defineConfig, devices } from '@playwright/test';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const PORT = process.env.E2E_PORT ?? '5173';
const API_PORT = process.env.E2E_API_PORT ?? '8000';

export default defineConfig({
  testDir: './tests',
  timeout: 120_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? 'github' : 'list',
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    trace: 'on-first-retry',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      command:
        'cd ../backend && python -m venv .venv-e2e 2>/dev/null; .venv-e2e/bin/pip install -q -r requirements-dev.txt && .venv-e2e/bin/alembic upgrade head && CORS_ORIGINS=http://127.0.0.1:' +
        PORT +
        ',http://localhost:' +
        PORT +
        ' .venv-e2e/bin/uvicorn app.main:app --host 127.0.0.1 --port ' +
        API_PORT,
      url: `http://127.0.0.1:${API_PORT}/api/v1/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      cwd: __dirname,
    },
    {
      command: `npm run dev -- --host 127.0.0.1 --port ${PORT}`,
      url: `http://127.0.0.1:${PORT}`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      cwd: `${__dirname}/../frontend`,
    },
  ],
});
