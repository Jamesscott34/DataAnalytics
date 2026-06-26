import { UploadForm } from '../components/UploadForm.jsx';

/**
 * UploadPage
 *
 * Analyst-only page for secure CSV upload.
 */
export function UploadPage() {
  return (
    <main className="page-shell page-shell--wide">
      <header className="page-header">
        <h1>Upload dataset</h1>
        <p className="page-lead">
          Upload a CSV file for validation and later analysis.
        </p>
      </header>
      <UploadForm />
    </main>
  );
}
