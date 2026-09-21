/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0b0f19",
        surface: "#131b2e",
        surfaceHover: "#1c2742",
        surfaceBorder: "#223152",
        primary: {
          DEFAULT: "#10b981",
          hover: "#059669",
          light: "#34d399",
        },
        secondary: {
          DEFAULT: "#06b6d4",
          violet: "#8b5cf6",
        },
        pitch: {
          grass: "#064e3b",
          line: "#10b981",
        }
      },
    },
  },
  plugins: [],
};
