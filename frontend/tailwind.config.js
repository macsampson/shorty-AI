/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#4a90e2",
        "primary-hover": "#3a80d2",
        secondary: "#6c757d",
        success: "#4caf50",
        warning: "#ff9800",
        danger: "#e74c3c",
      },
      keyframes: {
        spin: {
          "0%": { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
        fadeIn: {
          "0%": { opacity: "0", transform: "scale(0.95)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        pulse: {
          "0%": { opacity: "0.5" },
          "50%": { opacity: "1" },
          "100%": { opacity: "0.5" },
        },
      },
      animation: {
        spin: "spin 1s linear infinite",
        fadeIn: "fadeIn 0.5s ease-out",
        pulse: "pulse 1.5s infinite",
      },
      boxShadow: {
        settings: "0 10px 25px rgba(0, 0, 0, 0.2)",
      },
      borderRadius: {
        settings: "8px",
      },
    },
  },
  plugins: [],
}
