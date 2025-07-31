const header = document.querySelector(".smd-layout_header");
let ticking = false;
let lastScrollY = 0;
let isFloating = false;
const isMobile = window.innerWidth <= 768;
const threshold = isMobile ? 3 : 5;
const anchorZone = 1;

function updateHeader() {
  const scrollY = window.scrollY;

  if (scrollY === lastScrollY) {
    ticking = false;
    return;
  }

  const shouldFloat = scrollY > threshold;

  if (shouldFloat !== isFloating) {
    if (shouldFloat) {
      header.classList.add("smd-layout_header--floating");
      isFloating = true;
    } else if (scrollY <= anchorZone) {
      header.classList.remove("smd-layout_header--floating");
      isFloating = false;
    }
  }

  if (scrollY === 0 && isFloating) {
    setTimeout(() => {
      if (window.scrollY === 0) {
        header.classList.remove("smd-layout_header--floating");
        isFloating = false;
      }
    }, 50);
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
      lastScrollY = -1;
      requestAnimationFrame(updateHeader);
    }
  },
  { passive: true }
);

updateHeader();
