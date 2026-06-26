import { UploadForm } from '../components/UploadForm.jsx';

/**
 * UploadPage
 *
 * Analyst-only page for secure CSV upload.
 */
export function UploadPage() {
  return (
    <main>
      <header>
        <h1>Upload dataset</h1>
        <p>Upload a CSV file for validation and later analysis.</p>
      </header>
      <UploadForm />
    </main>
  );
}
