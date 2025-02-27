function togglePassword() {
    let passwordField = document.getElementById("password");
    
    if (passwordField.type === "password") {
        passwordField.type = "text";
    } else {
        passwordField.type = "password";
    }
}

// Wait for the page to load
document.addEventListener("DOMContentLoaded", function () {
    // Select all alert messages
    let alerts = document.querySelectorAll(".alert");

    // Set timeout to remove alerts after 5 seconds (5000ms)
    alerts.forEach(function (alert) {
        setTimeout(function () {
            alert.style.transition = "opacity 0.5s";
            alert.style.opacity = "0"; // Fade out effect
            setTimeout(() => alert.remove(), 500); // Remove after fade-out
        }, 5000);
    });
});

