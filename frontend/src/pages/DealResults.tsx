import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import type { AxiosResponse } from "axios";
import api, { getToken } from "../lib/api";
import type { DealPreviewResponse, DealResponse } from "../types";

type DealDisplay = DealResponse | DealPreviewResponse;

function formatCurrency(n: number | undefined): string {
  if (n === undefined || n === null) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(n);
}

function formatPercent(n: number | undefined): string {
  if (n === undefined || n === null) return "—";
  return `${Number(n).toFixed(1)}%`;
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
  const location = useLocation();
  const stateDeal = location.state?.deal as DealPreviewResponse | undefined;
  const [deal, setDeal] = useState<DealDisplay | null>(stateDeal ?? null);
  const [loading, setLoading] = useState(!stateDeal);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id === "preview" && stateDeal) {
      setDeal(stateDeal);
      setLoading(false);
      return;
    }
    if (!id || id === "preview") {
      if (!stateDeal) {
        setError("No preview data. Go back and analyze a deal.");
        setLoading(false);
      }
      return;
    }
    if (!getToken()) {
      setError("Please log in to view saved deal details.");
      setLoading(false);
      return;
    }
    api
      .get<DealResponse>(`/api/v1/deals/${id}`)
      .then((res: AxiosResponse<DealResponse>) => setDeal(res.data))
      .catch(() => setError("Deal not found or you don't have access."))
      .finally(() => setLoading(false));
  }, [id, stateDeal]);

  if (loading) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-12">
        <div className="mb-8 h-8 w-48 animate-pulse rounded bg-border" />
        <div className="grid gap-6 sm:grid-cols-2">
          <div className="h-32 animate-pulse rounded-xl bg-border" />
          <div className="h-32 animate-pulse rounded-xl bg-border" />
        </div>
        <div className="mt-8 grid gap-4 sm:grid-cols-5">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-20 animate-pulse rounded-xl bg-border" />
          ))}
        </div>
        <div className="mt-8 flex justify-center">
          <svg
            className="h-8 w-8 animate-spin text-blue-primary"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        </div>
      </div>
    );
  }
  if (error || !deal) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-12">
        <p className="text-red-negative">{error}</p>
        <Link
          to="/"
          className="mt-4 inline-block text-blue-primary hover:underline"
        >
          Home
        </Link>
      </div>
    );
  }

  const score = deal.risk_score != null ? Number(deal.risk_score) : undefined;

  const mcFlow =
    deal.monthly_cash_flow != null ? Number(deal.monthly_cash_flow) : undefined;
  const grossRent = deal.gross_monthly_rent ?? 0;
  const vacancyPct = deal.vacancy_rate_pct ?? 5;
  const vacancyLoss = grossRent * (vacancyPct / 100);
  const propTax = deal.property_tax_monthly ?? 0;
  const insurance = deal.insurance_monthly ?? 0;
  const maintPct = deal.maintenance_rate_pct ?? 5;
  const mgmtPct = deal.management_fee_pct ?? 10;
  const maintenance = grossRent * (maintPct / 100);
  const management = grossRent * (mgmtPct / 100);
  const mortgage = deal.monthly_mortgage ?? 0;

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <div className="mb-8 flex items-center justify-between">
        <h1 className="font-sans text-2xl font-bold text-navy">
          Deal analysis
        </h1>
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
            className={`font-mono text-4xl font-bold ${mcFlow != null && mcFlow >= 0 ? "text-green-positive" : "text-red-negative"}`}
          >
            {formatCurrency(deal.monthly_cash_flow)}
          </p>
        </div>
        <div className="rounded-xl border border-border bg-white p-6 shadow-sm">
          <h2 className="text-sm font-medium text-muted">Risk score</h2>
          <p className="font-mono text-4xl font-bold text-navy">
            {score != null ? `${Math.round(score)} / 100` : "—"}
          </p>
          <span
            className={`mt-2 inline-block rounded-full px-3 py-1 text-sm font-medium ${riskColorClass(score)}`}
          >
            {riskLabel(score)}
          </span>
        </div>
      </div>

      <div className="mt-8 rounded-xl border border-border bg-white p-6 shadow-sm">
        <h2 className="mb-4 font-sans text-lg font-semibold text-navy">
          Key metrics
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <div>
            <span className="text-sm text-muted">NOI (annual)</span>
            <p className="font-mono font-semibold text-slate">
              {formatCurrency(deal.noi)}
            </p>
          </div>
          <div>
            <span className="text-sm text-muted">Cap rate</span>
            <p className="font-mono font-semibold text-slate">
              {formatPercent(deal.cap_rate)}
            </p>
          </div>
          <div>
            <span className="text-sm text-muted">Cash-on-cash</span>
            <p className="font-mono font-semibold text-slate">
              {formatPercent(deal.cash_on_cash)}
            </p>
          </div>
          <div>
            <span className="text-sm text-muted">DSCR</span>
            <p className="font-mono font-semibold text-slate">
              {formatNumber(deal.dscr)}
            </p>
          </div>
          <div>
            <span className="text-sm text-muted">GRM</span>
            <p className="font-mono font-semibold text-slate">
              {formatNumber(deal.grm)}
            </p>
          </div>
          <div>
            <span className="text-sm text-muted">Total cash invested</span>
            <p className="font-mono font-semibold text-slate">
              {formatCurrency(deal.total_cash_invested)}
            </p>
          </div>
        </div>
      </div>

      <div className="mt-8 grid gap-8 sm:grid-cols-2">
        <div className="rounded-xl border border-border bg-white p-6 shadow-sm">
          <h2 className="mb-4 font-sans text-lg font-semibold text-navy">
            Financing summary
          </h2>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-muted">Purchase price</dt>
              <dd className="font-mono font-semibold text-slate">
                {formatCurrency(deal.purchase_price)}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted">Down payment</dt>
              <dd className="font-mono font-semibold text-slate">
                {formatCurrency(
                  deal.purchase_price != null && deal.down_payment_pct != null
                    ? Number(deal.purchase_price) *
                        (Number(deal.down_payment_pct) / 100)
                    : undefined,
                )}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted">Loan amount</dt>
              <dd className="font-mono font-semibold text-slate">
                {formatCurrency(deal.loan_amount)}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted">Monthly mortgage</dt>
              <dd className="font-mono font-semibold text-slate">
                {formatCurrency(deal.monthly_mortgage)}
              </dd>
            </div>
          </dl>
        </div>
        <div className="rounded-xl border border-border bg-white p-6 shadow-sm">
          <h2 className="mb-4 font-sans text-lg font-semibold text-navy">
            Monthly expense breakdown
          </h2>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-muted">Gross rent</dt>
              <dd className="font-mono text-slate">
                {formatCurrency(grossRent)}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted">Vacancy ({vacancyPct}%)</dt>
              <dd className="font-mono text-red-negative">
                -{formatCurrency(vacancyLoss)}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted">Property tax</dt>
              <dd className="font-mono text-red-negative">
                -{formatCurrency(propTax)}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted">Insurance</dt>
              <dd className="font-mono text-red-negative">
                -{formatCurrency(insurance)}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted">Maintenance ({maintPct}%)</dt>
              <dd className="font-mono text-red-negative">
                -{formatCurrency(maintenance)}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted">Management ({mgmtPct}%)</dt>
              <dd className="font-mono text-red-negative">
                -{formatCurrency(management)}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted">Mortgage</dt>
              <dd className="font-mono text-red-negative">
                -{formatCurrency(mortgage)}
              </dd>
            </div>
            <div className="flex justify-between border-t border-border pt-2 font-medium">
              <dt className="text-navy">Net cash flow</dt>
              <dd
                className={`font-mono ${mcFlow != null && mcFlow >= 0 ? "text-green-positive" : "text-red-negative"}`}
              >
                {formatCurrency(deal.monthly_cash_flow)}
              </dd>
            </div>
          </dl>
        </div>
      </div>

      <div className="mt-8 rounded-xl border border-border bg-white p-6 shadow-sm">
        <h2 className="mb-4 font-sans text-lg font-semibold text-navy">
          IRR & equity
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <span className="text-sm text-muted">IRR 5 yr</span>
            <p className="font-mono font-semibold text-slate">
              {formatPercent(deal.irr_5yr)}
            </p>
          </div>
          <div>
            <span className="text-sm text-muted">IRR 10 yr</span>
            <p className="font-mono font-semibold text-slate">
              {formatPercent(deal.irr_10yr)}
            </p>
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
          <h2 className="mb-4 font-sans text-lg font-semibold text-navy">
            Risk factor breakdown
          </h2>
          <ul className="space-y-3">
            {Object.entries(deal.risk_factors).map(([key, val]) => {
              const numVal =
                typeof val === "number" ? val : parseFloat(String(val)) || 0;
              const pct = Math.min(100, Math.max(0, numVal));
              return (
                <li key={key} className="flex items-center gap-4">
                  <span className="w-40 shrink-0 text-sm text-slate">
                    {key
                      .replace(/_/g, " ")
                      .replace(/\b\w/g, (c) => c.toUpperCase())}
                  </span>
                  <div className="h-2 flex-1 overflow-hidden rounded-full bg-border">
                    <div
                      className="h-full rounded-full bg-blue-primary transition-all"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <span className="font-mono text-sm text-slate">
                    {typeof val === "number" ? val.toFixed(0) : String(val)}
                  </span>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
