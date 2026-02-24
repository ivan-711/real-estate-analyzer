import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import api, { getToken } from "../lib/api";
import type {
  DealCreatePayload,
  DealPreviewPayload,
  DealPreviewResponse,
  DealResponse,
  PropertyCreate,
  PropertyResponse,
} from "../types";

const MIDWEST_DEFAULTS = {
  down_payment_pct: "20",
  interest_rate: "7",
  loan_term_years: 30,
  vacancy_rate_pct: "5",
  property_tax_monthly: "300",
  insurance_monthly: "120",
  maintenance_rate_pct: "5",
  management_fee_pct: "10",
  closing_costs: "0",
  rehab_costs: "0",
  other_monthly_income: "0",
  hoa_monthly: "0",
  utilities_monthly: "0",
};

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

function validate(
  address: string,
  purchasePrice: string,
  grossMonthlyRent: string,
  advanced: typeof MIDWEST_DEFAULTS,
): string | null {
  const addrTrim = address.trim();
  if (addrTrim.length < 5) {
    return "Address is required (at least 5 characters).";
  }
  const purchase = Number(purchasePrice);
  if (Number.isNaN(purchase) || purchase <= 0) {
    return "Purchase price must be a number greater than 0.";
  }
  const rent = Number(grossMonthlyRent);
  if (Number.isNaN(rent) || rent < 0) {
    return "Gross monthly rent must be a number ≥ 0.";
  }
  const downPct = Number(advanced.down_payment_pct);
  if (!Number.isNaN(downPct) && (downPct < 0 || downPct > 100)) {
    return "Down payment % must be between 0 and 100.";
  }
  const rate = Number(advanced.interest_rate);
  if (!Number.isNaN(rate) && (rate < 0 || rate > 30)) {
    return "Interest rate must be between 0 and 30%.";
  }
  const term = Number(advanced.loan_term_years);
  if (!Number.isNaN(term) && (term < 1 || term > 50)) {
    return "Loan term must be between 1 and 50 years.";
  }
  const vacancy = Number(advanced.vacancy_rate_pct);
  if (!Number.isNaN(vacancy) && (vacancy < 0 || vacancy > 100)) {
    return "Vacancy % must be between 0 and 100.";
  }
  const tax = Number(advanced.property_tax_monthly);
  if (!Number.isNaN(tax) && tax < 0) {
    return "Property tax must be ≥ 0.";
  }
  const ins = Number(advanced.insurance_monthly);
  if (!Number.isNaN(ins) && ins < 0) {
    return "Insurance must be ≥ 0.";
  }
  const maint = Number(advanced.maintenance_rate_pct);
  if (!Number.isNaN(maint) && (maint < 0 || maint > 100)) {
    return "Maintenance % must be between 0 and 100.";
  }
  const mgmt = Number(advanced.management_fee_pct);
  if (!Number.isNaN(mgmt) && (mgmt < 0 || mgmt > 100)) {
    return "Management % must be between 0 and 100.";
  }
  return null;
}

export default function Analyze() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [accordionOpen, setAccordionOpen] = useState(false);

  const initialAddress = searchParams.get("address") ?? "";
  const initialPurchase = searchParams.get("purchase_price") ?? "";
  const initialRent = searchParams.get("gross_monthly_rent") ?? "";

  const [address, setAddress] = useState(initialAddress);
  const [purchasePrice, setPurchasePrice] = useState(initialPurchase);
  const [grossMonthlyRent, setGrossMonthlyRent] = useState(initialRent);
  const [advanced, setAdvanced] = useState(MIDWEST_DEFAULTS);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const validationError = validate(
      address,
      purchasePrice,
      grossMonthlyRent,
      advanced,
    );
    if (validationError) {
      setError(validationError);
      return;
    }
    setLoading(true);
    try {
      const isLoggedIn = !!getToken();
      if (!isLoggedIn) {
        const previewPayload: DealPreviewPayload = {
          purchase_price: purchasePrice,
          gross_monthly_rent: grossMonthlyRent,
          down_payment_pct: advanced.down_payment_pct,
          interest_rate: advanced.interest_rate,
          loan_term_years: advanced.loan_term_years,
          vacancy_rate_pct: advanced.vacancy_rate_pct,
          property_tax_monthly: advanced.property_tax_monthly,
          insurance_monthly: advanced.insurance_monthly,
          maintenance_rate_pct: advanced.maintenance_rate_pct,
          management_fee_pct: advanced.management_fee_pct,
          closing_costs: advanced.closing_costs,
          rehab_costs: advanced.rehab_costs,
          other_monthly_income: advanced.other_monthly_income,
          hoa_monthly: advanced.hoa_monthly,
          utilities_monthly: advanced.utilities_monthly,
        };
        const previewRes = await api.post<DealPreviewResponse>(
          "/api/v1/deals/preview",
          previewPayload,
        );
        navigate("/deals/preview", {
          state: { deal: previewRes.data, inputs: previewPayload, address },
        });
        return;
      }
      const { address: addr, city, state, zip } = parseAddress(address);
      if (!addr) {
        setError("Please fill in property address.");
        return;
      }
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
      const propertyId = propRes.data.id;

      const dealPayload: DealCreatePayload = {
        property_id: propertyId,
        purchase_price: purchasePrice,
        gross_monthly_rent: grossMonthlyRent,
        down_payment_pct: advanced.down_payment_pct,
        interest_rate: advanced.interest_rate,
        loan_term_years: advanced.loan_term_years,
        vacancy_rate_pct: advanced.vacancy_rate_pct,
        property_tax_monthly: advanced.property_tax_monthly,
        insurance_monthly: advanced.insurance_monthly,
        maintenance_rate_pct: advanced.maintenance_rate_pct,
        management_fee_pct: advanced.management_fee_pct,
        closing_costs: advanced.closing_costs,
        rehab_costs: advanced.rehab_costs,
        other_monthly_income: advanced.other_monthly_income,
        hoa_monthly: advanced.hoa_monthly,
        utilities_monthly: advanced.utilities_monthly,
      };
      const dealRes = await api.post<DealResponse>(
        "/api/v1/deals/",
        dealPayload,
      );
      navigate(`/deals/${dealRes.data.id}`);
    } catch (err: unknown) {
      const errMessage =
        err instanceof Error ? err.message : String(err ?? "");
      if (errMessage.includes("returned HTML")) {
        setError(
          "Guest preview is misconfigured. API base URL is pointing at the frontend. Fix VITE_API_URL.",
        );
        return;
      }
      const msg =
        err && typeof err === "object" && "response" in err
          ? (
              err as {
                response?: {
                  status?: number;
                  data?: { detail?: string | { detail?: string } };
                };
              }
            ).response?.data?.detail
          : null;
      if (
        (err as { response?: { status?: number } })?.response?.status === 401
      ) {
        setError("Session expired. Log in again to save deals to your portfolio.");
        return;
      }
      setError(
        typeof msg === "string"
          ? msg
          : msg && typeof msg === "object" && "detail" in msg
            ? String((msg as { detail: string }).detail)
            : "Something went wrong. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="font-sans text-2xl font-bold text-navy">Analyze a deal</h1>
      <p className="mt-1 text-slate">Enter property and financial details.</p>

      <form onSubmit={handleSubmit} className="mt-8 space-y-6">
        <div className="rounded-xl border border-border bg-white p-6 shadow-sm">
          <div className="space-y-4">
            <div>
              <label
                htmlFor="address"
                className="mb-1 block text-sm font-medium text-slate"
              >
                Property address
              </label>
              <input
                id="address"
                type="text"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder="e.g. 1515 N 7th St, Sheboygan WI 53081"
                className="w-full rounded-lg border border-border px-4 py-2.5 placeholder-muted focus:border-blue-primary focus:ring-2 focus:ring-blue-primary"
              />
            </div>
            <div>
              <label
                htmlFor="purchase_price"
                className="mb-1 block text-sm font-medium text-slate"
              >
                Purchase price ($)
              </label>
              <input
                id="purchase_price"
                type="text"
                inputMode="decimal"
                min={1}
                value={purchasePrice}
                onChange={(e) => setPurchasePrice(e.target.value)}
                placeholder="220000"
                className="font-mono w-full rounded-lg border border-border px-4 py-2.5 text-right placeholder-muted focus:border-blue-primary focus:ring-2 focus:ring-blue-primary"
              />
            </div>
            <div>
              <label
                htmlFor="gross_monthly_rent"
                className="mb-1 block text-sm font-medium text-slate"
              >
                Gross monthly rent ($)
              </label>
              <input
                id="gross_monthly_rent"
                type="text"
                inputMode="decimal"
                min={0}
                value={grossMonthlyRent}
                onChange={(e) => setGrossMonthlyRent(e.target.value)}
                placeholder="1700"
                className="font-mono w-full rounded-lg border border-border px-4 py-2.5 text-right placeholder-muted focus:border-blue-primary focus:ring-2 focus:ring-blue-primary"
              />
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-border bg-white shadow-sm">
          <button
            type="button"
            onClick={() => setAccordionOpen((o) => !o)}
            className="flex w-full items-center justify-between px-6 py-4 text-left font-medium text-slate hover:bg-off-white"
          >
            Advanced inputs (Midwest defaults)
            <span className="text-muted">{accordionOpen ? "−" : "+"}</span>
          </button>
          {accordionOpen && (
            <div className="border-t border-border px-6 py-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-sm text-muted">
                    Down payment %
                  </label>
                  <input
                    type="text"
                    inputMode="decimal"
                    min={0}
                    max={100}
                    value={advanced.down_payment_pct}
                    onChange={(e) =>
                      setAdvanced((a) => ({
                        ...a,
                        down_payment_pct: e.target.value,
                      }))
                    }
                    className="font-mono w-full rounded-lg border border-border px-3 py-2 text-right text-sm"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm text-muted">
                    Interest rate %
                  </label>
                  <input
                    type="text"
                    inputMode="decimal"
                    min={0}
                    max={30}
                    value={advanced.interest_rate}
                    onChange={(e) =>
                      setAdvanced((a) => ({
                        ...a,
                        interest_rate: e.target.value,
                      }))
                    }
                    className="font-mono w-full rounded-lg border border-border px-3 py-2 text-right text-sm"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm text-muted">
                    Loan term (years)
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={50}
                    value={advanced.loan_term_years}
                    onChange={(e) =>
                      setAdvanced((a) => ({
                        ...a,
                        loan_term_years: Number(e.target.value) || 30,
                      }))
                    }
                    className="font-mono w-full rounded-lg border border-border px-3 py-2 text-right text-sm"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm text-muted">
                    Vacancy %
                  </label>
                  <input
                    type="text"
                    inputMode="decimal"
                    min={0}
                    max={100}
                    value={advanced.vacancy_rate_pct}
                    onChange={(e) =>
                      setAdvanced((a) => ({
                        ...a,
                        vacancy_rate_pct: e.target.value,
                      }))
                    }
                    className="font-mono w-full rounded-lg border border-border px-3 py-2 text-right text-sm"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm text-muted">
                    Property tax $/mo
                  </label>
                  <input
                    type="text"
                    inputMode="decimal"
                    min={0}
                    value={advanced.property_tax_monthly}
                    onChange={(e) =>
                      setAdvanced((a) => ({
                        ...a,
                        property_tax_monthly: e.target.value,
                      }))
                    }
                    className="font-mono w-full rounded-lg border border-border px-3 py-2 text-right text-sm"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm text-muted">
                    Insurance $/mo
                  </label>
                  <input
                    type="text"
                    inputMode="decimal"
                    min={0}
                    value={advanced.insurance_monthly}
                    onChange={(e) =>
                      setAdvanced((a) => ({
                        ...a,
                        insurance_monthly: e.target.value,
                      }))
                    }
                    className="font-mono w-full rounded-lg border border-border px-3 py-2 text-right text-sm"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm text-muted">
                    Maintenance %
                  </label>
                  <input
                    type="text"
                    inputMode="decimal"
                    min={0}
                    max={100}
                    value={advanced.maintenance_rate_pct}
                    onChange={(e) =>
                      setAdvanced((a) => ({
                        ...a,
                        maintenance_rate_pct: e.target.value,
                      }))
                    }
                    className="font-mono w-full rounded-lg border border-border px-3 py-2 text-right text-sm"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm text-muted">
                    Management %
                  </label>
                  <input
                    type="text"
                    inputMode="decimal"
                    min={0}
                    max={100}
                    value={advanced.management_fee_pct}
                    onChange={(e) =>
                      setAdvanced((a) => ({
                        ...a,
                        management_fee_pct: e.target.value,
                      }))
                    }
                    className="font-mono w-full rounded-lg border border-border px-3 py-2 text-right text-sm"
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {error && (
          <div className="rounded-lg bg-red-light px-4 py-3 text-sm text-red-negative">
            {error}
            {error.includes("log in") && (
              <Link to="/login" className="ml-2 font-medium underline">
                Log in
              </Link>
            )}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-primary py-3 font-medium text-white hover:bg-blue-light disabled:opacity-50"
        >
          {loading ? (
            <>
              <svg
                className="h-5 w-5 animate-spin"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                aria-hidden="true"
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
              Analyzing…
            </>
          ) : (
            "Analyze"
          )}
        </button>
      </form>
    </div>
  );
}
