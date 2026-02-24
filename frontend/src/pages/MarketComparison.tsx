import { useState } from "react";
import BlurText from "../components/ui/BlurText";
import SpotlightCard from "../components/ui/SpotlightCard";
import { getMarketComparison } from "../lib/api";
import type { MarketSnapshot } from "../types";

// ─── Formatting helpers ──────────────────────────────────────────────────────

function fmtCurrency(n: number | null): string {
  if (n === null) return "";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(n);
}

function fmtPct(n: number | null): string {
  if (n === null) return "";
  return `${Number(n).toFixed(2)}%`;
}

function fmtRatio(n: number | null): string {
  if (n === null) return "";
  return Number(n).toFixed(4);
}

// ─── Zip validation ──────────────────────────────────────────────────────────

function isValidZip(z: string): boolean {
  return /^\d{5}$/.test(z.trim());
}

// ─── Row definitions ─────────────────────────────────────────────────────────

type BestDir = "highest" | "lowest" | null;
type RowKey = keyof MarketSnapshot | "location";

interface RowDef {
  label: string;
  key: RowKey;
  format: "location" | "currency" | "pct" | "ratio";
  bestDir: BestDir;
}

const ROWS: RowDef[] = [
  { label: "Location", key: "location", format: "location", bestDir: null },
  {
    label: "Median Home Value",
    key: "median_home_value",
    format: "currency",
    bestDir: "lowest",
  },
  { label: "Median Rent", key: "median_rent", format: "currency", bestDir: "highest" },
  {
    label: "Rent-to-Price Ratio",
    key: "rent_to_price_ratio",
    format: "ratio",
    bestDir: "highest",
  },
  {
    label: "YoY Appreciation",
    key: "yoy_appreciation_pct",
    format: "pct",
    bestDir: "highest",
  },
  {
    label: "Vacancy Rate",
    key: "avg_vacancy_rate",
    format: "pct",
    bestDir: "lowest",
  },
  {
    label: "Population Growth",
    key: "population_growth_pct",
    format: "pct",
    bestDir: "highest",
  },
];

// ─── Best-value index per row ─────────────────────────────────────────────────

function bestIndex(snapshots: MarketSnapshot[], key: RowKey, dir: BestDir): number | null {
  if (dir === null || key === "location") return null;
  const values = snapshots.map((s) => {
    const v = s[key as keyof MarketSnapshot];
    return typeof v === "number" ? v : null;
  });
  const defined = values.filter((v): v is number => v !== null);
  if (defined.length < 2) return null;
  const target =
    dir === "highest" ? Math.max(...defined) : Math.min(...defined);
  const idx = values.indexOf(target);
  return idx === -1 ? null : idx;
}

// ─── Cell renderer ────────────────────────────────────────────────────────────

function CellValue({
  snap,
  row,
}: {
  snap: MarketSnapshot;
  row: RowDef;
}): React.ReactElement {
  if (row.key === "location") {
    const loc = [snap.city, snap.state].filter(Boolean).join(", ");
    return <span className="font-medium text-navy">{loc || snap.zip_code}</span>;
  }

  const raw = snap[row.key as keyof MarketSnapshot] as number | null;

  if (raw === null) {
    return <span className="text-muted">N/A</span>;
  }

  let formatted = "";
  if (row.format === "currency") formatted = fmtCurrency(raw);
  else if (row.format === "pct") formatted = fmtPct(raw);
  else if (row.format === "ratio") formatted = fmtRatio(raw);

  return <span className="font-mono tabular-nums text-slate">{formatted}</span>;
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function MarketComparison(): React.ReactElement {
  const [zipInputs, setZipInputs] = useState<string[]>(["53081", "53202"]);
  const [snapshots, setSnapshots] = useState<MarketSnapshot[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const allValid = zipInputs.every((z) => isValidZip(z));
  const canCompare = allValid && !loading;

  function handleZipChange(idx: number, value: string) {
    setZipInputs((prev) => prev.map((z, i) => (i === idx ? value : z)));
  }

  function handleAddZip() {
    if (zipInputs.length < 5) setZipInputs((prev) => [...prev, ""]);
  }

  function handleRemoveZip(idx: number) {
    if (zipInputs.length <= 2) return;
    setZipInputs((prev) => prev.filter((_, i) => i !== idx));
  }

  function handleCompare() {
    setLoading(true);
    setError(null);
    setHasSearched(true);
    getMarketComparison(zipInputs.map((z) => z.trim()))
      .then(setSnapshots)
      .catch(() =>
        setError(
          "Failed to fetch market data. Check your zip codes and try again.",
        ),
      )
      .finally(() => setLoading(false));
  }

  // ── Loading skeleton ────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-8">
        <div className="mb-2 h-9 w-64 animate-pulse rounded bg-border" />
        <div className="mb-8 h-5 w-80 animate-pulse rounded bg-border" />
        <div className="mb-8 flex gap-3">
          {[1, 2].map((i) => (
            <div key={i} className="h-10 w-32 animate-pulse rounded-lg bg-border" />
          ))}
        </div>
        <div className="overflow-x-auto rounded-xl border border-border bg-white shadow-sm">
          <div className="grid grid-cols-3 gap-0">
            {Array.from({ length: 21 }).map((_, i) => (
              <div
                key={i}
                className="h-12 animate-pulse border-b border-border bg-border/40 last:border-0"
              />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      {/* ── Header ──────────────────────────────────────────────────────────── */}
      <BlurText
        text="Market Comparison"
        as="h1"
        delay={80}
        className="mb-1 font-sans text-2xl font-bold text-navy"
      />
      <p className="mb-8 text-sm text-muted">
        Compare real estate markets across Midwest zip codes
      </p>

      {/* ── Input section ───────────────────────────────────────────────────── */}
      <div className="mb-8 rounded-xl border border-border bg-white p-6 shadow-sm">
        <p className="mb-4 text-sm font-medium text-slate">
          Enter 2–5 zip codes to compare
        </p>

        <div className="flex flex-wrap gap-3">
          {zipInputs.map((zip, idx) => {
            const touched = zip.length > 0;
            const invalid = touched && !isValidZip(zip);
            return (
              <div key={idx} className="flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    inputMode="numeric"
                    maxLength={5}
                    placeholder="e.g. 53081"
                    value={zip}
                    onChange={(e) => handleZipChange(idx, e.target.value)}
                    className={`w-32 rounded-lg border px-3 py-2 font-mono text-sm text-navy focus:outline-none focus:ring-2 focus:ring-blue-primary ${
                      invalid
                        ? "border-red-negative bg-red-50 focus:ring-red-negative"
                        : "border-border bg-white"
                    }`}
                  />
                  <button
                    type="button"
                    onClick={() => handleRemoveZip(idx)}
                    disabled={zipInputs.length <= 2}
                    className="rounded p-1 text-muted hover:text-red-negative disabled:cursor-not-allowed disabled:opacity-30"
                    aria-label="Remove zip code"
                  >
                    ✕
                  </button>
                </div>
                {invalid && (
                  <p className="text-xs text-red-negative">Must be 5 digits</p>
                )}
              </div>
            );
          })}
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={handleAddZip}
            disabled={zipInputs.length >= 5}
            className="rounded-lg border border-border bg-white px-4 py-2 text-sm font-medium text-slate hover:bg-blue-subtle disabled:cursor-not-allowed disabled:opacity-40"
          >
            + Add Zip Code
          </button>

          <button
            type="button"
            onClick={handleCompare}
            disabled={!canCompare}
            className="rounded-lg bg-blue-primary px-5 py-2 text-sm font-medium text-white hover:bg-blue-light disabled:cursor-not-allowed disabled:opacity-50"
          >
            Compare Markets
          </button>
        </div>
      </div>

      {/* ── Error state ─────────────────────────────────────────────────────── */}
      {error && (
        <div className="mb-6 flex items-center justify-between rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-negative">
          <span>{error}</span>
          <button
            type="button"
            onClick={handleCompare}
            className="ml-4 font-medium underline hover:no-underline"
          >
            Retry
          </button>
        </div>
      )}

      {/* ── Empty state ─────────────────────────────────────────────────────── */}
      {!hasSearched && !error && (
        <div className="rounded-xl border border-border bg-white p-10 text-center text-slate shadow-sm">
          <p className="text-base">Enter zip codes above to compare markets</p>
          <p className="mt-1 text-sm text-muted">
            Try 53081 (Sheboygan) vs 53202 (Milwaukee) to get started
          </p>
        </div>
      )}

      {/* ── No results (API returned empty after search) ─────────────────────── */}
      {hasSearched && !error && snapshots.length === 0 && (
        <div className="rounded-xl border border-border bg-white p-10 text-center text-slate shadow-sm">
          <p>No market data found for the entered zip codes.</p>
          <p className="mt-1 text-sm text-muted">
            Try zip codes in Wisconsin, Illinois, Michigan, or Minnesota.
          </p>
        </div>
      )}

      {/* ── Results table ───────────────────────────────────────────────────── */}
      {hasSearched && !error && snapshots.length > 0 && (
        <>
          <div className="mb-4 flex flex-wrap gap-2">
            {snapshots.map((s) => (
              <SpotlightCard
                key={s.id}
                className="rounded-lg border border-border bg-white px-3 py-1.5 shadow-sm"
                spotlightColor="rgba(59, 130, 246, 0.12)"
              >
                <span className="font-mono text-sm font-medium text-navy">
                  {s.zip_code}
                </span>
                {s.city && (
                  <span className="ml-1 text-xs text-muted">
                    — {s.city}, {s.state}
                  </span>
                )}
              </SpotlightCard>
            ))}
          </div>

          <div className="overflow-x-auto rounded-xl border border-border bg-white shadow-sm">
            <table className="w-full min-w-max border-collapse text-sm">
              <thead>
                <tr className="border-b border-border bg-section-bg">
                  <th className="px-5 py-3 text-left font-medium text-muted">
                    Metric
                  </th>
                  {snapshots.map((s) => (
                    <th
                      key={s.id}
                      className="px-5 py-3 text-left font-medium text-navy"
                    >
                      {s.zip_code}
                      {s.city && (
                        <span className="ml-1 font-normal text-muted">
                          ({s.city})
                        </span>
                      )}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {ROWS.map((row, rowIdx) => {
                  const best = bestIndex(snapshots, row.key, row.bestDir);
                  return (
                    <tr
                      key={row.key}
                      className={
                        rowIdx % 2 === 0 ? "bg-white" : "bg-section-bg/50"
                      }
                    >
                      <td className="border-b border-border px-5 py-3 font-medium text-slate">
                        {row.label}
                      </td>
                      {snapshots.map((snap, colIdx) => (
                        <td
                          key={snap.id}
                          className={`border-b border-border px-5 py-3 ${
                            best === colIdx
                              ? "bg-green-50 font-medium"
                              : ""
                          }`}
                        >
                          <CellValue snap={snap} row={row} />
                          {best === colIdx && row.bestDir !== null && (
                            <span className="ml-2 text-xs text-green-positive">
                              ✓ best
                            </span>
                          )}
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <p className="mt-3 text-right text-xs text-muted">
            Data from{" "}
            {snapshots
              .map((s) => s.data_source ?? "unknown")
              .filter((v, i, a) => a.indexOf(v) === i)
              .join(", ")}
            {" · "}
            Snapshot date:{" "}
            {snapshots[0]?.snapshot_date ?? "—"}
          </p>
        </>
      )}
    </div>
  );
}
