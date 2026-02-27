import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { getToken } from "../lib/api";
import type { DealResponse, DealSummaryResponse } from "../types";
import BlurText from "../components/ui/BlurText";
import CountUp from "../components/ui/CountUp";
import SpotlightCard from "../components/ui/SpotlightCard";
import StarBorder from "../components/ui/StarBorder";

function formatCurrency(n: number | undefined | null): string {
  if (n === undefined || n === null) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(n);
}

function formatPercent(n: number | undefined | null): string {
  if (n === undefined || n === null) return "—";
  return `${(Number(n) * 100).toFixed(1)}%`;
}

function riskLabel(score: number | undefined | null): string {
  if (score === undefined || score === null) return "—";
  if (score <= 33) return "Low Risk";
  if (score <= 66) return "Moderate Risk";
  return "High Risk";
}

function riskColorClass(score: number | undefined | null): string {
  if (score === undefined || score === null) return "bg-muted text-slate";
  if (score <= 33) return "bg-green-light text-green-positive";
  if (score <= 66) return "bg-yellow-light text-yellow-moderate";
  return "bg-red-light text-red-negative";
}

export default function Dashboard() {
  const [summary, setSummary] = useState<DealSummaryResponse | null>(null);
  const [deals, setDeals] = useState<DealResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      setLoading(false);
      return;
    }

    Promise.all([
      api.get<DealSummaryResponse>("/api/v1/deals/summary"),
      api.get<DealResponse[]>("/api/v1/deals/"),
    ])
      .then(([summaryRes, dealsRes]) => {
        setSummary(summaryRes.data);
        setDeals(dealsRes.data);
      })
      .catch(() => setError("Failed to load dashboard data."))
      .finally(() => setLoading(false));
  }, []);

  if (!getToken()) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-12 text-center">
        <p className="text-slate">Log in to view your dashboard.</p>
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
      <div className="mx-auto max-w-6xl px-4 py-12">
        <div className="mb-8 h-8 w-56 animate-pulse rounded bg-border" />
        <div className="grid grid-cols-2 gap-6 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-28 animate-pulse rounded-xl bg-border" />
          ))}
        </div>
        <div className="mt-10 mb-6 h-7 w-48 animate-pulse rounded bg-border" />
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-40 animate-pulse rounded-xl bg-border" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-12">
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

  const cashFlow = summary?.total_monthly_cash_flow ?? 0;

  // Best deal = highest cash_on_cash; worst deal = highest risk_score
  const bestDealId =
    deals.reduce<{ id: string; coc: number } | null>((best, d) => {
      const coc = d.cash_on_cash != null ? Number(d.cash_on_cash) : null;
      if (coc === null) return best;
      return best === null || coc > best.coc ? { id: d.id, coc } : best;
    }, null)?.id ?? null;

  const worstDealId =
    deals.reduce<{ id: string; score: number } | null>((worst, d) => {
      const score = d.risk_score != null ? Number(d.risk_score) : null;
      if (score === null) return worst;
      return worst === null || score > worst.score
        ? { id: d.id, score }
        : worst;
    }, null)?.id ?? null;

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <BlurText
        text="Portfolio Overview"
        as="h1"
        delay={100}
        className="mb-8 font-sans text-2xl font-bold text-navy"
      />

      {/* KPI cards */}
      <div className="grid grid-cols-2 gap-6 lg:grid-cols-4">
        <div className="rounded-xl border border-border bg-white p-6 shadow-sm">
          <p className="text-sm text-muted">Total Cash Flow</p>
          <p
            className={`mt-1 font-mono text-2xl lg:text-4xl font-semibold tabular-nums ${cashFlow >= 0 ? "text-green-positive" : "text-red-negative"}`}
          >
            $<CountUp to={cashFlow} separator="," decimals={0} />
            /mo
          </p>
        </div>

        <div className="rounded-xl border border-border bg-white p-6 shadow-sm">
          <p className="text-sm text-muted">Avg Cap Rate</p>
          <p className="mt-1 font-mono text-2xl lg:text-4xl font-semibold tabular-nums text-navy">
            {summary?.average_cap_rate != null ? (
              <>
                <CountUp to={summary.average_cap_rate * 100} decimals={1} />%
              </>
            ) : (
              "—"
            )}
          </p>
        </div>

        <div className="rounded-xl border border-border bg-white p-6 shadow-sm">
          <p className="text-sm text-muted">Total Equity</p>
          <p className="mt-1 font-mono text-2xl lg:text-4xl font-semibold tabular-nums text-navy">
            $
            <CountUp
              to={summary?.total_equity ?? 0}
              separator=","
              decimals={0}
            />
          </p>
        </div>

        <div className="rounded-xl border border-border bg-white p-6 shadow-sm">
          <p className="text-sm text-muted">Active Deals</p>
          <p className="mt-1 font-mono text-2xl lg:text-4xl font-semibold tabular-nums text-navy">
            <CountUp to={summary?.active_deal_count ?? 0} decimals={0} />
          </p>
        </div>
      </div>

      {/* Deal grid */}
      <BlurText
        text="Your Active Deals"
        as="h2"
        delay={100}
        className="mt-10 mb-6 font-sans text-xl font-semibold text-navy"
      />

      {deals.length === 0 ? (
        <div className="rounded-xl border border-border bg-white p-8 text-center text-slate">
          <p>No deals yet.</p>
          <Link
            to="/analyze"
            className="mt-4 inline-block text-blue-primary hover:underline"
          >
            Analyze your first deal
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {deals.map((deal) => {
            const mcf =
              deal.monthly_cash_flow != null
                ? Number(deal.monthly_cash_flow)
                : null;
            const score =
              deal.risk_score != null ? Number(deal.risk_score) : null;
            const coc =
              deal.cash_on_cash != null ? Number(deal.cash_on_cash) : null;

            // 1-deal edge case: isBest=true, isWorst=false → green StarBorder only
            const isBest = bestDealId === deal.id;
            const isWorst = !isBest && worstDealId === deal.id;

            // Shared card content — key goes on the outermost returned element
            const cardInner = (
              <div className="relative p-6">
                <h3 className="font-sans text-lg font-semibold text-navy">
                  {deal.deal_name?.trim() || "Deal"}
                </h3>

                <div className="mt-3 space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-muted">Cash Flow</span>
                    <span
                      className={`font-mono font-semibold tabular-nums ${mcf != null && mcf >= 0 ? "text-green-positive" : "text-red-negative"}`}
                    >
                      {mcf != null ? `${formatCurrency(mcf)}/mo` : "—"}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-muted">Cash-on-Cash</span>
                    <span className="font-mono tabular-nums text-slate">
                      {formatPercent(coc)}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-muted">Risk</span>
                    <span
                      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${riskColorClass(score)}`}
                    >
                      {riskLabel(score)}
                    </span>
                  </div>
                </div>

                <Link
                  to={`/deals/${deal.id}`}
                  className="mt-4 inline-block text-sm font-medium text-blue-primary no-underline hover:underline"
                >
                  View Deal
                </Link>
              </div>
            );

            const spotlightCard = (
              <SpotlightCard
                className="rounded-xl border border-border bg-white shadow-sm transition-shadow duration-200 hover:shadow-md"
                spotlightColor="rgba(59, 130, 246, 0.15)"
              >
                {cardInner}
              </SpotlightCard>
            );

            // StarBorder (outer) > SpotlightCard (inner) for best/worst deals
            if (isBest) {
              return (
                <StarBorder key={deal.id} color="#22C55E" speed="5s">
                  {spotlightCard}
                </StarBorder>
              );
            }
            if (isWorst) {
              return (
                <StarBorder key={deal.id} color="#EF4444" speed="5s">
                  {spotlightCard}
                </StarBorder>
              );
            }
            return (
              <SpotlightCard
                key={deal.id}
                className="rounded-xl border border-border bg-white shadow-sm transition-shadow duration-200 hover:shadow-md"
                spotlightColor="rgba(59, 130, 246, 0.15)"
              >
                {cardInner}
              </SpotlightCard>
            );
          })}
        </div>
      )}
    </div>
  );
}
