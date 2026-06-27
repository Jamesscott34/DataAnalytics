/**
 * Shared workspace navigation links for dataset analysis pages.
 *
 * @param {number} fileId
 */
export function workspaceLinks(fileId) {
  return [
    { to: `/scan/${fileId}`, label: 'Full scan' },
    { to: `/sql/${fileId}`, label: 'SQL' },
    { to: `/eda/${fileId}`, label: 'EDA' },
    { to: `/regression/${fileId}`, label: 'Regression' },
    { to: `/classification/${fileId}`, label: 'Classification' },
    { to: `/clustering/${fileId}`, label: 'Clustering' },
    { to: `/pca/${fileId}`, label: 'PCA' },
    { to: `/timeseries/${fileId}`, label: 'Time series' },
    { to: `/similarity/${fileId}`, label: 'Similarity' },
    { to: `/business/${fileId}`, label: 'Business' },
    { to: `/versions/${fileId}`, label: 'Versions' },
  ];
}
