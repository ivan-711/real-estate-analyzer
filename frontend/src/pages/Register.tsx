import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../lib/api";
import type { TokenResponse } from "../types";
import { useAuth } from "../context/AuthContext";

export default function Register() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await api.post<TokenResponse>("/api/v1/auth/register", {
        email,
        password,
        full_name: fullName || undefined,
      });
      login(res.data.access_token);
      navigate("/", { replace: true });
    } catch (err: unknown) {
      const data =
        err && typeof err === "object" && "response" in err
          ? (
              err as {
                response?: { data?: { detail?: string | { detail?: string } } };
              }
            ).response?.data?.detail
          : null;
      setError(
        typeof data === "string"
          ? data
          : data && typeof data === "object" && "detail" in data
            ? String((data as { detail: string }).detail)
            : "Registration failed. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-md px-4 py-16">
      <div className="rounded-xl border border-border bg-white p-8 shadow-sm">
        <h1 className="font-sans text-2xl font-bold text-navy">Register</h1>
        <p className="mt-1 text-sm text-slate">
          Create an account to analyze and save deals.
        </p>
        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label
              htmlFor="email"
              className="mb-1 block text-sm font-medium text-slate"
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full rounded-lg border border-border px-4 py-2.5 focus:border-blue-primary focus:ring-2 focus:ring-blue-primary"
            />
          </div>
          <div>
            <label
              htmlFor="password"
              className="mb-1 block text-sm font-medium text-slate"
            >
              Password (min 8 characters)
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              className="w-full rounded-lg border border-border px-4 py-2.5 focus:border-blue-primary focus:ring-2 focus:ring-blue-primary"
            />
          </div>
          <div>
            <label
              htmlFor="fullName"
              className="mb-1 block text-sm font-medium text-slate"
            >
              Full name (optional)
            </label>
            <input
              id="fullName"
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full rounded-lg border border-border px-4 py-2.5 focus:border-blue-primary focus:ring-2 focus:ring-blue-primary"
            />
          </div>
          {error && <p className="text-sm text-red-negative">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-blue-primary py-2.5 font-medium text-white hover:bg-blue-light disabled:opacity-50"
          >
            {loading ? "Creating account…" : "Register"}
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-slate">
          Already have an account?{" "}
          <Link to="/login" className="text-blue-primary hover:underline">
            Log in
          </Link>
        </p>
      </div>
    </div>
  );
}
