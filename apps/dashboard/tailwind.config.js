/**
 * Tailwind config for kirobi-dashboard.
 * Shared theme is mirrored from apps/_design/tailwind-theme.js — keep in sync.
 */
/** @type {import('tailwindcss').Config} */
const tailwindAnimate = (() => {
  try {
    return require('tailwindcss-animate');
  } catch {
    return null;
  }
})();

module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        kirobi: {
          50: '#ecfeff', 100: '#cffafe', 200: '#a5f3fc', 300: '#67e8f9',
          400: '#22d3ee', 500: '#06b6d4', 600: '#0891b2', 700: '#0e7490',
          800: '#155e75', 900: '#164e63', 950: '#083344',
        },
        aurora: {
          cyan: '#5eead4', magenta: '#e879f9', violet: '#a78bfa', gold: '#fbbf24',
        },
        void: { DEFAULT: '#040614', deep: '#080b1f', rise: '#0d1230' },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      letterSpacing: { display: '-0.02em' },
      boxShadow: {
        'glow-cyan': '0 0 24px rgba(94, 234, 212, 0.45), 0 0 48px rgba(94, 234, 212, 0.25)',
        'glow-magenta': '0 0 24px rgba(232, 121, 249, 0.4), 0 0 48px rgba(232, 121, 249, 0.2)',
        'glow-violet': '0 0 24px rgba(167, 139, 250, 0.4), 0 0 48px rgba(167, 139, 250, 0.2)',
        card: '0 1px 0 rgba(255,255,255,0.04) inset, 0 12px 32px -8px rgba(0,0,0,0.6)',
        float: '0 24px 48px -12px rgba(6,8,30,0.8), 0 0 0 1px rgba(255,255,255,0.06) inset',
      },
      transitionTimingFunction: {
        spring: 'cubic-bezier(0.16, 1, 0.3, 1)',
        glide: 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
      backgroundImage: {
        'aurora-text': 'linear-gradient(110deg, #5eead4 0%, #a78bfa 45%, #e879f9 100%)',
        'mesh-deep': 'radial-gradient(circle at 20% 10%, rgba(94,234,212,0.18), transparent 40%), radial-gradient(circle at 80% 0%, rgba(232,121,249,0.16), transparent 40%), radial-gradient(circle at 50% 100%, rgba(167,139,250,0.12), transparent 45%)',
      },
      animation: {
        'pulse-ring': 'pulse-ring 1.5s ease-out infinite',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'breathe': 'breathe 4s ease-in-out infinite',
        'orbit-slow': 'orbit-slow 24s linear infinite',
        'float-y': 'float-y 5s ease-in-out infinite',
        'shimmer': 'shimmer 1.6s linear infinite',
      },
      keyframes: {
        'pulse-ring': {
          '0%, 100%': { transform: 'scale(1)', opacity: '0.55' },
          '50%': { transform: 'scale(1.32)', opacity: '0' },
        },
        'breathe': {
          '0%, 100%': { opacity: '0.85', transform: 'scale(1)' },
          '50%': { opacity: '1', transform: 'scale(1.02)' },
        },
        'orbit-slow': { from: { transform: 'rotate(0deg)' }, to: { transform: 'rotate(360deg)' } },
        'float-y': { '0%, 100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(-6px)' } },
        'shimmer': { '0%': { backgroundPosition: '-200% 0' }, '100%': { backgroundPosition: '200% 0' } },
      },
    },
  },
  plugins: tailwindAnimate ? [tailwindAnimate] : [],
};
