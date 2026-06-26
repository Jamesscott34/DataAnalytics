/**
 * ScannerResultPanel
 *
 * Displays Python-only CSV scanner status, issues, risk score, and guidance.
 *
 * @param {Object} props
 * @param {Object|null} props.result - Scan result returned by the backend.
 */
export function ScannerResultPanel({ result }) {
  if (!result) {
    return null;
  }

  return (
    <section
      className={`scanner-panel scanner-panel--${result.status}`}
      aria-labelledby="scanner-result-heading"
    >
      <h3 id="scanner-result-heading">Security scan: {result.status}</h3>
      <p>Risk score: {result.risk_score}/100</p>
      <p>{result.recommended_action}</p>

      {result.issues.length > 0 ? (
        <ul>
          {result.issues.map((issue) => (
            <li key={issue}>{issue}</li>
          ))}
        </ul>
      ) : (
        <p>No scanner issues found.</p>
      )}
    </section>
  );
}
