/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './projects.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        generalsans: ['General Sans', 'sans-serif'],
      },
      colors: {
        // Every shade resolves through a CSS variable defined per theme in
        // src/index.css, so components never care which theme is active.
        black: {
          DEFAULT: '#000',
          100: 'rgb(var(--color-black-100) / <alpha-value>)',
          200: 'rgb(var(--color-black-200) / <alpha-value>)',
          300: 'rgb(var(--color-black-300) / <alpha-value>)',
          500: 'rgb(var(--color-black-500) / <alpha-value>)',
          600: 'rgb(var(--color-black-600) / <alpha-value>)',
        },
        white: {
          DEFAULT: '#FFFFFF',
          900: 'rgb(var(--color-white-900) / <alpha-value>)',
          800: 'rgb(var(--color-white-800) / <alpha-value>)',
          700: 'rgb(var(--color-white-700) / <alpha-value>)',
          600: 'rgb(var(--color-white-600) / <alpha-value>)',
          500: 'rgb(var(--color-white-500) / <alpha-value>)',
        },
        accent: 'rgb(var(--theme-accent) / <alpha-value>)',
        'on-accent': 'rgb(var(--on-accent) / <alpha-value>)',
      },
      backgroundImage: {
        terminal: "url('/assets/terminal.png')",
      },
    },
  },
  plugins: [],
};