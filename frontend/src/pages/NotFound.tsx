import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-md px-4 py-16 text-center">
      <h1 className="font-sans text-2xl font-bold text-navy">Page not found</h1>
      <p className="mt-2 text-slate">The page you’re looking for doesn’t exist.</p>
      <Link
        to="/analyze"
        className="mt-6 inline-block rounded-lg bg-blue-primary px-4 py-2 font-medium text-white no-underline hover:bg-blue-light"
      >
        Go to Analyze
      </Link>
    </div>
  );
}
