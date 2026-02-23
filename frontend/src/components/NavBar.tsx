import { Link } from "react-router-dom";
import { clearToken, getToken } from "../lib/api";

export default function NavBar() {
  const isLoggedIn = !!getToken();

  return (
    <nav className="border-border bg-white shadow-sm">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-14 items-center justify-between">
          <div className="flex items-center gap-6">
            <Link
              to="/"
              className="font-sans text-lg font-bold text-navy no-underline hover:text-blue-primary"
            >
              MidwestDealAnalyzer
            </Link>
            <Link
              to="/analyze"
              className="text-slate no-underline hover:text-blue-primary"
            >
              Analyze
            </Link>
          </div>
          <div className="flex items-center gap-4">
            {isLoggedIn ? (
              <button
                type="button"
                onClick={() => {
                  clearToken();
                  window.location.href = "/";
                }}
                className="rounded-lg border border-border bg-white px-4 py-2 text-sm font-medium text-slate hover:bg-blue-subtle"
              >
                Log out
              </button>
            ) : (
              <>
                <Link
                  to="/login"
                  className="text-slate no-underline hover:text-blue-primary"
                >
                  Log in
                </Link>
                <Link
                  to="/register"
                  className="rounded-lg bg-blue-primary px-4 py-2 text-sm font-medium text-white no-underline hover:bg-blue-light"
                >
                  Register
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
