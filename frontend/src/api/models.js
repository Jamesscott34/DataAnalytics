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

export async function runClustering(fileId, payload) {
  const response = await fetch(`${API_BASE_URL}/models/${fileId}/clustering`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({
      algorithm: payload.algorithm,
      feature_columns: payload.featureColumns,
      n_clusters: payload.nClusters ?? 3,
      max_k: payload.maxK ?? 8,
      random_state: payload.randomState ?? 42,
    }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message ?? body.detail ?? 'Clustering failed');
  }
  return response.json();
}

export async function runPca(fileId, payload) {
  const response = await fetch(`${API_BASE_URL}/models/${fileId}/pca`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({
      feature_columns: payload.featureColumns,
      n_components: payload.nComponents ?? 2,
      random_state: payload.randomState ?? 42,
    }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message ?? body.detail ?? 'PCA failed');
  }
  return response.json();
}

/**
 * @param {number} fileId
 * @param {{
 *   algorithm: string,
 *   dateColumn: string,
 *   valueColumn: string,
 *   forecastPeriods?: number,
 *   trainRatio?: number,
 *   window?: number,
 *   arLags?: number,
 *   arimaP?: number,
 *   arimaD?: number,
 *   arimaQ?: number,
 *   seasonalPeriod?: number | null,
 * }} payload
 */
export async function runTimeseries(fileId, payload) {
  const response = await fetch(`${API_BASE_URL}/models/${fileId}/timeseries`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({
      algorithm: payload.algorithm,
      date_column: payload.dateColumn,
      value_column: payload.valueColumn,
      forecast_periods: payload.forecastPeriods ?? 5,
      train_ratio: payload.trainRatio ?? 0.75,
      window: payload.window ?? 3,
      ar_lags: payload.arLags ?? 3,
      arima_p: payload.arimaP ?? 1,
      arima_d: payload.arimaD ?? 1,
      arima_q: payload.arimaQ ?? 1,
      seasonal_period: payload.seasonalPeriod ?? null,
    }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message ?? body.detail ?? 'Time series forecast failed');
  }
  return response.json();
}

export async function runSimilarity(fileId, payload) {
  const response = await fetch(`${API_BASE_URL}/models/${fileId}/similarity`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({
      mode: payload.mode,
      id_column: payload.idColumn || null,
      feature_columns: payload.featureColumns,
      top_n: payload.topN ?? 10,
    }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message ?? body.detail ?? 'Similarity analysis failed');
  }
  return response.json();
}
