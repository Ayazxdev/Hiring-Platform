/** @type {import('tailwindcss').Config} */
export default {
    darkMode: 'class',
    content: [
        "./index.html",
        "./src/**/*.{js,jsx}",
    ],
    theme: {
        extend: {
            fontFamily: {
                'montreal': ['Neue Montreal', 'sans-serif'],
                'inter': ['Inter Variable', 'sans-serif'],
                'grotesk': ['Space Grotesk', 'sans-serif'],
            },
            colors: {
                'bg-dark': '#1c1c1c',
                'text-light': '#e5e5e5',
                'accent-gray': '#9a9a9a',
                // Protocall AI Interview colors
                'p-teal': '#407E86',
                'p-gold': '#A58D66',
                'p-deep': '#083A4F',
                'p-white': '#F5F5F5',
                'p-pale': '#C0D5D6',
            },
        },
    },
    plugins: [],
}
