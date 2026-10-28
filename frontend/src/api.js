const ROOT = '/api';

export async function api(path, options = {}) {
  const response = await fetch(`${ROOT}${path}`, {
    ...options,
    headers: options.body instanceof FormData ? options.headers : { 'Content-Type': 'application/json', ...options.headers },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
  return data;
}

export const post = (path, body = {}) => api(path, { method: 'POST', body: JSON.stringify(body) });
export const put = (path, body = {}) => api(path, { method: 'PUT', body: JSON.stringify(body) });
