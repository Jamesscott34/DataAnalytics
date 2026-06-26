import { useState } from 'react';
import { useUpload } from '../hooks/useUpload.js';

/**
 * UploadForm
 *
 * Lets analysts upload a CSV file and displays returned metadata.
 */
export function UploadForm() {
  const [file, setFile] = useState(null);
  const { upload, loading, error, result } = useUpload();

  const handleSubmit = async (event) => {
    event.preventDefault();
    await upload(file);
  };

  return (
    <section className="upload-panel" aria-labelledby="upload-heading">
      <h2 id="upload-heading">Upload CSV</h2>
      <form onSubmit={handleSubmit}>
        <label htmlFor="csv-file">CSV file</label>
        <input
          id="csv-file"
          type="file"
          accept=".csv,text/csv"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          aria-label="CSV file"
        />
        {error && <p role="alert">{error}</p>}
        <button type="submit" disabled={loading} aria-busy={loading}>
          {loading ? 'Uploading…' : 'Upload'}
        </button>
      </form>

      {result && (
        <div className="upload-result" role="status" aria-live="polite">
          <p>Uploaded: {result.filename}</p>
          <p>Rows: {result.row_count}</p>
          <p>Columns: {result.column_count}</p>
          <p>Duplicate: {result.is_duplicate ? 'yes' : 'no'}</p>
        </div>
      )}
    </section>
  );
}
