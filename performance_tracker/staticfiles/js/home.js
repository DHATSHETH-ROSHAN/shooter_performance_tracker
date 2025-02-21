window.addEventListener("scroll", function () {
    let targetDiv = document.getElementById("wello"); // Replace with your div's ID
    let scrollPosition = window.scrollY; // Get vertical scroll position

    if (scroll) {
        targetDiv.style.opacity = "1";  
        targetDiv.style.transform = "translateY(0)";  
    } else {
        targetDiv.style.opacity = "0";
        targetDiv.style.transform = "translateY(20px)";  
    }
});
window.addEventListener("scroll", function () {
    let targetDiv = document.getElementById("features"); //
    let scrollPosition = window.scrollY; // Get vertical scroll position

    if (scroll) {
        targetDiv.style.opacity = "1";  
        targetDiv.style.transform = "translateX(0)";  
    } else {
        targetDiv.style.opacity = "0";
        targetDiv.style.transform = "translateX(100px)";  
    }
});