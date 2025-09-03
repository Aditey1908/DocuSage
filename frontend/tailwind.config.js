/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'light-beige': '#dad7cd',
        'sage': '#a3b18a',
        'moss': '#588157',
        'forest': '#3a5a40',
        'dark-forest': '#344e41',
      },
      animation: {
        'first': 'moveVertical 25s ease infinite',
        'second': 'moveInCircle 18s reverse infinite',
        'third': 'moveInCircle 35s linear infinite',
        'fourth': 'moveHorizontal 30s ease infinite',
        'fifth': 'moveInCircle 22s ease infinite',
        'shimmer': 'shimmer 2s linear infinite',
        'pulse-slow': 'pulse 3s ease-in-out infinite',
        'bounce-slow': 'bounce 3s infinite',
        'fadeIn': 'fadeIn 1.5s ease-in-out',
        'glow': 'glow 2.5s ease-in-out infinite alternate',
        'float': 'float 6s ease-in-out infinite',
      },
      keyframes: {
        moveHorizontal: {
          '0%': { transform: 'translateX(-50%) translateY(-10%)' },
          '50%': { transform: 'translateX(50%) translateY(10%)' },
          '100%': { transform: 'translateX(-50%) translateY(-10%)' },
        },
        moveInCircle: {
          '0%': { transform: 'rotate(0deg)' },
          '50%': { transform: 'rotate(180deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
        moveVertical: {
          '0%': { transform: 'translateY(-50%)' },
          '50%': { transform: 'translateY(50%)' },
          '100%': { transform: 'translateY(-50%)' },
        },
        shimmer: {
          from: { backgroundPosition: '0 0' },
          to: { backgroundPosition: '-200% 0' },
        },
        fadeIn: {
          '0%': { opacity: 0, transform: 'translateY(-10px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        },
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(156, 39, 176, 0.3), 0 0 8px rgba(156, 39, 176, 0.3)' },
          '100%': { boxShadow: '0 0 10px rgba(156, 39, 176, 0.6), 0 0 20px rgba(156, 39, 176, 0.3), 0 0 30px rgba(156, 39, 176, 0.2)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
      },
    },
  },
  plugins: [],
}

