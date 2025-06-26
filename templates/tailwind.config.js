// tailwind.config.js
module.exports = {
  content: ["./templates/**/*.html", "./static/**/*.js"], // ajuste conforme seu projeto
  theme: {
    extend: {
      keyframes: {
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'fade-up': 'fade-up 1s ease-out forwards',
      },
    },
    fontFamily: {
      montserrat: ['Montserrat', 'sans-serif'],
    },
  },
  plugins: [],
}
