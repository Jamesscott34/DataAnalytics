import { Link } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { addGroupMember, listGroups } from '../api/groups.js';

/**
 * AddToGroupPanel
 *
 * Lets users add an uploaded file to an existing dataset group.
 */
export function AddToGroupPanel({ fileId, filename }) {
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedGroupId, setSelectedGroupId] = useState('');
  const [tableAlias, setTableAlias] = useState('');
  const [adding, setAdding] = useState(false);
  const [addedToGroup, setAddedToGroup] = useState(null);

  const loadGroups = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await listGroups();
      setGroups(response.items ?? []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGroups();
  }, [fileId]);

  const availableGroups = groups.filter(
    (group) => !group.members.some((member) => member.file_id === fileId),
  );

  const handleAdd = async (event) => {
    event.preventDefault();
    if (!selectedGroupId) {
      return;
    }
    setAdding(true);
    setError(null);
    try {
      const updated = await addGroupMember(
        Number(selectedGroupId),
        fileId,
        tableAlias.trim() || null,
      );
      setAddedToGroup(updated);
      setSelectedGroupId('');
      setTableAlias('');
      await loadGroups();
    } catch (err) {
      setError(err.message);
    } finally {
      setAdding(false);
    }
  };

  const handleAddAnother = () => {
    setAddedToGroup(null);
    loadGroups();
  };

  if (addedToGroup) {
    return (
      <div className="add-to-group-panel">
        <p>
          Added to <strong>{addedToGroup.name}</strong>.
        </p>
        <div className="inline-links">
          <Link to={`/sql/groups/${addedToGroup.id}`}>Open group SQL</Link>
          {availableGroups.length > 0 && (
            <button type="button" className="text-button" onClick={handleAddAnother}>
              Add to another group
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="add-to-group-panel">
      <h3>Add to dataset group</h3>
      <p className="upload-help">
        Group this file with related CSVs (e.g. customers + prices) for multi-table SQL.
      </p>
      {loading && <p>Loading groups…</p>}
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      {!loading && groups.length === 0 && (
        <p>
          No groups yet. <Link to="/groups">Create a dataset group</Link>
        </p>
      )}
      {!loading && groups.length > 0 && availableGroups.length === 0 && (
        <p>This file is already in all your groups.</p>
      )}
      {!loading && availableGroups.length > 0 && (
        <form onSubmit={handleAdd} className="add-to-group-form">
          <label htmlFor={`group-select-${fileId}`}>Existing group</label>
          <select
            id={`group-select-${fileId}`}
            value={selectedGroupId}
            onChange={(event) => setSelectedGroupId(event.target.value)}
            required
          >
            <option value="">Choose a group…</option>
            {availableGroups.map((group) => (
              <option key={group.id} value={group.id}>
                {group.name} ({group.members.length} file
                {group.members.length === 1 ? '' : 's'})
              </option>
            ))}
          </select>
          <label htmlFor={`table-alias-${fileId}`}>
            Table alias <span className="optional-label">(optional)</span>
          </label>
          <input
            id={`table-alias-${fileId}`}
            type="text"
            value={tableAlias}
            onChange={(event) => setTableAlias(event.target.value)}
            placeholder={suggestAlias(filename)}
          />
          <button type="submit" className="primary-button" disabled={adding || !selectedGroupId}>
            {adding ? 'Adding…' : 'Add to group'}
          </button>
        </form>
      )}
      {!loading && (
        <p>
          <Link to="/groups">Manage dataset groups</Link>
        </p>
      )}
    </div>
  );
}

function suggestAlias(filename) {
  if (!filename) {
    return 'e.g. customers';
  }
  const stem = filename.replace(/\.csv$/i, '');
  const cleaned = stem.replace(/[^a-zA-Z0-9_]/g, '_') || 'dataset';
  return cleaned[0]?.match(/\d/) ? `t_${cleaned}` : cleaned;
}
