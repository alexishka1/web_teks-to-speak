import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        surface: "var(--surface)",
        card: "var(--surface)",
        panel: "var(--panel)",
        border: "var(--border)",
        "border-subtle": "var(--border-subtle)",
        fg: "var(--text)",
        muted: "var(--muted)",
        hover: "var(--hover)",
        primary: "var(--primary)",
        "primary-fg": "var(--primary-fg)",
        "primary-hover": "var(--primary-hover)",
        // Strict neutral tokens for dark/light state
        accent: "var(--primary)",
        "accent-hover": "var(--primary-hover)",
      },
      fontFamily: {
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "system-ui",
          "sans-serif",
        ],
        mono: [
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          "monospace",
        ],
      },
      borderRadius: {
        DEFAULT: "6px",
        md: "6px",
        lg: "8px",
        xl: "10px",
      },
    },
  },
  plugins: [],
};

export default config;
