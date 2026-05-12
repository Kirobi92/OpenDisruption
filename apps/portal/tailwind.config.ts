import type { Config } from 'tailwindcss';
const config: Config = {
  content: ['./src/pages/**/*.{js,ts,jsx,tsx,mdx}','./src/components/**/*.{js,ts,jsx,tsx,mdx}','./src/app/**/*.{js,ts,jsx,tsx,mdx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        kirobi: { 50:'#ecfeff',100:'#cffafe',200:'#a5f3fc',300:'#67e8f9',400:'#22d3ee',500:'#06b6d4',600:'#0891b2',700:'#0e7490',800:'#155e75',900:'#164e63',950:'#083344' },
        aurora: { cyan:'#5eead4', magenta:'#e879f9', violet:'#a78bfa', gold:'#fbbf24' },
        void: { DEFAULT:'#040614', deep:'#080b1f', rise:'#0d1230' },
      },
      fontFamily: { sans: ['Inter','ui-sans-serif','system-ui','-apple-system','Segoe UI','Roboto','sans-serif'] },
      boxShadow: {
        'glow-cyan': '0 0 24px rgba(94,234,212,0.45), 0 0 48px rgba(94,234,212,0.25)',
        'glow-magenta': '0 0 24px rgba(232,121,249,0.4), 0 0 48px rgba(232,121,249,0.2)',
        'glow-violet': '0 0 24px rgba(167,139,250,0.4)',
        card: '0 1px 0 rgba(255,255,255,0.04) inset, 0 12px 32px -8px rgba(0,0,0,0.6)',
      },
    },
  },
  plugins: [],
};
export default config;
