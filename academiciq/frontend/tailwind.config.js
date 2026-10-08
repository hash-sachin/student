/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          900: '#0c4a6e',
        },
        // Colorblind-safe palette (Section 20)
        attention: {
          normal: '#22c55e',      // green
          monitor: '#f59e0b',     // amber
          attention: '#f97316',   // orange
          high: '#ef4444',        // red
        },
        hypothetical: '#9333ea',  // purple — distinct from all others
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
