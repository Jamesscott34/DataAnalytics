import { API_BASE_URL } from './client.js';
import { getAccessToken } from './tokenStorage.js';

function authHeaders() {
  const headers = {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  };
  const token = getAccessToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

export async function generateInsight({ resultId, analysisType, jobId = null }) {
  const response = await fetch(`${API_BASE_URL}/insights/generate`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({
      result_id: resultId,
      analysis_type: analysisType,
      job_id: jobId,
    }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message ?? body.detail ?? 'Insight generation failed');
  }
  return response.json();
}
