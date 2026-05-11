import { useEffect } from "react";

const useParallax = () => {
  useEffect(() => {
    const handleScroll = () => {
      const parallaxElements = document.querySelectorAll(".parallax, .hero");

      parallaxElements.forEach((el) => {
        const speed = 0.5; // ajusta la velocidad del efecto
        const yOffset = window.scrollY * speed;
        el.style.backgroundPosition = `center calc(50% + ${yOffset}px)`;
      });
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);
};

export default useParallax;
