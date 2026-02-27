import axios from "axios";
import type { DealProjectionsResponse, MarketSnapshot } from "../types";

const rawBaseURL =
  typeof import.meta.env.VITE_API_URL === "string" &&
  import.meta.env.VITE_API_URL.length > 0
    ? import.meta.env.VITE_API_URL
    : "http://localhost:8000";
const baseURL = rawBaseURL.replace(/\/+$/, "");

/** Base URL for API (e.g. for fetch-based SSE where axios is not used). */
export const apiBaseURL = baseURL;

export const api = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

const TOKEN_KEY = "midwest_deal_analyzer_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => {
    const ct = response.headers?.["content-type"] ?? "";
    if (String(ct).toLowerCase().includes("text/html")) {
      return Promise.reject(
        new Error("API returned HTML. Check VITE_API_URL and Vercel rewrites."),
      );
    }
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      clearToken();
    }
    return Promise.reject(error);
  },
);

export default api;

export async function getMarketSnapshot(
  zipCode: string,
): Promise<MarketSnapshot> {
  const res = await api.get<MarketSnapshot>(`/api/v1/markets/${zipCode}`);
  return res.data;
}

export async function getMarketComparison(
  zips: string[],
): Promise<MarketSnapshot[]> {
  const res = await api.get<MarketSnapshot[]>(
    `/api/v1/markets/compare?zips=${zips.join(",")}`,
  );
  return res.data;
}

export async function getMarketHistory(
  zipCode: string,
): Promise<{ zip_code: string; snapshots: MarketSnapshot[] }> {
  const res = await api.get<{ zip_code: string; snapshots: MarketSnapshot[] }>(
    `/api/v1/markets/${zipCode}/history`,
  );
  return res.data;
}

export async function getDealProjections(
  dealId: string,
  params?: {
    years?: number;
    appreciation_pct?: number;
    rent_growth_pct?: number;
    expense_growth_pct?: number;
    selling_cost_pct?: number;
  },
): Promise<DealProjectionsResponse> {
  const res = await api.get<DealProjectionsResponse>(
    `/api/v1/deals/${dealId}/projections`,
    { params },
  );
  return res.data;
}

export async function exportAllDealsCsv(): Promise<void> {
  const token = getToken();
  const res = await fetch(`${baseURL}/api/v1/deals/export/csv`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new Error("Export failed");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `midwestdealanalyzer-deals-${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export async function exportDealCsv(dealId: string): Promise<void> {
  const token = getToken();
  const res = await fetch(`${baseURL}/api/v1/deals/${dealId}/export/csv`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new Error("Export failed");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  const cd = res.headers.get("content-disposition") ?? "";
  const match = cd.match(/filename="([^"]+)"/);
  a.download = match?.[1] ?? `deal-${dealId}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
