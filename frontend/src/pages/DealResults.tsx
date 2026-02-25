import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import type { AxiosResponse } from "axios";
import api, { getDealProjections, getToken } from "../lib/api";
import AmortizationChart from "../components/charts/AmortizationChart";
import CashFlowChart from "../components/charts/CashFlowChart";
import EquityBuildupChart from "../components/charts/EquityBuildupChart";
import type {
  DealCreatePayload,
  DealPreviewPayload,
  DealPreviewResponse,
  DealProjectionsResponse,
  DealResponse,
  PropertyCreate,
  PropertyResponse,
} from "../types";

type DealDisplay = DealResponse | DealPreviewResponse;

function parseAddress(addressStr: string): {
  address: string;
  city: string;
  state: string;
  zip: string;
} {
  const trimmed = addressStr.trim();
  const parts = trimmed.split(",").map((p) => p.trim());
  const address = parts[0] || trimmed;
  const lastPart = parts[1] || parts[2] || "";
  const stateZipMatch = lastPart.match(/([A-Z]{2})\s*(\d{5}(-\d{4})?)$/);
  const state = stateZipMatch?.[1] || "WI";
  const zip = stateZipMatch?.[2] || "";
  const city =
    lastPart.replace(/\s+[A-Z]{2}\s*\d{5}(-\d{4})?$/, "").trim() || "";
  return { address, city, state, zip };
}

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

/** Fixed-rate monthly payment. Principal in dollars, annualRatePercent e.g. 7, termYears e.g. 30. */
function computeMonthlyMortgage(
  principal: number,
  annualRatePercent: number,
  termYears: number,
): number {
  if (principal <= 0) return 0;
  const n = termYears * 12;
  if (n <= 0) return 0;
  const r = annualRatePercent / 100 / 12;
  if (r <= 0) return Math.round((principal / n) * 100) / 100;
  const factor = Math.pow(1 + r, n);
  const payment = (principal * r * factor) / (factor - 1);
  return Math.round(payment * 100) / 100;
}

export default function DealResults() {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const stateDeal = location.state?.deal as DealPreviewResponse | undefined;
  const stateInputs = location.state?.inputs as DealPreviewPayload | undefined;
  const stateAddress = location.state?.address as string | undefined;
  const [deal, setDeal] = useState<DealDisplay | null>(stateDeal ?? null);
  const [loading, setLoading] = useState(!stateDeal);
  const [error, setError] = useState<string | null>(null);
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [projections, setProjections] =
    useState<DealProjectionsResponse | null>(null);

  useEffect(() => {
    if (!id || id === "preview" || !getToken()) return;
    getDealProjections(id)
      .then(setProjections)
      .catch(() => {
        // Charts simply don't render if projections fetch fails
      });
  }, [id]);

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

  const purchaseNum =
    deal.purchase_price != null ? Number(deal.purchase_price) : NaN;
  const downPct =
    deal.down_payment_pct != null ? Number(deal.down_payment_pct) : NaN;
  const ratePct = deal.interest_rate != null ? Number(deal.interest_rate) : NaN;
  const termYears =
    deal.loan_term_years != null ? Number(deal.loan_term_years) : NaN;
  const hasFinancingInputs =
    Number.isFinite(purchaseNum) &&
    purchaseNum > 0 &&
    Number.isFinite(downPct) &&
    downPct >= 0 &&
    downPct <= 100 &&
    Number.isFinite(ratePct) &&
    ratePct >= 0 &&
    Number.isFinite(termYears) &&
    termYears >= 1 &&
    termYears <= 50;

  const computedLoanAmount = hasFinancingInputs
    ? purchaseNum * (1 - downPct / 100)
    : undefined;
  const computedMonthlyMortgage =
    hasFinancingInputs && computedLoanAmount != null && computedLoanAmount > 0
      ? computeMonthlyMortgage(computedLoanAmount, ratePct, termYears)
      : undefined;

  const loanAmountDisplay =
    deal.loan_amount != null ? Number(deal.loan_amount) : computedLoanAmount;
  const mortgage =
    deal.monthly_mortgage != null
      ? Number(deal.monthly_mortgage)
      : (computedMonthlyMortgage ?? 0);

  const isPreview = id === "preview";

  async function handleSaveDeal() {
    if (!stateInputs || !stateAddress?.trim()) {
      setSaveError("Missing form data. Go back and analyze again.");
      return;
    }
    const { address: addr, city, state, zip } = parseAddress(stateAddress);
    if (!addr) {
      setSaveError("Address is required to save.");
      return;
    }
    setSaveError(null);
    setSaveLoading(true);
    try {
      const propertyPayload: PropertyCreate = {
        address: addr,
        city: city || "Sheboygan",
        state: state || "WI",
        zip_code: zip || "53081",
        property_type: "duplex",
        num_units: 2,
      };
      const propRes = await api.post<PropertyResponse>(
        "/api/v1/properties/",
        propertyPayload,
      );
      const dealPayload: DealCreatePayload = {
        property_id: propRes.data.id,
        purchase_price: stateInputs.purchase_price,
        gross_monthly_rent: stateInputs.gross_monthly_rent,
        deal_name: stateInputs.deal_name,
        down_payment_pct: stateInputs.down_payment_pct,
        interest_rate: stateInputs.interest_rate,
        loan_term_years: stateInputs.loan_term_years,
        vacancy_rate_pct: stateInputs.vacancy_rate_pct,
        property_tax_monthly: stateInputs.property_tax_monthly,
        insurance_monthly: stateInputs.insurance_monthly,
        maintenance_rate_pct: stateInputs.maintenance_rate_pct,
        management_fee_pct: stateInputs.management_fee_pct,
        closing_costs: stateInputs.closing_costs,
        rehab_costs: stateInputs.rehab_costs,
        other_monthly_income: stateInputs.other_monthly_income,
        hoa_monthly: stateInputs.hoa_monthly,
        utilities_monthly: stateInputs.utilities_monthly,
      };
      const dealRes = await api.post<DealResponse>(
        "/api/v1/deals/",
        dealPayload,
      );
      navigate(`/deals/${dealRes.data.id}`);
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (
              err as {
                response?: { data?: { detail?: string | { detail?: string } } };
              }
            ).response?.data?.detail
          : null;
      setSaveError(
        typeof msg === "string"
          ? msg
          : msg && typeof msg === "object" && "detail" in msg
            ? String((msg as { detail: string }).detail)
            : "Failed to save deal. Try again.",
      );
    } finally {
      setSaveLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="font-sans text-2xl font-bold text-navy">
            Deal analysis
          </h1>
          {isPreview && !getToken() && (
            <span
              className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-slate"
              title="Results are not saved until you log in and save"
            >
              Guest preview
            </span>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-3">
          {isPreview && (
            <>
              {!getToken() ? (
                <Link
                  to="/login?redirect=/deals/preview"
                  className="rounded-lg border border-border bg-white px-4 py-2 text-sm font-medium text-slate no-underline hover:bg-blue-subtle"
                >
                  Log in to save
                </Link>
              ) : (
                <>
                  <button
                    type="button"
                    onClick={handleSaveDeal}
                    disabled={saveLoading}
                    className="rounded-lg bg-blue-primary px-4 py-2 text-sm font-medium text-white hover:bg-blue-light disabled:opacity-50"
                  >
                    {saveLoading ? "Saving…" : "Save deal"}
                  </button>
                  {saveError && (
                    <span className="text-sm text-red-negative">
                      {saveError}
                    </span>
                  )}
                </>
              )}
            </>
          )}
          <Link
            to="/analyze"
            className="rounded-lg border border-border bg-white px-4 py-2 text-sm font-medium text-slate no-underline hover:bg-blue-subtle"
          >
            New analysis
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <div className="break-words rounded-xl border border-border bg-white p-6 shadow-sm">
          <h2 className="text-sm font-medium text-muted">Monthly cash flow</h2>
          <p
            className={`font-mono text-3xl font-bold tabular-nums sm:text-4xl ${mcFlow != null && mcFlow >= 0 ? "text-green-positive" : "text-red-negative"}`}
          >
            {formatCurrency(deal.monthly_cash_flow)}
          </p>
        </div>
        <div className="break-words rounded-xl border border-border bg-white p-6 shadow-sm">
          <h2 className="text-sm font-medium text-muted">Risk score</h2>
          <p className="font-mono text-3xl font-bold tabular-nums text-navy sm:text-4xl">
            {score != null ? `Score: ${Math.round(score)}` : "—"}
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
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          <div className="break-words">
            <span className="text-sm text-muted">NOI (annual)</span>
            <p className="font-mono font-semibold tabular-nums text-slate">
              {formatCurrency(deal.noi)}
            </p>
          </div>
          <div className="break-words">
            <span className="text-sm text-muted">Cap rate</span>
            <p className="font-mono font-semibold tabular-nums text-slate">
              {formatPercent(deal.cap_rate)}
            </p>
          </div>
          <div className="break-words">
            <span className="text-sm text-muted">Cash-on-cash</span>
            <p className="font-mono font-semibold tabular-nums text-slate">
              {formatPercent(deal.cash_on_cash)}
            </p>
          </div>
          <div className="break-words">
            <span className="text-sm text-muted">DSCR</span>
            <p className="font-mono font-semibold tabular-nums text-slate">
              {formatNumber(deal.dscr)}
            </p>
          </div>
          <div className="break-words">
            <span className="text-sm text-muted">GRM</span>
            <p className="font-mono font-semibold tabular-nums text-slate">
              {formatNumber(deal.grm)}
            </p>
          </div>
          <div className="break-words">
            <span className="text-sm text-muted">Total cash invested</span>
            <p className="font-mono font-semibold tabular-nums text-slate">
              {formatCurrency(deal.total_cash_invested)}
            </p>
          </div>
        </div>
      </div>

      <div className="mt-8 grid grid-cols-1 gap-8 sm:grid-cols-2">
        <div className="break-words rounded-xl border border-border bg-white p-6 shadow-sm">
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
            {(hasFinancingInputs && computedLoanAmount != null) ||
            deal.loan_amount != null ? (
              <div className="flex justify-between">
                <dt className="text-muted">Loan amount</dt>
                <dd className="font-mono font-semibold text-slate">
                  {formatCurrency(loanAmountDisplay)}
                </dd>
              </div>
            ) : null}
            {hasFinancingInputs || deal.monthly_mortgage != null ? (
              <div className="flex justify-between">
                <dt className="text-muted">Monthly mortgage</dt>
                <dd className="font-mono font-semibold text-slate">
                  {formatCurrency(
                    deal.monthly_mortgage != null
                      ? Number(deal.monthly_mortgage)
                      : (computedMonthlyMortgage ?? 0),
                  )}
                </dd>
              </div>
            ) : null}
          </dl>
        </div>
        <div className="break-words rounded-xl border border-border bg-white p-6 shadow-sm">
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
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="break-words">
            <span className="text-sm text-muted">IRR 5 yr</span>
            <p className="font-mono font-semibold tabular-nums text-slate">
              {formatPercent(deal.irr_5yr)}
            </p>
          </div>
          <div className="break-words">
            <span className="text-sm text-muted">IRR 10 yr</span>
            <p className="font-mono font-semibold tabular-nums text-slate">
              {formatPercent(deal.irr_10yr)}
            </p>
          </div>
          <div className="break-words">
            <span className="text-sm text-muted">Equity buildup 5 yr</span>
            <p className="font-mono font-semibold tabular-nums text-slate">
              {formatCurrency(deal.equity_buildup_5yr)}
            </p>
          </div>
          <div className="break-words">
            <span className="text-sm text-muted">Equity buildup 10 yr</span>
            <p className="font-mono font-semibold tabular-nums text-slate">
              {formatCurrency(deal.equity_buildup_10yr)}
            </p>
          </div>
        </div>
      </div>

      {projections && projections.yearly_projections.length > 0 && (
        <div className="mt-8 rounded-xl border border-border bg-white p-6 shadow-sm">
          <h2 className="mb-6 font-sans text-lg font-semibold text-navy">
            {projections.parameters.projection_years}-Year Projections
          </h2>
          <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
            <div>
              <h3 className="mb-3 text-sm font-medium text-slate">
                Equity Buildup
              </h3>
              <EquityBuildupChart data={projections.yearly_projections} />
            </div>
            <div>
              <h3 className="mb-3 text-sm font-medium text-slate">
                Annual Cash Flow
              </h3>
              <CashFlowChart data={projections.yearly_projections} />
            </div>
            <div>
              <h3 className="mb-3 text-sm font-medium text-slate">
                Principal vs. Interest
              </h3>
              <AmortizationChart data={projections.yearly_projections} />
            </div>
          </div>
          {(projections.irr_5_year != null ||
            projections.irr_10_year != null) && (
            <div className="mt-6 grid grid-cols-2 gap-4 border-t border-border pt-4">
              <div>
                <span className="text-sm text-muted">
                  Projected IRR 5 yr
                </span>
                <p className="font-mono font-semibold tabular-nums text-slate">
                  {projections.irr_5_year != null
                    ? formatPercent(projections.irr_5_year * 100)
                    : "—"}
                </p>
              </div>
              <div>
                <span className="text-sm text-muted">
                  Projected IRR 10 yr
                </span>
                <p className="font-mono font-semibold tabular-nums text-slate">
                  {projections.irr_10_year != null
                    ? formatPercent(projections.irr_10_year * 100)
                    : "—"}
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {deal.risk_factors && Object.keys(deal.risk_factors).length > 0 && (
        <div className="mt-8 rounded-xl border border-border bg-white p-6 shadow-sm">
          <h2 className="mb-4 font-sans text-lg font-semibold text-navy">
            Risk factor breakdown
          </h2>
          <ul className="space-y-3">
            {Object.entries(deal.risk_factors).map(([key, val]) => {
              type RiskFactor = { score: number; raw?: string | number | null };
              const factor = (val ?? {}) as RiskFactor;
              const score =
                typeof factor.score === "number"
                  ? factor.score
                  : Number(factor.score) || 0;
              const raw = factor.raw;
              const pct = Math.min(100, Math.max(0, score));
              const rawNum =
                raw != null && raw !== ""
                  ? typeof raw === "number"
                    ? raw
                    : Number(raw)
                  : NaN;
              const isPercentLike =
                /vacancy|cap_rate|cash_on_cash|rate|pct|percent/i.test(key);
              const rawFormatted = Number.isFinite(rawNum)
                ? isPercentLike
                  ? rawNum.toFixed(1)
                  : rawNum.toFixed(2)
                : null;
              return (
                <li key={key} className="flex flex-wrap items-center gap-4">
                  <span className="w-40 shrink-0 text-sm text-slate">
                    {key
                      .replace(/_/g, " ")
                      .replace(/\b\w/g, (c) => c.toUpperCase())}
                  </span>
                  <div className="h-2 min-w-0 flex-1 overflow-hidden rounded-full bg-border">
                    <div
                      className="h-full rounded-full bg-blue-primary transition-all"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <span className="shrink-0 font-mono text-sm tabular-nums text-slate">
                    Score: {score.toFixed(0)}
                  </span>
                  {rawFormatted != null && (
                    <span
                      className="w-full shrink-0 text-xs text-muted sm:w-auto"
                      title="Raw metric"
                    >
                      raw: {rawFormatted}
                    </span>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
