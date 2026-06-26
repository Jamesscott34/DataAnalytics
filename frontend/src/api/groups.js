/**
 * Dataset group API calls.
 */

import { API_BASE_URL } from './client.js';
import { getAccessToken } from './tokenStorage.js';

function authHeaders(json = true) {
  const headers = { Accept: 'application/json' };
  if (json) {
    headers['Content-Type'] = 'application/json';
  }
  const token = getAccessToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

/**
 * @param {{ name: string, members?: Array<{ file_id: number, table_alias?: string }> }} payload
 */
export async function createGroup(payload) {
  const response = await fetch(`${API_BASE_URL}/groups`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message ?? body.detail ?? 'Failed to create group');
  }
  return response.json();
}

export async function listGroups() {
  const response = await fetch(`${API_BASE_URL}/groups`, {
    headers: authHeaders(false),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message ?? body.detail ?? 'Failed to load groups');
  }
  return response.json();
}

export async function addGroupMember(groupId, fileId, tableAlias) {
  const response = await fetch(`${API_BASE_URL}/groups/${groupId}/members`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({
      file_id: fileId,
      table_alias: tableAlias || null,
    }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message ?? body.detail ?? 'Failed to add file to group');
  }
  return response.json();
}

export async function importGroupTables(groupId) {
  const response = await fetch(`${API_BASE_URL}/sql/groups/${groupId}/import`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({}),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message ?? body.detail ?? 'Group import failed');
  }
  return response.json();
}

export async function getGroupPresets(groupId) {
  const response = await fetch(`${API_BASE_URL}/sql/groups/${groupId}/presets`, {
    headers: authHeaders(false),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message ?? body.detail ?? 'Failed to load group presets');
  }
  return response.json();
}

export async function runGroupSqlQuery(groupId, query) {
  const response = await fetch(`${API_BASE_URL}/sql/groups/${groupId}/query`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ query }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message ?? body.detail ?? 'Group SQL query failed');
  }
  return response.json();
}
