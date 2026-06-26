import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { createGroup, listGroups } from '../api/groups.js';
import { listUploads } from '../api/uploads.js';

/**
 * GroupsPage
 *
 * Create and manage dataset groups.
 */
export function GroupsPage() {
  const [groups, setGroups] = useState([]);
  const [uploads, setUploads] = useState([]);
  const [name, setName] = useState('');
  const [selectedFileIds, setSelectedFileIds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const [groupResponse, uploadResponse] = await Promise.all([
        listGroups(),
        listUploads(),
      ]);
      setGroups(groupResponse.items ?? []);
      setUploads(uploadResponse.items ?? []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const toggleFile = (fileId) => {
    setSelectedFileIds((current) =>
      current.includes(fileId)
        ? current.filter((id) => id !== fileId)
        : [...current, fileId],
    );
  };

  const handleCreate = async (event) => {
    event.preventDefault();
    setError(null);
    try {
      await createGroup({
        name,
        members: selectedFileIds.map((file_id) => ({ file_id })),
      });
      setName('');
      setSelectedFileIds([]);
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <main className="page-shell page-shell--wide">
      <header className="page-header">
        <h1>Dataset groups</h1>
        <p className="page-lead">
          Combine related CSV files (e.g. customers, groceries, prices) and run SQL
          across them together.
        </p>
      </header>

      <section className="panel-card">
        <h2>Create a group</h2>
        <form onSubmit={handleCreate} className="group-form">
          <label htmlFor="group-name">Group name</label>
          <input
            id="group-name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="e.g. Retail shop datasets"
            required
          />
          <fieldset>
            <legend>Select CSV files to include</legend>
            {uploads.length === 0 ? (
              <p>No uploads yet. Upload CSV files first.</p>
            ) : (
              <ul className="checkbox-list">
                {uploads.map((file) => (
                  <li key={file.id}>
                    <label>
                      <input
                        type="checkbox"
                        checked={selectedFileIds.includes(file.id)}
                        onChange={() => toggleFile(file.id)}
                      />
                      {file.original_filename}
                    </label>
                  </li>
                ))}
              </ul>
            )}
          </fieldset>
          <button
            type="submit"
            className="primary-button"
            disabled={!name.trim() || selectedFileIds.length < 1}
          >
            Create group
          </button>
        </form>
      </section>

      {loading && <p>Loading groups…</p>}
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}

      <section className="panel-card">
        <h2>Your groups</h2>
        {groups.length === 0 ? (
          <p>No groups yet.</p>
        ) : (
          <ul className="file-list">
            {groups.map((group) => (
              <li key={group.id}>
                <div>
                  <strong>{group.name}</strong>
                  <span>
                    {group.members.length} file{group.members.length === 1 ? '' : 's'}
                  </span>
                </div>
                <Link className="primary-link" to={`/sql/groups/${group.id}`}>
                  Open group SQL
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
