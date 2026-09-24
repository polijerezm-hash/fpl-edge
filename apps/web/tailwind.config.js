/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#f8fafc",
        surface: "#ffffff",
        surfaceHover: "#f1f5f9",
        surfaceBorder: "#e2e8f0",
        primary: {
          DEFAULT: "#4f46e5",
          hover: "#4338ca",
          light: "#e0e7ff",
        },
        secondary: {
          DEFAULT: "#e5b85c",
          violet: "#b99bd8",
        },
        pitch: {
          grass: "#e9f7ef",
          line: "#047857",
        }
      },
      borderRadius: {
        xl: "0.55rem",
        "2xl": "0.7rem",
        "3xl": "0.85rem",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
    },
  },
  plugins: [],
};
