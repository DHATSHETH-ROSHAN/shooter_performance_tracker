document.addEventListener("DOMContentLoaded", function () {
    console.log("DOM fully loaded!");

    const categorySelect = document.getElementById("category");
    const nameSelect = document.getElementById("name");

    if (!categorySelect || !nameSelect) {
        console.error("Dropdown elements not found! Check HTML.");
        return;
    }

    // Set initial options
    updateActivityNames();

    // Listen for changes in category selection
    categorySelect.addEventListener("change", function () {
        console.log("Category changed to:", categorySelect.value);  // Debugging log
        updateActivityNames();
    });
});

function updateActivityNames() {
    const categorySelect = document.getElementById("category");
    const nameSelect = document.getElementById("name");

    if (!categorySelect || !nameSelect) {
        console.error("Elements missing in updateActivityNames!");
        return;
    }

    console.log("Updating activity names for:", categorySelect.value);

    const activities = {
        technical: ["Scatt training", "Position Training", "Holding training", "Dry Firing"],
        physical: ["Endurance Training", "Core Strength", "Balance Training"],
        mental: ["Visualization", "Breathing Exercises", "Focus Drills", "Meditation"],
        equipment: ["Rifle Maintenance", "Rifle adjustments", "Kit Check"]
    };

    const selectedCategory = categorySelect.value;
    nameSelect.innerHTML = ""; // Clear previous options

    (activities[selectedCategory] || []).forEach(activity => {
        const option = document.createElement("option");
        option.value = activity;
        option.textContent = activity;
        nameSelect.appendChild(option);
    });

    console.log("Options updated:", nameSelect.innerHTML); // Debugging log
}
