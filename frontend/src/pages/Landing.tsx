import { Link } from "react-router-dom";

const SAMPLE_ADDRESS = "1515 N 7th St";
const SAMPLE_CITY = "Sheboygan";
const SAMPLE_STATE = "WI";
const SAMPLE_ZIP = "53081";
const SAMPLE_PURCHASE = "220000";
const SAMPLE_RENT = "1700";
const SAMPLE_BEDS = 5;
const SAMPLE_BATHS = 2;

export default function Landing() {
  const sampleQuery = new URLSearchParams({
    address: `${SAMPLE_ADDRESS}, ${SAMPLE_CITY} ${SAMPLE_STATE} ${SAMPLE_ZIP}`,
    purchase_price: SAMPLE_PURCHASE,
    gross_monthly_rent: SAMPLE_RENT,
    bedrooms: String(SAMPLE_BEDS),
    bathrooms: String(SAMPLE_BATHS),
  }).toString();

  return (
    <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="text-center">
        <h1 className="font-sans text-4xl font-bold tracking-tight text-navy sm:text-5xl">
          MidwestDealAnalyzer
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-lg text-slate">
          Analyze rental property deals in the Midwest
        </p>
        <div className="mt-10">
          <Link
            to={`/analyze?${sampleQuery}`}
            className="inline-flex rounded-lg bg-blue-primary px-6 py-3 text-base font-medium text-white no-underline hover:bg-blue-light"
          >
            Try Sample Deal
          </Link>
        </div>
        <p className="mt-4 text-sm text-muted">
          1515 N 7th St, Sheboygan WI — $220,000 · $1,700/mo · 5 bed / 2 bath
        </p>
      </div>
    </div>
  );
}
