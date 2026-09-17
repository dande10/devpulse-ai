/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: "hsl(var(--card))",
        muted: "hsl(var(--muted))",
        primary: "hsl(var(--primary))",
        "primary-strong": "hsl(var(--primary-strong))",
        accent: "hsl(var(--accent))",
        success: "hsl(var(--success))",
        warning: "hsl(var(--warning))",
        danger: "hsl(var(--danger))"
      },
      boxShadow: {
        panel: "0 10px 30px rgba(15, 23, 42, 0.08)",
        card: "0 1px 2px rgba(15, 23, 42, 0.04), 0 8px 24px -12px rgba(15, 23, 42, 0.12)",
        "card-hover": "0 4px 10px rgba(15, 23, 42, 0.05), 0 16px 32px -14px rgba(15, 23, 42, 0.2)",
        glow: "0 0 0 3px hsl(var(--primary) / 0.15)"
      }
    }
  },
  plugins: []
};
