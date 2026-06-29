/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        nailong: {
          yellow: "#f8b33c",
          orange: "#ff9d34",
          "orange-dark": "#f70",
          cream: "#fff5df",
          "cream-dark": "#ffe9ba",
          gold: "#ff9b0f",
        },
      },
      borderRadius: {
        "3xl": "1.5rem",
        "4xl": "2rem",
        capsule: "82px",
      },
      boxShadow: {
        nailong: "0 4px 8px #f8b33c40",
        "nailong-lg": "0 8px 16px #f8b33c40",
      },
      animation: {
        "nailong-swing": "nailongSwing 0.8s ease-in-out infinite alternate",
        "nailong-float": "nailongFloat 3s ease-in-out infinite",
        "nailong-bounce-gentle": "nailongBounceGentle 2s ease-in-out infinite",
        "nailong-fade-in": "nailongFadeIn 0.8s ease-out",
        "nailong-slide-up": "nailongSlideUp 1s ease-out",
      },
      keyframes: {
        nailongSwing: {
          "0%": { transform: "rotate(-3deg)" },
          "100%": { transform: "rotate(3deg)" },
        },
        nailongFloat: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-10px)" },
        },
        nailongBounceGentle: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-6px)" },
        },
        nailongFadeIn: {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        nailongSlideUp: {
          "0%": { opacity: "0", transform: "translateY(40px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};
