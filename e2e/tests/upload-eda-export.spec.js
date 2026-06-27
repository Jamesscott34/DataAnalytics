import { expect, test } from '@playwright/test';
import path from 'node:path';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const sampleCsv = path.join(__dirname, '../../temp_assets/pest_control_sample.csv');
const apiBase = process.env.E2E_API_BASE ?? 'http://127.0.0.1:8000/api/v1';

test('upload, EDA, and JSON export workflow', async ({ page, request }) => {
  const email = `e2e-${Date.now()}@example.com`;
  const password = 'password123';

  await request.post(`${apiBase}/auth/register`, {
    data: { email, password, role: 'analyst' },
  });
  const login = await request.post(`${apiBase}/auth/login`, {
    data: { email, password },
  });
  expect(login.ok()).toBeTruthy();
  const { access_token: token } = await login.json();

  await page.goto('/login');
  await page.getByLabel(/email/i).fill(email);
  await page.getByLabel(/password/i).fill(password);
  await page.getByRole('button', { name: /sign in/i }).click();
  await expect(page).toHaveURL(/dashboard/, { timeout: 30_000 });

  const csvBuffer = await readFile(sampleCsv);
  const uploadResponse = await request.post(`${apiBase}/uploads`, {
    headers: { Authorization: `Bearer ${token}` },
    multipart: {
      file: {
        name: 'pest_control_sample.csv',
        mimeType: 'text/csv',
        buffer: csvBuffer,
      },
    },
  });
  expect(uploadResponse.status()).toBe(201);
  const { file_id: fileId } = await uploadResponse.json();

  const edaResponse = await request.post(`${apiBase}/eda/${fileId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    data: { force_refresh: true },
  });
  expect(edaResponse.ok()).toBeTruthy();

  const quickScan = await request.post(`${apiBase}/files/${fileId}/quick-scan`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(quickScan.ok()).toBeTruthy();
  const { report_id: reportId } = await quickScan.json();

  const exportResponse = await request.post(`${apiBase}/export/json`, {
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    data: { report_id: reportId },
  });
  expect(exportResponse.ok()).toBeTruthy();

  await page.goto(`/eda/${fileId}`);
  await expect(page.getByRole('heading', { name: /exploratory analysis/i })).toBeVisible();
  await page.getByRole('button', { name: /run eda/i }).click();
  await expect(page.getByText('Rows')).toBeVisible({ timeout: 60_000 });
});
