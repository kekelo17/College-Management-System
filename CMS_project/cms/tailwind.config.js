/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    '../templates/**/*.html',          // Project-level templates
    '../**/templates/**/*.html',       // App templates (accounts, core, etc.)
  ],
  theme: {
    extend: {},
  },
  plugins: [
    require('daisyui').default,
  ],
  daisyui: {
    themes: ["light", "dark", "corporate", "synthwave"], // You can customize themes
    base: true,
    styled: true,
    utils: true,
  },
}
