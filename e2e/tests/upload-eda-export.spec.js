import { expect, test } from '@playwright/test';
import path from 'node:path';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const sampleCsv = path.join(__dirname, '../../temp_assets/pest_control_sample.csv');
const apiBase = process.env.E2E_API_BASE ?? 'http://127.0.0.1:8000/api/v1';
const MANIFEST_PASSWORD = 'password123';

/**
 * Prepare the asset integrity manifest so the UI overlay does not block clicks.
 */
async function ensureAssetIntegrity(request, token) {
  const authHeader = { Authorization: `Bearer ${token}` };
  const jsonHeader = { ...authHeader, 'Content-Type': 'application/json' };

  let status = await (
    await request.get(`${apiBase}/asset-integrity/status`, { headers: authHeader })
  ).json();

  if (status.setup_required) {
    const initRes = await request.post(`${apiBase}/asset-integrity/initialize`, {
      headers: jsonHeader,
      data: {
        password: MANIFEST_PASSWORD,
        confirm_password: MANIFEST_PASSWORD,
      },
    });
    expect(initRes.ok()).toBeTruthy();
    status = await (
      await request.get(`${apiBase}/asset-integrity/status`, { headers: authHeader })
    ).json();
  }

  if (!status.unlocked) {
    const unlockRes = await request.post(`${apiBase}/asset-integrity/unlock`, {
      headers: jsonHeader,
      data: { password: MANIFEST_PASSWORD },
    });
    expect(unlockRes.ok()).toBeTruthy();
    status = await (
      await request.get(`${apiBase}/asset-integrity/status`, { headers: authHeader })
    ).json();
  }

  const addOrUpdate = [
    ...status.new_files.map((file) => file.path),
    ...status.modified_files.map((file) => file.path),
  ];
  if (addOrUpdate.length > 0 || status.removed_files.length > 0) {
    const applyRes = await request.post(`${apiBase}/asset-integrity/apply`, {
      headers: jsonHeader,
      data: {
        add_or_update: addOrUpdate,
        remove: status.removed_files,
      },
    });
    expect(applyRes.ok()).toBeTruthy();
  }
}

/**
 * Upload a CSV file, reusing an existing upload when the API reports a duplicate.
 */
async function uploadCsv(request, token, buffer, filename) {
  const headers = { Authorization: `Bearer ${token}` };
  const response = await request.post(`${apiBase}/uploads`, {
    headers,
    multipart: {
      file: {
        name: filename,
        mimeType: 'text/csv',
        buffer,
      },
    },
  });

  if (response.status() === 201) {
    return (await response.json()).file_id;
  }

  if (response.status() === 409) {
    const body = await response.json();
    return body.existing_file.id;
  }

  expect(response.status()).toBe(201);
  return null;
}

/**
 * Dismiss any integrity modal still visible in the browser.
 */
async function dismissIntegrityOverlay(page) {
  const reviewLater = page.getByRole('button', { name: /review later/i });
  if (await reviewLater.isVisible({ timeout: 2000 }).catch(() => false)) {
    await reviewLater.click();
  }
}

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

  await ensureAssetIntegrity(request, token);

  await page.addInitScript(() => {
    sessionStorage.setItem('psal_integrity_unlocked', 'true');
  });

  await page.goto('/login');
  await page.getByLabel(/email/i).fill(email);
  await page.getByLabel(/password/i).fill(password);
  await page.getByRole('button', { name: /sign in/i }).click();
  await expect(page).toHaveURL(/dashboard/, { timeout: 30_000 });

  const csvBuffer = await readFile(sampleCsv);
  const fileId = await uploadCsv(request, token, csvBuffer, 'pest_control_sample.csv');

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
  await dismissIntegrityOverlay(page);
  await expect(page.getByRole('heading', { name: /exploratory analysis/i })).toBeVisible();
  await page.getByRole('button', { name: /run eda/i }).click();
  await expect(page.getByText('Rows')).toBeVisible({ timeout: 60_000 });
});
