import { useState } from 'react';
import { useAssetIntegrity } from '../hooks/useAssetIntegrity.jsx';

/**
 * AssetIntegrityGate
 *
 * Prompts once per session for manifest setup/unlock and shows folder changes.
 */
export function AssetIntegrityGate() {
  const {
    status,
    loading,
    error,
    showSetup,
    showUnlock,
    showChanges,
    initialize,
    unlock,
    applyAllChanges,
    dismissChanges,
    canManageIntegrity,
  } = useAssetIntegrity();

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  if (!canManageIntegrity || (!showSetup && !showUnlock && !showChanges)) {
    return null;
  }

  const resetFields = () => {
    setPassword('');
    setConfirmPassword('');
  };

  const handleInitialize = async (event) => {
    event.preventDefault();
    await initialize(password, confirmPassword);
    resetFields();
  };

  const handleUnlock = async (event) => {
    event.preventDefault();
    await unlock(password);
    resetFields();
  };

  return (
    <div className="integrity-overlay" role="presentation">
      <section
        className="integrity-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="integrity-modal-heading"
      >
        {showSetup && (
          <>
            <h2 id="integrity-modal-heading">Create integrity manifest</h2>
            <p>
              No password-protected manifest exists yet. Create one to store SHA-256
              hashes for files in <code>temp_assets</code> and <code>assets</code>.
            </p>
            <p>
              Discovered files: <strong>{status?.discovered_file_count ?? 0}</strong>
            </p>
            <form onSubmit={handleInitialize}>
              <label htmlFor="integrity-password">Manifest password</label>
              <input
                id="integrity-password"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="new-password"
                required
                minLength={8}
              />
              <label htmlFor="integrity-confirm-password">Confirm password</label>
              <input
                id="integrity-confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                autoComplete="new-password"
                required
                minLength={8}
              />
              {error && <p role="alert">{error}</p>}
              <button type="submit" disabled={loading}>
                {loading ? 'Creating…' : 'Create manifest'}
              </button>
            </form>
          </>
        )}

        {showUnlock && (
          <>
            <h2 id="integrity-modal-heading">Unlock integrity manifest</h2>
            <p>
              Enter the manifest password once this session so the app can compare
              folder files against the stored SHA-256 hashes.
            </p>
            <form onSubmit={handleUnlock}>
              <label htmlFor="integrity-unlock-password">Manifest password</label>
              <input
                id="integrity-unlock-password"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="current-password"
                required
              />
              {error && <p role="alert">{error}</p>}
              <button type="submit" disabled={loading}>
                {loading ? 'Unlocking…' : 'Unlock manifest'}
              </button>
            </form>
          </>
        )}

        {showChanges && status && (
          <>
            <h2 id="integrity-modal-heading">Asset folder changes detected</h2>
            <p>
              The backend scanned <code>temp_assets</code> and <code>assets</code> on
              startup and found differences from the manifest.
            </p>

            {status.new_files.length > 0 && (
              <div>
                <h3>New files</h3>
                <ul>
                  {status.new_files.map((file) => (
                    <li key={file.path}>
                      <code>{file.path}</code> — SHA-256 {file.sha256}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {status.modified_files.length > 0 && (
              <div>
                <h3>Updated files</h3>
                <ul>
                  {status.modified_files.map((file) => (
                    <li key={file.path}>
                      <code>{file.path}</code>
                      <div>Stored: {file.stored_sha256}</div>
                      <div>Current: {file.current_sha256}</div>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {status.removed_files.length > 0 && (
              <div>
                <h3>Removed files</h3>
                <ul>
                  {status.removed_files.map((path) => (
                    <li key={path}>
                      <code>{path}</code>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {error && <p role="alert">{error}</p>}
            <div className="duplicate-actions">
              <button type="button" onClick={applyAllChanges} disabled={loading}>
                {loading ? 'Updating…' : 'Add/update manifest entries'}
              </button>
              <button
                type="button"
                className="secondary-button"
                onClick={dismissChanges}
                disabled={loading}
              >
                Review later
              </button>
            </div>
          </>
        )}
      </section>
    </div>
  );
}
