(function () {
    const loader = document.getElementById("page-loader");
    const loaderText = document.getElementById("loader-text");

    if (!loader) return;

    const delayTimer = setTimeout(() => {
        if (loaderText) loaderText.style.opacity = "1";
    }, 5000);

    window.addEventListener("load", () => {
        clearTimeout(delayTimer);

        if (loaderText) loaderText.style.opacity = "0";

        loader.style.opacity = "0";
        loader.style.transition = "opacity 0.3s ease";
        setTimeout(() => loader.remove(), 300);
    });
})();
