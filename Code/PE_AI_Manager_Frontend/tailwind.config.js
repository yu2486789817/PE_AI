/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}'
  ],
  theme: {
    extend: {
      colors: {
        web: {
          primary: {
            50: '#eef4ff',
            100: '#dbe7ff',
            500: '#236df2',
            600: '#1d5fdd',
            700: '#1a4dac'
          },
          success: { 500: '#139769', 600: '#0f8059' },
          warning: { 500: '#ea8814', 600: '#c16e10' },
          danger: { 500: '#d63e35', 600: '#b4322a' },
          ink: {
            900: '#172033',
            700: '#2b3851',
            600: '#44516e',
            500: '#67748f'
          },
          line: { 100: '#e8edf7', 200: '#d8e0ee' },
          surface: {
            100: '#f7f9fe',
            200: '#eff3fb',
            card: '#ffffff'
          }
        }
      },
      borderRadius: {
        md: '12px',
        lg: '16px',
        xl: '22px'
      },
      boxShadow: {
        card: '0 10px 24px rgba(23, 56, 122, 0.08)',
        soft: '0 20px 40px rgba(15, 44, 96, 0.12)'
      },
      fontFamily: {
        display: ['"DIN Alternate"', '"Avenir Next"', '"PingFang SC"', '"Noto Sans SC"', 'sans-serif']
      }
    }
  },
  plugins: [import('@tailwindcss/typography')]
}
