import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import type { AxiosResponse } from "axios";
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

function formatPercent(n: number | undefined): string {
  if (n === undefined || n === null) return "—";
  return `${Number(n).toFixed(2)}%`;
}

function formatNumber(n: number | undefined): string {
  if (n === undefined || n === null) return "—";
  return Number(n).toFixed(2);
}

function riskLabel(score: number | undefined): string {
  if (score === undefined || score === null) return "—";
  if (score <= 33) return "Low Risk";
  if (score <= 66) return "Moderate Risk";
  return "High Risk";
}

function riskColorClass(score: number | undefined): string {
  if (score === undefined || score === null) return "bg-muted text-slate";
  if (score <= 33) return "bg-green-light text-green-positive";
  if (score <= 66) return "bg-yellow-light text-yellow-moderate";
  return "bg-red-light text-red-negative";
}

export default function DealResults() {
  const { id } = useParams<{ id: string }>();
  const [deal, setDeal] = useState<DealResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id || !getToken()) {
      setError("Please log in to view deal details.");
      setLoading(false);
      return;
    }
    api
      .get<DealResponse>(`/api/v1/deals/${id}`)
      .then((res: AxiosResponse<DealResponse>) => setDeal(res.data))
      .catch(() => setError("Deal not found or you don’t have access."))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-12 text-center text-slate">
        Loading…
      </div>
    );
  }
  if (error || !deal) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-12">
        <p className="text-red-negative">{error}</p>
        <Link to="/" className="mt-4 inline-block text-blue-primary hover:underline">
          Home
        </Link>
      </div>
    );
  }

  const score = deal.risk_score != null ? Number(deal.risk_score) : undefined;

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <div className="mb-8 flex items-center justify-between">
        <h1 className="font-sans text-2xl font-bold text-navy">Deal analysis</h1>
        <Link
          to="/analyze"
          className="rounded-lg border border-border bg-white px-4 py-2 text-sm font-medium text-slate no-underline hover:bg-blue-subtle"
        >
          New analysis
        </Link>
      </div>

      <div className="grid gap-6 sm:grid-cols-2">
        <div className="rounded-xl border border-border bg-white p-6 shadow-sm">
          <h2 className="text-sm font-medium text-muted">Monthly cash flow</h2>
          <p
            className={`font-mono text-3xl font-bold ${deal.monthly_cash_flow != null && Number(deal.monthly_cash_flow) >= 0 ? "text-green-positive" : "text-red-negative"}`}
          >
            {formatCurrency(deal.monthly_cash_flow)}
          </p>
        </div>
        <div className="rounded-xl border border-border bg-white p-6 shadow-sm">
          <h2 className="text-sm font-medium text-muted">Risk score</h2>
          <p className="font-mono text-3xl font-bold text-navy">
            {score != null ? `${score} / 100` : "—"}
          </p>
          <span
            className={`mt-2 inline-block rounded-full px-3 py-1 text-sm font-medium ${riskColorClass(score)}`}
          >
            {riskLabel(score)}
          </span>
        </div>
      </div>

      <div className="mt-8 rounded-xl border border-border bg-white p-6 shadow-sm">
        <h2 className="mb-4 font-sans text-lg font-semibold text-navy">Key metrics</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <span className="text-sm text-muted">NOI (annual)</span>
            <p className="font-mono font-semibold text-slate">{formatCurrency(deal.noi)}</p>
          </div>
          <div>
            <span className="text-sm text-muted">Cap rate</span>
            <p className="font-mono font-semibold text-slate">{formatPercent(deal.cap_rate)}</p>
          </div>
          <div>
            <span className="text-sm text-muted">Cash-on-cash</span>
            <p className="font-mono font-semibold text-slate">{formatPercent(deal.cash_on_cash)}</p>
          </div>
          <div>
            <span className="text-sm text-muted">DSCR</span>
            <p className="font-mono font-semibold text-slate">{formatNumber(deal.dscr)}</p>
          </div>
          <div>
            <span className="text-sm text-muted">GRM</span>
            <p className="font-mono font-semibold text-slate">{formatNumber(deal.grm)}</p>
          </div>
          <div>
            <span className="text-sm text-muted">Total cash invested</span>
            <p className="font-mono font-semibold text-slate">
              {formatCurrency(deal.total_cash_invested)}
            </p>
          </div>
          <div>
            <span className="text-sm text-muted">IRR 5 yr</span>
            <p className="font-mono font-semibold text-slate">{formatPercent(deal.irr_5yr)}</p>
          </div>
          <div>
            <span className="text-sm text-muted">IRR 10 yr</span>
            <p className="font-mono font-semibold text-slate">{formatPercent(deal.irr_10yr)}</p>
          </div>
          <div>
            <span className="text-sm text-muted">Equity buildup 5 yr</span>
            <p className="font-mono font-semibold text-slate">
              {formatCurrency(deal.equity_buildup_5yr)}
            </p>
          </div>
          <div>
            <span className="text-sm text-muted">Equity buildup 10 yr</span>
            <p className="font-mono font-semibold text-slate">
              {formatCurrency(deal.equity_buildup_10yr)}
            </p>
          </div>
        </div>
      </div>

      {deal.risk_factors && Object.keys(deal.risk_factors).length > 0 && (
        <div className="mt-8 rounded-xl border border-border bg-white p-6 shadow-sm">
          <h2 className="mb-4 font-sans text-lg font-semibold text-navy">Risk factor breakdown</h2>
          <ul className="space-y-2">
            {Object.entries(deal.risk_factors).map(([key, val]) => (
              <li key={key} className="flex justify-between text-sm">
                <span className="text-slate">
                  {key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                </span>
                <span className="font-mono text-slate">{String(val)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
