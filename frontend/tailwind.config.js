/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Sora', 'Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        obsidian: {
          900: '#0a0a0f',
          800: '#111118',
          700: '#1a1a25',
          600: '#242435',
          500: '#2e2e45',
        },
      },
    }
  },
  plugins: []
}
