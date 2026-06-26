/**
 * Browser hashing helpers.
 */

/**
 * Calculate a SHA-256 hash for a File in the browser.
 *
 * @param {File} file - File to hash.
 * @returns {Promise<string>} Lowercase SHA-256 hex digest.
 */
export async function sha256File(file) {
  const buffer = await file.arrayBuffer();
  const digest = await crypto.subtle.digest('SHA-256', buffer);
  return Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, '0'))
    .join('');
}
