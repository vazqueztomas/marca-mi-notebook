import type { Config } from 'tailwindcss'

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        surface: "var(--surface)",
        ink: "var(--ink)",
        "ink-soft": "var(--ink-soft)",
        "ink-faint": "var(--ink-faint)",
        celeste: "var(--celeste)",
        "celeste-soft": "var(--celeste-soft)",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      }
    },
  },
  plugins: [],
} satisfies Config
