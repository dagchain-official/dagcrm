/** @type {import('tailwindcss').Config} */
const ink = (v) => `rgb(var(--ink-${v}) / <alpha-value>)`;

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef2ff", 100: "#e0e7ff", 200: "#c7d2fe", 300: "#a5b4fc",
          400: "#818cf8", 500: "#6366f1", 600: "#4f46e5", 700: "#4338ca",
          800: "#3730a3", 900: "#312e81",
        },
        // `ink` is themeable: tokens flip in dark mode (see index.css).
        // ink-0 = card/panel surface (white in light, slate in dark).
        ink: {
          0: ink(0), 50: ink(50), 100: ink(100), 200: ink(200), 300: ink(300),
          400: ink(400), 500: ink(500), 600: ink(600), 700: ink(700),
          800: ink(800), 900: ink(900),
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(15,23,42,.04), 0 1px 3px rgba(15,23,42,.04)",
        soft: "0 6px 30px rgba(15,23,42,.05)",
      },
      borderRadius: {
        "2xl": "1rem",
        "3xl": "1.5rem",
      },
    },
  },
  plugins: [],
};
