/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#1e40af',
        danger: '#dc2626',
        success: '#16a34a',
        warning: '#ea580c',
      }
    },
  },
  plugins: [],
}