// side bar activating the main content
document.addEventListener("DOMContentLoaded", function() {
    function showOnly(elementId, clickedbtn) {
        let containers = [
            'users-container',
            'coach-relation-container',
            'notification-container',
            'profile-container',
            'settings-container'
        ];

        let buttons = document.querySelectorAll('.custom-btn');

        containers.forEach(id => {
            document.getElementById(id).style.display = 'none';
        });

        buttons.forEach(btn => btn.classList.remove('active'));

        document.getElementById(elementId).style.display = 'block';
        clickedbtn.classList.add('active');
    }

    let defaultBtn = document.getElementById('users-btn');

    showOnly('users-container', defaultBtn);

    document.getElementById('users-btn').addEventListener('click', function() {
        showOnly('users-container', this);
    });

    document.getElementById('coach-relation-btn').addEventListener('click', function() {
        showOnly('coach-relation-container', this);
    });

    document.getElementById('notifications-btn').addEventListener('click', function() {
        showOnly('notification-container', this)
    });
    document.getElementById('profile-btn').addEventListener('click', function() {
        showOnly('profile-container', this)
    });
    document.getElementById('settings-btn').addEventListener('click', function() {
        showOnly('settings-container', this)
    });

});

// shrink buttons workings
document.addEventListener("DOMContentLoaded", function() {
    const sidebar = document.getElementById("sidebar");
    const mainContent = document.getElementById("main-content");
    const shrinkButton = document.getElementById("shrink-btn");

    shrinkButton.addEventListener('click', function () {
        sidebar.classList.toggle("collapsed");
        mainContent.classList.toggle("expanded");
    });
});

function showDetails(id) {
    var element = document.getElementById(id);
    if (element.style.display === "none" || element.style.display === "") {
        element.style.display = "block";
    } else {
        element.style.display = "none";
    }
};

function closeFunction(id) {
    document.getElementById(id).style.display = "none";
};


// for the chats only
document.querySelectorAll(".open-chat").forEach(button => {
    button.addEventListener("click", function() {
        const userId = this.getAttribute("data-user-id");
        const chatWindow = document.getElementById("chat-window");
        const conversationId = [userId, '{{ profile_id }}'].sort().join('_');

        // Remove active class from all message cards and add to the current one
        document.querySelectorAll('.message-card').forEach(card => {
            card.classList.remove('active');
        });
        this.classList.add('active');

        // Mark messages as read in backend
        fetch(`/message/messages/read/${conversationId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            }
        })
        .then(response => response.json())
        .then(() => {
            // Hide unread badge
            const unreadBadge = this.querySelector('.unread-badge');
            if (unreadBadge) unreadBadge.style.display = 'none';
        })
        .catch(error => console.error('Error marking messages as read:', error));

        // Load chat content
        fetch(`/message/chat/${userId}/`)
            .then(response => response.text())
            .then(data => {
                chatWindow.innerHTML = data;

                // Scroll to the bottom of messages
                const messagesDiv = document.getElementById('chat-messages');
                if (messagesDiv) messagesDiv.scrollTop = messagesDiv.scrollHeight;

                // Initialize WebSocket connection
                connectChatSocket(userId, conversationId);
            })
            .catch(error => console.error("Error loading chat:", error));
    });
});

// Track active WebSocket connections
let activeWebSockets = {};

function connectChatSocket(userId, conversationId) {
    // Close existing WebSocket for this user (if any) before reconnecting
    if (activeWebSockets[userId]) {
        activeWebSockets[userId].close();
    }

    // Create a new WebSocket connection
    const chatSocket = new WebSocket(
        (window.location.protocol === "https:" ? "wss://" : "ws://") + window.location.host + "/ws/chat/" + conversationId + "/"
    );

    chatSocket.onopen = function() {
        console.log('WebSocket connection established');
    };

    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        
        // Get chat messages container
        const messagesDiv = document.getElementById('chat-messages');
        if (!messagesDiv) return;

        // Create a new message element
        const messageDiv = document.createElement('div');
        messageDiv.className = data.sender === '{{ request.user.username }}' ? 'sent-message' : 'received-message';

        // Format timestamp
        const timestamp = new Date(data.timestamp);
        const formattedTime = timestamp.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit',
            hour12: false 
        });

        // Set message content
        messageDiv.innerHTML = `
            <p>${data.message}</p>
            <small class="text-muted">${formattedTime}</small>
        `;

        // Append message and scroll to bottom
        messagesDiv.appendChild(messageDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;

        // Mark message as read if chat is active
        const activeChat = document.querySelector('.message-card.active');
        if (data.sender !== '{{ request.user.username }}' && activeChat?.getAttribute("data-user-id") === userId) {
            fetch(`/message/messages/read/${conversationId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                }
            }).catch(error => console.error('Error marking message as read:', error));
        }
    };

    chatSocket.onerror = function(e) {
        console.error('WebSocket error:', e);
    };

    chatSocket.onclose = function(e) {
        console.error('WebSocket connection closed:', e);
        delete activeWebSockets[userId];  // Remove the reference
        
        // Attempt to reconnect after a delay
        setTimeout(() => {
            console.log('Attempting to reconnect...');
            connectChatSocket(userId, conversationId);
        }, 3000);
    };

    activeWebSockets[userId] = chatSocket;  // Store the active WebSocket connection

    // Set up message sending
    const messageInput = document.querySelector('#chat-message-input');
    const sendButton = document.querySelector('#chat-message-send');

    function sendMessage() {
        const message = messageInput.value.trim();
        if (message && chatSocket.readyState === WebSocket.OPEN) {
            const messageData = {
                'message': message,
                'sender_id': '{{ request.user.id }}',
                'receiver_id': userId,
                'conversation_id': conversationId
            };
            chatSocket.send(JSON.stringify(messageData));
            messageInput.value = '';  // Clear input field
        }
    }

    if (sendButton) sendButton.onclick = sendMessage;
    if (messageInput) {
        messageInput.onkeyup = function(e) {
            if (e.keyCode === 13) {  // Enter key
                sendMessage();
            }
        };
    }
};

function viewShooter(shooter_id) {
    //maek ajax request call to fetch details
    fetch(`/staff/get-shooter-details/${shooter_id}/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById("shooterName").textContent = data.username;
            document.getElementById("shooterEmail").textContent = data.email;
            document.getElementById("shooterMobile").textContent = data.mobile;
            document.getElementById("shooterCategory").textContent = data.category;
            document.getElementById("shooterGender").textContent = data.gender;
            document.getElementById("coach_name").textContent = data.coach_name;

            // Show Shooter Details Div
            document.getElementById("shooterDetailsContainer").style.display = "block";
            document.getElementById("shooterdetails").style.display = "none";

            // Hide Coach Details if it's open
            document.getElementById("coachDetailsContainer").style.display = "none";

            let manualScoresHTML = "";
            data.manual_scores.forEach((score, index) => {
                manualScoresHTML += `
                <tr>
                    <td>${index + 1}</td>
                    <td>${score.date}</td>
                    <td>${score.match_type}</td>
                    <td>${score.s1t || "-"}</td>
                    <td>${score.s2t || "-"}</td>
                    <td>${score.s3t || "-"}</td>
                    <td>${score.s4t || "-"}</td>
                    <td>${score.s5t || "-"}</td>
                    <td>${score.s6t || "-"}</td>
                    <td>${score.total}</td>
                    <td>${score.average}</td>
                    <td>${score.duration}</td>
                </tr>
                `;
            });
            document.getElementById("shotersManualScoreTable").innerHTML = manualScoresHTML;

            let estScoresHTML = "";
            data.est_scores.forEach((score, index) => {
                estScoresHTML += `
                <tr>
                    <td>${index + 1}</td>
                    <td>${score.date}</td>
                    <td>${score.match_type}</td>
                    <td>${score.s1t || "-"}</td>
                    <td>${score.s2t || "-"}</td>
                    <td>${score.s3t || "-"}</td>
                    <td>${score.s4t || "-"}</td>
                    <td>${score.s5t || "-"}</td>
                    <td>${score.s6t || "-"}</td>
                    <td>${score.total}</td>
                    <td>${score.average_shot_score}</td>
                    <td>${score.duration}</td>
                </tr>
                `;
            });
            document.getElementById("shotersEstScoreTable").innerHTML = estScoresHTML;

        })
        .catch(error => console.error("Error Fetching shooter details:", error));
        
}

function viewCoach(coach_id) {
    // make the ajax call request to collect the datas and display it 
    fetch(`/staff/get-coach-details/${coach_id}/`)
        .then(response =>response.json())
        .then(data => {
            document.getElementById("coachName").textContent = data.username;
            document.getElementById("coachEmail").textContent = data.email;
            document.getElementById("coachMobile").textContent = data.mobile;
            document.getElementById("coachGender").textContent = data.gender;
            document.getElementById("coachExperience").textContent = data.experience;
            document.getElementById("coachSpecialization").textContent = data.specialization;

            document.getElementById("shooters_count").textContent = data.shooters_count;
            document.getElementById("male_shooters_count").textContent = data.male_shooters_count;
            document.getElementById("female_shooters_count").textContent = data.female_shooters_count;

            
            let shooterTableHTML = "";

            data.shooter_details.forEach((shooter, index) => {
                shooterTableHTML += `
                <tr>
                    <td>${index + 1}</td>
                    <td>${shooter.username}</td>
                    <td>${shooter.category || "N/A"}</td>
                    <td>${shooter.date_of_birth || "N/A"}</td>
                    <td>${shooter.mobile_number}</td>
                    <td>${shooter.gender}</td>
                </tr>
                `;
            });
            document.getElementById("shooterTableBody").innerHTML = shooterTableHTML;

            // Show Coach Details Div
            document.getElementById("coachDetailsContainer").style.display = "block";
            document.getElementById("coachDetails").style.display="none";

            // Hide Shooter Details if it's open
            document.getElementById("shooterDetailsContainer").style.display = "none";
            
        })
        .catch(error => console.error("Error fetching the coach details:", error));

};

function closeFunctionS_C_cont(id1, id2) {
    document.getElementById(id1).style.display = "none";
    document.getElementById(id2).style.display = "block";
};

// add new shooter 
const passwordInput = document.getElementById('password1');
const passwordRequirements = document.getElementById('password-requirements');

passwordInput.addEventListener('input', function() {
    const password = passwordInput.value;
    const isValid = password.length >= 8 && 
                    /[a-z]/.test(password) && 
                    /[A-Z]/.test(password) && 
                    /\d/.test(password) && 
                    /[!#$%^&*>?]/.test(password);
    setTimeout(() => {
        passwordRequirements.style.display = 'none';
    }, 5000);
    passwordRequirements.style.display = isValid ? 'none' : 'block';
});
document.addEventListener("DOMContentLoaded", function() {
const firstnameInput = document.getElementById("first_name");
const lastnameInput = document.getElementById("last_name");
const firstLastRequirements = document.getElementById("first_last-requirements");
let firstLastTimeout;
// first name and last name validation
function validateAlphabetInput(event) {
    const input = event.target;
    const regex = /^[A-Za-z]+$/; // Allow alphabets only

    if (!regex.test(input.value)) {
        input.value = input.value.replace(/[^A-Za-z]/g, ''); // Remove all non-alphabetic characters
        firstLastRequirements.style.display = "block"; // Show message

        clearTimeout(firstLastTimeout); // Clear existing timeout if any
        firstLastTimeout = setTimeout(() => {
            firstLastRequirements.style.display = "none"; // Hide message after 5 seconds
        }, 5000);
    } else {
        firstLastRequirements.style.display = "none";
    }
}

firstnameInput.addEventListener("input", validateAlphabetInput);
lastnameInput.addEventListener("input", validateAlphabetInput);
});

document.addEventListener("DOMContentLoaded", function() {
const usernameInput = document.getElementById("username");
let usernameTimeout;

usernameInput.addEventListener("input", function() {
    const regex = /^[a-zA-Z0-9_@]+$/; // Allow letters, numbers, _ and @
    if (!regex.test(usernameInput.value)) {
        usernameInput.value = usernameInput.value.replace(/[^a-zA-Z0-9_@]/g, ''); // Remove unwanted characters

        clearTimeout(usernameTimeout); // Clear existing timeout if any
        usernameTimeout = setTimeout(() => {
            usernameInput.style.borderColor = ""; // Reset border color after 5 seconds
        }, 5000);

        usernameInput.style.borderColor = "red"; // Temporarily highlight input
    } else {
        usernameInput.style.borderColor = ""; // Reset immediately if valid
    }
});
});

document.addEventListener("DOMContentLoaded", function () {
const emailInput = document.getElementById("email");
const emailRequirements = document.getElementById("email-requirements");
let emailTimeout;

function validateEmail() {
    const emailPattern = /^[a-zA-Z0-9][a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/; 
    // Ensures email starts with a letter/number and follows proper structure

    if (!emailPattern.test(emailInput.value)) {
        emailInput.style.borderColor = "red"; // Highlight input in red
        emailRequirements.style.display = "block"; // Show message

        clearTimeout(emailTimeout); // Clear existing timeout
        emailTimeout = setTimeout(() => {
            emailRequirements.style.display = "none"; // Hide message after 5 seconds
            emailInput.style.borderColor = ""; // Reset border color
        }, 5000);
    } else {
        emailInput.style.borderColor = ""; // Reset border color
        emailRequirements.style.display = "none"; // Hide error message
    }
}

emailInput.addEventListener("input", validateEmail);
});

document.addEventListener("DOMContentLoaded", function () {
const mobileInput = document.getElementById("mobile");
const mobileRequirements = document.getElementById("mobile-requirements");
let mobileTimeout;

mobileInput.addEventListener("input", function () {
    const regex = /^[0-9]*$/; // Allow only numbers
    if (!regex.test(mobileInput.value)) {
        mobileInput.value = mobileInput.value.replace(/[^0-9]/g, ''); // Remove non-numeric characters
    }

    if (mobileInput.value.length !== 10) {
        mobileRequirements.style.display = "block"; // Show message
        clearTimeout(mobileTimeout); // Clear existing timeout
        mobileTimeout = setTimeout(() => {
            mobileRequirements.style.display = "none"; // Hide message after 5 seconds
        }, 5000);
    } else {
        mobileRequirements.style.display = "none"; // Hide message if valid
    }
});
});

// coach relation & remove coach or shoter
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.coach-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            const coachId = this.getAttribute('data-coach-id');
            fetch(`/staff/coach-shooter-relation/${coachId}/`)
                .then(response => response.json())
                .then(data => {
                    document.getElementById('relation-display').innerHTML = `
                    <div class="container text-start text-light bg-dark p-3" style="border-radius: 10px;">
                        <div class="d-flex justify-content-between align-items-center">
                            <h4 class="mb-2 tb-head" >Coach: ${data.name}</h4>
                            <button class="btn btn-outline-info add-shooter-btn" data-coach-id="${coachId}">Assign shooter's </button>       
                        </div>
                        <div class="container text-start text-light bg-dark p-3">
                            <p>Email: ${data.email}</p>
                            <p>Total Shooters: ${data.shooter_count}</p>
                            <ul class="list-group list-group-flush bg-dark">
                                ${data.shooters.map(shooter => `<li class="list-group-item bg-dark text-light">${shooter}</li>`).join('')}
                            </ul>
                        </div>
                    </div>
                `;
                document.querySelector('.add-shooter-btn').addEventListener('click', function () {
                    const coach_id = this.getAttribute('data-coach-id');
                    document.getElementById('modal-coach-id').value = coach_id;

                    const selectElement = document.getElementById('available-shooters-select');
                    selectElement.innerHTML='';

                    if (data.available_shooters.length === 0) {
                        const option = document.createElement('option');
                        option.textContent = 'No shooters available';
                        option.disabled = true;
                        selectElement.appendChild(option);
                    } else {
                        data.available_shooters.forEach(shooter => {
                            const option = document.createElement('option');
                            option.value = shooter[0];  // shooterid
                            option.textContent = shooter[1]; // username
                            selectElement.appendChild(option);
                        });
                    }

                    const choices = new Choices(selectElement, {
                        removeItemButton: true,
                        placeholder: true,
                        placeeholderValue: 'Select shooters...',
                        maxItemCoun: 10,
                        searchResultLismit: 10,
                        renderChoiceLimit: 10
                    });

                    const modalElement = document.getElementById('addShooterModal');
                    const bootstrapModal = new bootstrap.Modal(modalElement);
                    bootstrapModal.show();

                });
            });
        });
    });
});

// relation shooter and coach
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.shooter-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            const shooterId = this.getAttribute('data-shooter-id');
            fetch(`/staff/shooter-coach-relation/${shooterId}/`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('relation-display').innerHTML = `
                    <div class="card text-start text-light bg-dark p-3">
                        <h5 class="mb-2">Shooter: ${data.name}</h5>
                        <p>Email: ${data.email}</p>
                        <p>Category: ${data.category}</p>
                    </div>
                `;
            });
        });
    });
});
//end of chats