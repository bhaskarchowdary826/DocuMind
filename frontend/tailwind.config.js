/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        beige: {
          50: '#faf9f7',
          100: '#f5f3f0',
          200: '#ebe6df',
          300: '#dcd4c8',
          400: '#c9bdaa',
          500: '#b8a68f',
          600: '#a8927a',
          700: '#8b7864',
          800: '#736454',
          900: '#5f5347',
        },
      },
    },
  },
  plugins: [],
}


