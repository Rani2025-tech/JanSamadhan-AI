/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        maroon: {
          50: '#FDF2F4',
          100: '#FCE7EB',
          200: '#F9D0D8',
          300: '#F4A9B7',
          400: '#EB728C',
          500: '#DC3F65',
          600: '#BF204A',
          700: '#9E153B',
          800: '#7A0F2E', // Primary maroon from design tokens
          900: '#641029',
          950: '#3A0515',
        },
        saffron: {
          50: '#FFF9F0',
          100: '#FFF0D9',
          200: '#FFDFB0',
          300: '#FFC67E',
          400: '#FFA445',
          500: '#F28C28', // Primary saffron
          600: '#DE6E13',
          700: '#B85010',
          800: '#933F14',
          950: '#501F07',
        },
        cream: {
          50: '#FFFFFF',
          100: '#FFFDF9',
          200: '#FFFBF5',
          300: '#FFF8F0',
          400: '#FFF6EE', // Primary cream background
          500: '#F5E6D8',
          600: '#E6D2BF',
        },
        status: {
          submitted: '#7A0F2E',
          assigned: '#2563EB',
          inprogress: '#D97706',
          resolved: '#16A34A',
          critical: '#DC2626',
        }
      },
      fontFamily: {
        sans: [
          '"Noto Sans"',
          '"Noto Sans Devanagari"',
          '"Noto Sans Oriya"',
          '"Noto Sans Bengali"',
          '"Noto Sans Tamil"',
          '"Noto Sans Telugu"',
          'system-ui',
          '-apple-system',
          'sans-serif'
        ],
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
      boxShadow: {
        'soft': '0 4px 20px -2px rgba(122, 15, 46, 0.08), 0 2px 6px -1px rgba(0, 0, 0, 0.04)',
        'soft-lg': '0 10px 30px -4px rgba(122, 15, 46, 0.12), 0 4px 10px -2px rgba(0, 0, 0, 0.05)',
      }
    },
  },
  plugins: [],
}

