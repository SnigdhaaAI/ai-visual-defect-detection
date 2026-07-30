/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Chakra Petch"', 'sans-serif'],
        body: ['"Inter"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        base: {
          950: '#07090c',
          900: '#0c0f13',
          850: '#10141a',
          800: '#141920',
          700: '#1b222a',
          600: '#242c36',
          500: '#323c48',
          400: '#48525f',
        },
        ink: {
          100: '#f1f4f7',
          300: '#c7cfd9',
          500: '#8b94a3',
          600: '#6b7482',
          700: '#4d5561',
        },
        accent: {
          300: '#7fe6dc',
          400: '#3fd6c8',
          500: '#17b8a9',
          600: '#0f8f84',
          glow: '#2dd4bf',
        },
        amber: {
          300: '#f8cd7a',
          400: '#f0b23e',
          500: '#e29a17',
          600: '#b87a0d',
        },
        signal: {
          teal: '#2dd4bf',
          tealDim: '#1a8c7f',
          red: '#ef5548',
          redDim: '#8a2f28',
        },
      },
      boxShadow: {
        panel: '0 1px 0 0 rgba(255,255,255,0.03) inset, 0 24px 48px -24px rgba(0,0,0,0.7)',
        panelHover: '0 1px 0 0 rgba(255,255,255,0.05) inset, 0 28px 56px -20px rgba(0,0,0,0.75)',
        glow: '0 0 0 1px rgba(63,214,200,0.18), 0 0 28px -4px rgba(63,214,200,0.35)',
        amberGlow: '0 0 0 1px rgba(240,178,62,0.2), 0 0 28px -4px rgba(240,178,62,0.4)',
        redGlow: '0 0 0 1px rgba(239,85,72,0.2), 0 0 28px -4px rgba(239,85,72,0.4)',
        inset: 'inset 0 1px 2px rgba(0,0,0,0.4)',
      },
      backgroundImage: {
        blueprint:
          'linear-gradient(rgba(63,214,200,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(63,214,200,0.04) 1px, transparent 1px)',
        blueprintFine:
          'linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)',
        noise:
          "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='60' height='60'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.03'/%3E%3C/svg%3E\")",
      },
      backgroundSize: {
        grid: '32px 32px',
        gridFine: '10px 10px',
      },
      keyframes: {
        scan: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(320%)' },
        },
        rise: {
          '0%': { opacity: 0, transform: 'translateY(10px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%': { opacity: 0 },
          '100%': { opacity: 1 },
        },
        pulseDot: {
          '0%, 100%': { opacity: 1 },
          '50%': { opacity: 0.35 },
        },
        pulseRing: {
          '0%': { transform: 'scale(0.9)', opacity: 0.6 },
          '80%, 100%': { transform: 'scale(1.6)', opacity: 0 },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        marquee: {
          '0%': { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(-50%)' },
        },
        drawIn: {
          '0%': { strokeDashoffset: 300 },
          '100%': { strokeDashoffset: 0 },
        },
        floatSlow: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-4px)' },
        },
      },
      animation: {
        scan: 'scan 2.4s linear infinite',
        rise: 'rise 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
        fadeIn: 'fadeIn 0.5s ease-out',
        pulseDot: 'pulseDot 1.6s ease-in-out infinite',
        pulseRing: 'pulseRing 2.2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        shimmer: 'shimmer 2.5s linear infinite',
        marquee: 'marquee 22s linear infinite',
        drawIn: 'drawIn 1s ease-out forwards',
        floatSlow: 'floatSlow 4s ease-in-out infinite',
      },
      transitionTimingFunction: {
        out: 'cubic-bezier(0.16, 1, 0.3, 1)',
      },
    },
  },
  plugins: [],
}
