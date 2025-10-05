import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        surface: "var(--surface)",
        ink: "var(--ink)",
        "muted-ink": "var(--muted-ink)",
        accent: "var(--accent)",
        accent2: "var(--accent-2)",
        "accent2-pressed": "var(--accent-2-pressed)",
        line: "var(--line)",
        white: "var(--white)"
      },
      fontFamily: {
        serif: ['"Cormorant Garamond"', "Georgia", "serif"],
        sans: ["Inter", "system-ui", "Segoe UI", "Roboto", "sans-serif"]
      },
      borderRadius: {
        xl: "24px",
        pill: "9999px"
      },
      boxShadow: {
        soft: "0 10px 24px rgba(0,0,0,0.06)"
      },
      letterSpacing: {
        widecaps: ".1em"
      },
      container: {
        center: true,
        padding: "1.25rem",
        screens: { "2xl": "1400px" }
      }
    }
  },
  plugins: []
} satisfies Config;
