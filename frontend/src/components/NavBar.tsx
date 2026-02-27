import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function NavBar() {
  const { isLoggedIn, logout } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

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
            {/* Desktop nav links — hidden on mobile */}
            <div className="hidden md:flex md:items-center md:gap-6">
              <Link
                to="/analyze"
                className="text-slate no-underline hover:text-blue-primary"
              >
                Analyze
              </Link>
              <Link
                to="/markets"
                className="text-slate no-underline hover:text-blue-primary"
              >
                Markets
              </Link>
              {isLoggedIn && (
                <>
                  <Link
                    to="/dashboard"
                    className="text-slate no-underline hover:text-blue-primary"
                  >
                    Dashboard
                  </Link>
                  <Link
                    to="/deals"
                    className="text-slate no-underline hover:text-blue-primary"
                  >
                    Deals
                  </Link>
                  <Link
                    to="/chat"
                    className="text-slate no-underline hover:text-blue-primary"
                  >
                    Chat
                  </Link>
                </>
              )}
            </div>
          </div>

          <div className="flex items-center gap-4">
            {isLoggedIn ? (
              <button
                type="button"
                onClick={() => {
                  logout();
                  navigate("/");
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
            {/* Hamburger — mobile only */}
            <button
              type="button"
              className="flex h-10 w-10 items-center justify-center rounded-lg text-slate hover:bg-section-bg md:hidden"
              onClick={() => setMenuOpen((o) => !o)}
              aria-label="Toggle menu"
            >
              {menuOpen ? (
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              ) : (
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M4 6h16M4 12h16M4 18h16"
                  />
                </svg>
              )}
            </button>
          </div>
        </div>

        {/* Mobile dropdown */}
        {menuOpen && (
          <div className="space-y-1 border-t border-border py-3 md:hidden">
            <Link
              to="/analyze"
              onClick={() => setMenuOpen(false)}
              className="block rounded-lg px-4 py-2 text-slate no-underline hover:bg-section-bg hover:text-blue-primary"
            >
              Analyze
            </Link>
            <Link
              to="/markets"
              onClick={() => setMenuOpen(false)}
              className="block rounded-lg px-4 py-2 text-slate no-underline hover:bg-section-bg hover:text-blue-primary"
            >
              Markets
            </Link>
            {isLoggedIn && (
              <>
                <Link
                  to="/dashboard"
                  onClick={() => setMenuOpen(false)}
                  className="block rounded-lg px-4 py-2 text-slate no-underline hover:bg-section-bg hover:text-blue-primary"
                >
                  Dashboard
                </Link>
                <Link
                  to="/deals"
                  onClick={() => setMenuOpen(false)}
                  className="block rounded-lg px-4 py-2 text-slate no-underline hover:bg-section-bg hover:text-blue-primary"
                >
                  Deals
                </Link>
                <Link
                  to="/chat"
                  onClick={() => setMenuOpen(false)}
                  className="block rounded-lg px-4 py-2 text-slate no-underline hover:bg-section-bg hover:text-blue-primary"
                >
                  Chat
                </Link>
              </>
            )}
          </div>
        )}
      </div>
    </nav>
  );
}
