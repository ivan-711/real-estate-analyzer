import axios from "axios";

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
