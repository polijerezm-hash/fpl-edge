/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0d120f",
        surface: "#151c18",
        surfaceHover: "#1d2721",
        surfaceBorder: "#2c3931",
        primary: {
          DEFAULT: "#a8d741",
          hover: "#b9e45b",
          light: "#d4ef97",
        },
        secondary: {
          DEFAULT: "#e5b85c",
          violet: "#b99bd8",
        },
        pitch: {
          grass: "#173e28",
          line: "#a8d741",
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
