/**
 * Machine learning model API calls.
 */

import { API_BASE_URL } from './client.js';
import { getAccessToken } from './tokenStorage.js';

function authHeaders(json = true) {
  const headers = { Accept: 'application/json' };
  if (json) {
    headers['Content-Type'] = 'application/json';
  }
  const token = getAccessToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

export async function getModelRegistry() {
  const response = await fetch(`${API_BASE_URL}/models/registry`, {
    headers: authHeaders(false),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message ?? body.detail ?? 'Failed to load model registry');
  }
  return response.json();
}

/**
 * @param {number} fileId
 * @param {{
 *   algorithm: string,
 *   targetColumn: string,
 *   featureColumns: string[],
 *   testSize?: number,
 *   randomState?: number,
 * }} payload
 */
export async function trainRegression(fileId, payload) {
  const response = await fetch(`${API_BASE_URL}/models/${fileId}/regression`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({
      algorithm: payload.algorithm,
      target_column: payload.targetColumn,
      feature_columns: payload.featureColumns,
      test_size: payload.testSize ?? 0.2,
      random_state: payload.randomState ?? 42,
    }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message ?? body.detail ?? 'Regression training failed');
  }
  return response.json();
}

export async function getRegressionResult(resultId) {
  const response = await fetch(`${API_BASE_URL}/models/results/${resultId}`, {
    headers: authHeaders(false),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message ?? body.detail ?? 'Model result not found');
  }
  return response.json();
}

/**
 * @param {number} fileId
 * @param {{
 *   algorithm: string,
 *   targetColumn: string,
 *   featureColumns: string[],
 *   testSize?: number,
 *   randomState?: number,
 * }} payload
 */
export async function trainClassification(fileId, payload) {
  const response = await fetch(`${API_BASE_URL}/models/${fileId}/classification`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({
      algorithm: payload.algorithm,
      target_column: payload.targetColumn,
      feature_columns: payload.featureColumns,
      test_size: payload.testSize ?? 0.2,
      random_state: payload.randomState ?? 42,
    }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message ?? body.detail ?? 'Classification training failed');
  }
  return response.json();
}
