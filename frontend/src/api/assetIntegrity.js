/**
 * Asset integrity manifest API calls.
 */

import { apiRequest } from './client.js';

const INTEGRITY_SESSION_KEY = 'psal_integrity_unlocked';

/**
 * Read whether this browser session already unlocked the manifest.
 *
 * @returns {boolean}
 */
export function isIntegritySessionUnlocked() {
  return sessionStorage.getItem(INTEGRITY_SESSION_KEY) === 'true';
}

/**
 * Mark the manifest as unlocked for this browser session.
 */
export function markIntegritySessionUnlocked() {
  sessionStorage.setItem(INTEGRITY_SESSION_KEY, 'true');
}

/**
 * Clear the browser-session unlock marker.
 */
export function clearIntegritySessionUnlocked() {
  sessionStorage.removeItem(INTEGRITY_SESSION_KEY);
}

/**
 * Fetch current asset integrity status.
 *
 * @returns {Promise<Object>}
 */
export function fetchIntegrityStatus() {
  return apiRequest('/asset-integrity/status');
}

/**
 * Create the encrypted integrity manifest.
 *
 * @param {string} password
 * @param {string} confirmPassword
 * @returns {Promise<Object>}
 */
export function initializeIntegrityManifest(password, confirmPassword) {
  return apiRequest('/asset-integrity/initialize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      password,
      confirm_password: confirmPassword,
    }),
  });
}

/**
 * Unlock the encrypted integrity manifest.
 *
 * @param {string} password
 * @returns {Promise<Object>}
 */
export function unlockIntegrityManifest(password) {
  return apiRequest('/asset-integrity/unlock', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password }),
  });
}

/**
 * Apply approved manifest updates.
 *
 * @param {{ addOrUpdate?: string[], remove?: string[] }} changes
 * @returns {Promise<Object>}
 */
export function applyIntegrityChanges(changes) {
  return apiRequest('/asset-integrity/apply', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      add_or_update: changes.addOrUpdate ?? [],
      remove: changes.remove ?? [],
    }),
  });
}
