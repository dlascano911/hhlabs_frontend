/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'crypto': {
          'dark': '#0d1117',
          'darker': '#010409',
          'card': '#161b22',
          'border': '#30363d',
          'green': '#3fb950',
          'red': '#f85149',
          'blue': '#58a6ff',
          'purple': '#a371f7',
          'yellow': '#d29922',
          'orange': '#db6d28',
        }
      }
    },
  },
  plugins: [],
}
