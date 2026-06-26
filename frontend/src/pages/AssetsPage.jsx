import { AssetsFileList } from '../components/AssetsFileList.jsx';

/**
 * AssetsPage
 *
 * Page for browsing and selecting temp_assets CSV files.
 */
export function AssetsPage() {
  return (
    <main className="page-shell page-shell--wide">
      <header className="page-header">
        <h1>Sample datasets</h1>
        <p className="page-lead">
          Import curated CSV files from temp_assets without uploading from disk.
        </p>
      </header>
      <AssetsFileList />
    </main>
  );
}
