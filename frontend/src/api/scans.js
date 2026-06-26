/**
 * Security scan API calls.
 */

import { apiRequest } from './client.js';

/**
 * Fetch latest scan result for a file.
 *
 * @param {number} fileId - Uploaded file identifier.
 * @returns {Promise<Object>} Scan result payload.
 */
export async function fetchLatestScan(fileId) {
  return apiRequest(`/scans/${fileId}`);
}
