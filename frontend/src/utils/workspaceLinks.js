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
    { to: `/versions/${fileId}`, label: 'Versions' },
  ];
}
