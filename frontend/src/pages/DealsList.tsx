import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { getToken } from "../lib/api";
import type { DealResponse } from "../types";

function formatCurrency(n: number | undefined): string {
  if (n === undefined || n === null) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(n);
}

function formatDate(s: string | undefined): string {
  if (!s) return "—";
  try {
    return new Date(s).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return "—";
  }
}

export default function DealsList() {
  const [deals, setDeals] = useState<DealResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      setLoading(false);
      return;
    }
    api
      .get<DealResponse[]>("/api/v1/deals/")
      .then((res) => setDeals(res.data))
      .catch(() => setError("Failed to load deals."))
      .finally(() => setLoading(false));
  }, []);

  if (!getToken()) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-12 text-center">
        <p className="text-slate">Log in to view saved deals.</p>
        <Link
          to="/login"
          className="mt-4 inline-block rounded-lg bg-blue-primary px-4 py-2 font-medium text-white no-underline hover:bg-blue-light"
        >
          Log in
        </Link>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-12">
        <div className="mb-6 h-8 w-48 animate-pulse rounded bg-border" />
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 animate-pulse rounded-xl bg-border" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-12">
        <p className="text-red-negative">{error}</p>
        <Link
          to="/analyze"
          className="mt-4 inline-block text-blue-primary hover:underline"
        >
          Analyze a deal
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <div className="mb-8 flex items-center justify-between">
        <h1 className="font-sans text-2xl font-bold text-navy">Saved deals</h1>
        <Link
          to="/analyze"
          className="rounded-lg border border-border bg-white px-4 py-2 text-sm font-medium text-slate no-underline hover:bg-blue-subtle"
        >
          New analysis
        </Link>
      </div>

      {deals.length === 0 ? (
        <div className="rounded-xl border border-border bg-white p-8 text-center text-slate">
          <p>No saved deals yet.</p>
          <Link
            to="/analyze"
            className="mt-4 inline-block text-blue-primary hover:underline"
          >
            Analyze a deal
          </Link>
        </div>
      ) : (
        <ul className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {deals.map((deal) => (
            <li key={deal.id}>
              <Link
                to={`/deals/${deal.id}`}
                className="block rounded-xl border border-border bg-white p-6 shadow-sm no-underline transition hover:border-blue-primary hover:shadow"
              >
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <h2 className="font-sans text-lg font-semibold text-navy">
                    {deal.deal_name?.trim() || "Deal"}
                  </h2>
                  <span className="text-sm text-muted">
                    {formatDate(deal.created_at)}
                  </span>
                </div>
                <div className="mt-3 grid gap-2 text-sm sm:grid-cols-2 lg:grid-cols-4">
                  <span className="text-muted">Purchase:</span>
                  <span className="font-mono tabular-nums text-slate">
                    {formatCurrency(deal.purchase_price)}
                  </span>
                  <span className="text-muted">Rent:</span>
                  <span className="font-mono tabular-nums text-slate">
                    {formatCurrency(deal.gross_monthly_rent)}/mo
                  </span>
                  {deal.monthly_cash_flow != null && (
                    <>
                      <span className="text-muted">Cash flow:</span>
                      <span
                        className={`font-mono tabular-nums ${Number(deal.monthly_cash_flow) >= 0 ? "text-green-positive" : "text-red-negative"}`}
                      >
                        {formatCurrency(Number(deal.monthly_cash_flow))}/mo
                      </span>
                    </>
                  )}
                  {deal.risk_score != null && (
                    <>
                      <span className="text-muted">Risk:</span>
                      <span className="font-mono tabular-nums text-slate">
                        Score: {Math.round(Number(deal.risk_score))}
                      </span>
                    </>
                  )}
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
