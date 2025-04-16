document.addEventListener("DOMContentLoaded", function () {

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
        updateActivityNames();
    });

    const viewButtons = document.querySelectorAll('.view-activity');
    viewButtons.forEach(btn => {
      btn.addEventListener('click', function () {
        const activityId = this.getAttribute('data-id');
    
        fetch(`/score/get-activity-modal/${activityId}/`)
          .then(response => response.json())
          .then(data => {
            // Set modal values
            document.getElementById('modal-date').textContent = data.date;
            document.getElementById('modal-name').textContent = data.name;
            document.getElementById('modal-category').textContent = data.category;
            document.getElementById('modal-duration').textContent = data.duration;
            document.getElementById('modal-notes').textContent = data.notes;
    
            // Show the modal
            const modal = new bootstrap.Modal(document.getElementById('activityModal'));
            modal.show();
          })
          .catch(error => {
            console.error('Error fetching modal:', error);
          });
      });
    });

});

function updateActivityNames() {
    const categorySelect = document.getElementById("category");
    const nameSelect = document.getElementById("name");

    if (!categorySelect || !nameSelect) {
        console.error("Elements missing in updateActivityNames!");
        return;
    }


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

}

