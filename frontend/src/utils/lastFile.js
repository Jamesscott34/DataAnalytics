const LAST_FILE_KEY = 'psa_last_file';

/**
 * Persist the most recently used dataset file for quick navigation.
 *
 * @param {{ file_id: number, filename: string }} file
 */
export function setLastFile(file) {
  if (!file?.file_id) {
    return;
  }
  localStorage.setItem(
    LAST_FILE_KEY,
    JSON.stringify({
      fileId: file.file_id,
      filename: file.filename,
      updatedAt: new Date().toISOString(),
    }),
  );
}

/**
 * @returns {{ fileId: number, filename: string, updatedAt: string } | null}
 */
export function getLastFile() {
  const raw = localStorage.getItem(LAST_FILE_KEY);
  if (!raw) {
    return null;
  }
  try {
    const parsed = JSON.parse(raw);
    if (!parsed?.fileId) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

export function clearLastFile() {
  localStorage.removeItem(LAST_FILE_KEY);
}
