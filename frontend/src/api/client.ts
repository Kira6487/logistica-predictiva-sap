const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export type QueryValue = string | number | boolean | null | undefined;

export function queryString(params: Record<string, QueryValue> = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, String(value));
    }
  });
  const value = search.toString();
  return value ? `?${value}` : "";
}

export async function apiGet<T>(
  path: string,
  params?: Record<string, QueryValue>,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}${queryString(params)}`);
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(
      payload?.detail || `La API respondió con estado ${response.status}.`,
    );
  }
  return response.json() as Promise<T>;
}

export { API_BASE_URL };
