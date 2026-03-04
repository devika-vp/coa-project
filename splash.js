/* ===============================
   FADE IN EFFECT
================================ */

document.addEventListener("DOMContentLoaded", function () {
    document.body.style.opacity = "0";

    setTimeout(() => {
        document.body.style.transition = "opacity 1.5s ease";
        document.body.style.opacity = "1";
    }, 100);
});


/* ===============================
   LOADING TEXT DOT ANIMATION
================================ */

const loadingText = document.querySelector(".loading-text");

let dots = 0;

setInterval(() => {
    dots = (dots + 1) % 4;
    if (loadingText) {
        loadingText.textContent = "Initializing System" + ".".repeat(dots);
    }
}, 500);


/* ===============================
   FADE OUT + REDIRECT
================================ */

setTimeout(() => {
    document.body.style.transition = "opacity 1s ease";
    document.body.style.opacity = "0";

    setTimeout(() => {
        window.location.href = "/landing";
    }, 1000);

}, 3000);