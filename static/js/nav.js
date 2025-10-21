const header = document.querySelector(".smd-layout_header");
let ticking = false;
let lastScrollY = 0;
let isFloating = false;
let animationPhase = 0; // 0 = normal, 1 = transitioning, 2 = floating
const isMobile = window.innerWidth <= 768;
const threshold = isMobile ? 15 : 25;
const anchorZone = 5;

function updateHeader() {
  const scrollY = window.scrollY;

  if (scrollY === lastScrollY) {
    ticking = false;
    return;
  }

  const shouldFloat = scrollY > threshold;
  const scrollDirection = scrollY > lastScrollY ? 'down' : 'up';

  // Smooth transition logic with phases
  if (shouldFloat && !isFloating) {
    // Start floating transition
    if (animationPhase === 0) {
      animationPhase = 1;
      header.classList.add("smd-layout_header--transitioning");
      
      setTimeout(() => {
        if (animationPhase === 1) {
          header.classList.remove("smd-layout_header--transitioning");
          header.classList.add("smd-layout_header--floating");
          animationPhase = 2;
          isFloating = true;
        }
      }, 250);
    }
  } else if (!shouldFloat && isFloating && scrollY <= anchorZone) {
    // Start un-floating transition
    if (animationPhase === 2) {
      animationPhase = 1;
      header.classList.remove("smd-layout_header--floating");
      header.classList.add("smd-layout_header--transitioning-back");
      
      setTimeout(() => {
        if (animationPhase === 1) {
          header.classList.remove("smd-layout_header--transitioning-back");
          animationPhase = 0;
          isFloating = false;
        }
      }, 350);
    }
  }

  // Handle snap to top
  if (scrollY === 0 && isFloating) {
    animationPhase = 1;
    header.classList.remove("smd-layout_header--floating");
    header.classList.add("smd-layout_header--snap-back");
    
    setTimeout(() => {
      header.classList.remove("smd-layout_header--snap-back");
      animationPhase = 0;
      isFloating = false;
    }, 350);
  }

  lastScrollY = scrollY;
  ticking = false;
}

function onScroll() {
  if (!ticking) {
    requestAnimationFrame(updateHeader);
    ticking = true;
  }
}

window.addEventListener("scroll", onScroll, { passive: true });

window.addEventListener(
  "resize",
  () => {
    const newIsMobile = window.innerWidth <= 768;
    if (newIsMobile !== isMobile) {
      // Reset animation state on resize
      animationPhase = 0;
      isFloating = false;
      header.classList.remove("smd-layout_header--floating", "smd-layout_header--transitioning", "smd-layout_header--transitioning-back", "smd-layout_header--snap-back");
      lastScrollY = -1;
      requestAnimationFrame(updateHeader);
    }
  },
  { passive: true }
);

updateHeader();
