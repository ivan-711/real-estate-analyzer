/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: "#1B2A4A",
        slate: "#334155",
        "off-white": "#F8FAFC",
        "blue-primary": "#2563EB",
        "blue-light": "#3B82F6",
        "blue-subtle": "#EFF6FF",
        "green-positive": "#16A34A",
        "green-light": "#DCFCE7",
        "yellow-moderate": "#CA8A04",
        "yellow-light": "#FEF9C3",
        "red-negative": "#DC2626",
        "red-light": "#FEE2E2",
        border: "#E2E8F0",
        muted: "#94A3B8",
        "section-bg": "#F1F5F9",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
};
