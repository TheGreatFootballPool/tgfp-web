/** @type {import('tailwindcss').Config} */
module.exports = {
  mode: 'jit',
  content: ["../templates/**/*.j2"],
  theme: {
    extend: {},
    fontFamily: {
      'header': ['verdana', 'sans-serif']
    }
  },
  plugins: [],
};
