/**
 * Monitoring and health API calls.
 */

import { apiRequest } from './client.js';

/**
 * Fetch the backend liveness health check.
 *
 * @returns {Promise<{ status: string }>} Health payload.
 */
export async function fetchHealth() {
  return apiRequest('/health');
}
