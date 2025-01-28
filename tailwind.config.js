/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
      './templates/**/*.html',
      './static/src/**/*.js', // ถ้ามี JS files ที่ใช้ Tailwind classes
    ],
    theme: {
      extend: {},
    },
    plugins: [],
  }