import { useCallback, useEffect, useState } from 'react';
import {
  applyIntegrityChanges,
  fetchIntegrityStatus,
  initializeIntegrityManifest,
  isIntegritySessionUnlocked,
  markIntegritySessionUnlocked,
  unlockIntegrityManifest,
} from '../api/assetIntegrity.js';
import { useAuth } from './useAuth.jsx';

/**
 * useAssetIntegrity
 *
 * Loads integrity status for watched asset folders and exposes unlock/apply actions.
 *
 * @returns {Object}
 */
export function useAssetIntegrity() {
  const { user, isAuthenticated } = useAuth();
  const canManageIntegrity = Boolean(
    user && (user.role === 'admin' || user.role === 'analyst'),
  );
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showSetup, setShowSetup] = useState(false);
  const [showUnlock, setShowUnlock] = useState(false);
  const [showChanges, setShowChanges] = useState(false);

  const refreshStatus = useCallback(async () => {
    if (!canManageIntegrity) {
      setStatus(null);
      return null;
    }
    setLoading(true);
    setError(null);
    try {
      const nextStatus = await fetchIntegrityStatus();
      setStatus(nextStatus);
      return nextStatus;
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, [canManageIntegrity]);

  useEffect(() => {
    if (!isAuthenticated || !canManageIntegrity) {
      return;
    }
    refreshStatus().then((nextStatus) => {
      if (!nextStatus) {
        return;
      }
      if (nextStatus.setup_required) {
        setShowSetup(true);
        return;
      }
      if (!nextStatus.unlocked && !isIntegritySessionUnlocked()) {
        setShowUnlock(true);
        return;
      }
      const hasChanges =
        nextStatus.new_files.length > 0 ||
        nextStatus.modified_files.length > 0 ||
        nextStatus.removed_files.length > 0;
      if (nextStatus.unlocked && hasChanges) {
        setShowChanges(true);
      }
    });
  }, [isAuthenticated, canManageIntegrity, refreshStatus]);

  const initialize = async (password, confirmPassword) => {
    setError(null);
    await initializeIntegrityManifest(password, confirmPassword);
    markIntegritySessionUnlocked();
    setShowSetup(false);
    const nextStatus = await refreshStatus();
    if (
      nextStatus &&
      (nextStatus.new_files.length > 0 ||
        nextStatus.modified_files.length > 0 ||
        nextStatus.removed_files.length > 0)
    ) {
      setShowChanges(true);
    }
  };

  const unlock = async (password) => {
    setError(null);
    await unlockIntegrityManifest(password);
    markIntegritySessionUnlocked();
    setShowUnlock(false);
    const nextStatus = await refreshStatus();
    const hasChanges =
      nextStatus &&
      (nextStatus.new_files.length > 0 ||
        nextStatus.modified_files.length > 0 ||
        nextStatus.removed_files.length > 0);
    if (hasChanges) {
      setShowChanges(true);
    }
  };

  const applyAllChanges = async () => {
    if (!status) {
      return;
    }
    setError(null);
    await applyIntegrityChanges({
      addOrUpdate: [
        ...status.new_files.map((file) => file.path),
        ...status.modified_files.map((file) => file.path),
      ],
      remove: status.removed_files,
    });
    setShowChanges(false);
    await refreshStatus();
  };

  const dismissChanges = () => {
    setShowChanges(false);
  };

  return {
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
    refreshStatus,
    canManageIntegrity,
  };
}
