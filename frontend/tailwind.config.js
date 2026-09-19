/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        graphite: '#16181d',
        card: '#1e2128',
        accent: '#ff9d2e',
        profit: '#34d399',
        danger: '#f87171',
      },
    },
  },
  plugins: [],
};
