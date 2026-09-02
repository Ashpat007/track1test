import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bgDark: "#090a0f",
        sidebarDark: "#0c0c14",
        borderDark: "#1e2230",
        mutedText: "#6b6f85",
        pillActive: "#1c1c2e",
        navyAccent: "#0000D6",
        onlineGreen: "#5dcaa5",
        emeraldSuccess: "#10b981",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
    },
  },
  plugins: [],
};
export default config;
