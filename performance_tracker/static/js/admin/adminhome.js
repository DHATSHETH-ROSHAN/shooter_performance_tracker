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
// Function to create and reconnect WebSocket
function setupChatSocket(conversationId, messageCardElement) {
    const currentUserId = document.body.getAttribute('data-user-id');
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const chatSocket = new WebSocket(`${protocol}://${window.location.host}/ws/chat/${conversationId}/`);
    

    chatSocket.onopen = () => console.log('WebSocket connected');

    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        const chatWindow = document.getElementById('chat-window');
        
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');

        if (data.sender_id == currentUserId) {
            messageDiv.classList.add('sent');
        } else {
            messageDiv.classList.add('received');
        }

        messageDiv.innerHTML = `<p>${data.message}</p>`;
        chatWindow.appendChild(messageDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    };

    chatSocket.onerror = e => console.error("WebSocket error:", e);

    chatSocket.onclose = function() {
        console.error("WebSocket closed");
        setTimeout(() => setupChatSocket(conversationId, messageCardElement), 3000);
    };

    return chatSocket;
}


//  Chat message card click listener
document.querySelectorAll(".open-chat").forEach(button => {
    button.addEventListener("click", function () {
        const userId = this.getAttribute("data-user-id");
        const profileId = this.getAttribute("data-profile-id");
        const chatWindow = document.getElementById("chat-window");
        const conversationId = [profileId ,userId].sort().join('_');

        // Remove active class from all cards
        document.querySelectorAll('.message-card').forEach(card => {
            card.classList.remove('active');
        });
        this.classList.add('active');

        // Mark messages as read
        fetch(`/message/messages/read/${conversationId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            }
        }).then(response => response.json())
          .then(() => {
              const unreadBadge = this.querySelector('.unread-badge');
              if (unreadBadge) unreadBadge.style.display = 'none';
          })
          .catch(error => console.error('Error marking messages as read:', error));

        // Load chat content
        fetch(`/message/chat/${userId}/`)
            .then(response => response.text())
            .then(data => {
                chatWindow.innerHTML = data;

                const messagesDiv = document.getElementById('chat-messages');
                if (messagesDiv) scrollChatToBottom();


                //  Initialize WebSocket
                const chatSocket = setupChatSocket(conversationId, this);

                //  Message sending logic
                const messageInput = document.querySelector('#chat-message-input');
                const sendButton = document.querySelector('#chat-message-send');

                function sendMessage() {
                    const message = messageInput.value.trim();

                    if (message && chatSocket.readyState === WebSocket.OPEN) {
                        chatSocket.send(JSON.stringify({
                            'message': message,
                            'sender_id': profileId,
                            'receiver_id': userId,
                            'conversation_id': conversationId
                        }));
                        messageInput.value = '';
                    }
                }

                if (sendButton) sendButton.onclick = sendMessage;

                if (messageInput) {
                    messageInput.onkeyup = function (e) {
                        if (e.keyCode === 13) sendMessage();
                    };
                }
            })
            .catch(error => console.error("Error loading chat:", error));
    });
});

//  Keep track of background sockets
let activeWebSockets = {};

//  Connect background sockets for unread badges
function connectAllChats() {
    document.querySelectorAll(".message-card").forEach(card => {
        const userId = card.getAttribute("data-user-id");
        if (!activeWebSockets[userId]) {

            const socket = new WebSocket('ws://' + window.location.host + '/ws/chat/' + userId + '/');

            socket.onmessage = function (e) {
                const data = JSON.parse(e.data);

                if (data.sender !== '{{ request.user.username }}') {
                    const conversationCard = document.querySelector(`.message-card[data-user-id="${userId}"]`);
                    if (conversationCard && !conversationCard.classList.contains('active')) {
                        const unreadBadge = conversationCard.querySelector('.unread-badge');
                        if (unreadBadge) {
                            const count = parseInt(unreadBadge.textContent) || 0;
                            unreadBadge.textContent = count + 1;
                            unreadBadge.style.display = 'inline';
                        }
                    }

                    // Show message if chat is open
                    const messagesDiv = document.getElementById('chat-messages');
                    if (messagesDiv && conversationCard.classList.contains('active')) {
                        const messageDiv = document.createElement('div');
                        messageDiv.className = 'received-message';

                        const timestamp = new Date(data.timestamp);
                        const formattedTime = timestamp.toLocaleTimeString('en-US', {
                            hour: '2-digit',
                            minute: '2-digit',
                            hour12: false
                        });

                        messageDiv.innerHTML = `
                            <p>${data.message}</p>
                            <small class="text-muted">${formattedTime}</small>
                        `;

                        messagesDiv.appendChild(messageDiv);
                        scrollChatToBottom();

                    }
                }
            };

            socket.onerror = e => console.error('WebSocket error:', e);

            socket.onclose = function () {
                console.error('WebSocket closed, reconnecting...');
                delete activeWebSockets[userId];
                setTimeout(() => connectAllChats(), 3000);
            };

            activeWebSockets[userId] = socket;
        }
    });
}

function scrollChatToBottom() {
    const messagesDiv = document.getElementById('chat-messages');
    if (messagesDiv) {
        // Ensure scroll after DOM has been updated
        setTimeout(() => {
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }, 50);
    }
}

// Connect background listeners on page load
document.addEventListener('DOMContentLoaded', connectAllChats);

// end of chats



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

function removeUserFromClub(userId, userType) {
    const confirmed = confirm(`Are you sure you want to remove this ${userType.toLowerCase()} from the club?`);

    if (confirmed) {
        fetch("/staff/remove-affiliation/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken(),
            },
            body: JSON.stringify({
                user_id: userId,
                user_type: userType // Should be either "Shooter" or "Coach"
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                location.reload(); // Django messages will appear after reload
            }
        });
    }
}



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
                            <button class="btn btn-outline-info add-shooter-btn" data-coach-id="${coachId}"><i class="bi bi-plus-lg"></i> Assign shooter's</button>       
                        </div>
                        <div class="container text-start text-light bg-dark p-3">
                            <p>Email: ${data.email}</p>
                            <p>Total Shooters: ${data.shooter_count}</p>
                            <ul class="list-group list-group-flush bg-dark">
                                ${data.shooters.map(shooter => `<li class="list-group-item bg-dark text-light d-flex justify-content-between align-items-center">
                                    ${shooter}
                                    <button class="btn btn-sm btn-danger remove-shooter-btn" data-shooter-username="${shooter}" data-coach-id="${coachId}">
                                    <i class="bi bi-trash3"></i> Remove
                                    </button>
                                    </li>`).join('')}
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

                    window.choicesInstance = new Choices(selectElement, {
                        removeItemButton: true,
                        placeholder: true,
                        placeholderValue: 'Select shooters...',
                        maxItemCount: 10,
                        searchResultLimit: 10,
                        renderChoiceLimit: 10
                    });

                    const modalElement = document.getElementById('addShooterModal');
                    const bootstrapModal = new bootstrap.Modal(modalElement);
                    bootstrapModal.show();

                });

                // logic for the remove shooter button

                setTimeout(() => {
                    document.querySelectorAll('.remove-shooter-btn').forEach(btn => {
                        btn.addEventListener('click', function() {
                            const coachId = this.getAttribute('data-coach-id');
                            const shooterUsername = this.getAttribute('data-shooter-username');

                            if (!confirm(`Are you sure you want to remove ${shooterUsername}?`)) return;

                            fetch(`/staff/remove-shooter/`, {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'X-CSRFToken': getcookie('csrftoken'),
                                },
                                body: JSON.stringify({
                                    coach_id: coachId,
                                    shooter_username: shooterUsername,
                                })
                            })
                            .then(response => response.json())
                            .then(data => {
                                if (data.Success) {
                                    alert('shooter removed successfully!');
                                    location.reload();
                                } else {
                                    alert('Error:' + data.error);
                                }
                            })
                            .catch(err => {
                                console.error(err)
                                alert('Error', + err.message);
                            });
                        });
                    });
                }, 100);
            });
        });
    });
});

// assign shooters to  the coaches 
document.getElementById('assign-shooters-btn').addEventListener('click', function () {
    const coachId = document.getElementById('modal-coach-id').value;
    const shooterIds = window.choicesInstance ? window.choicesInstance.getValue(true) : [];

    if (shooterIds.length === 0) {
        alert('please select at least one shooter!!');
        return;
    }

    fetch(`/staff/assign-shooters-to-coach/`, {
        method: 'POST',
        headers: {
            'content-Type': 'application/json',
            'X-CSRFToken': getcookie('csrftoken'),
        },
        body: JSON.stringify({
            coach_id: coachId,
            shooter_ids:shooterIds
            
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('shooters assigned successfully!');
            location.reload();
        } else {
            alert('Error:' + data.error);
        }
    })
    .catch(err => {
        console.error('Caught error:', err);
        alert('Error: ' + err.message);
    });

});

// helper function to get csrf token
function getcookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie != '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim()
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
};

// csrftoken helper
function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}


document.addEventListener('DOMContentLoaded', function () {
    let selectedShooterId = null;
    let selectedCoachId = null;
    
    // evento trigger when the card is clicked
    document.querySelectorAll('.shooter-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            const shooterId = this.getAttribute('data-shooter-id');
            fetch(`/staff/shooter-coach-relation/${shooterId}/`)
                .then(response => response.json())
                .then(data => {
                    const shooter = data.shooter;
                    const coach = data.coach;

                    document.getElementById('relation-display').innerHTML = `
                        <div class="card text-start text-light bg-dark p-3">
                            <h5 class="mb-2"><span class="tb-head">Shooter:</span> ${shooter.username}</h5>
                            <p>Email: ${shooter.email}</p>
                            <p>Category: ${shooter.category}</p>
                            ${
                                coach
                                ? `<p class="d-flex align-items-center justify-content-between">
                                    <span><strong class="tb-head">Coach:</strong> ${coach.username}</span>
                                    <button class="btn btn-sm btn-danger unassign-coach-btn ms-3"
                                            data-coach-id="${coach.id}"
                                            data-shooter-id="${shooter.id}"
                                            data-shooter-username="${shooter.username}">
                                        <i class="bi bi-eraser"></i> Unassign coach
                                    </button>
                                </p>`
                                : `<p class="d-flex align-items-center justify-content-between">
                                    <span style="color: gray;">Coach not assigned</span>
                                    <button class="btn btn-sm btn-primary assign-select-btn ms-3"
                                            data-shooter-id="${shooter.id}">
                                        <i class="bi bi-plus-lg"></i> Assign Coach
                                    </button>
                                </p>`
                            }
                        </div>
                    `;
                });
        });
    });

    //  dynamically created 'Assign Coach' buttons
    document.addEventListener('click', function (e) {
        if (e.target.classList.contains('assign-select-btn')) {
            selectedShooterId = e.target.getAttribute('data-shooter-id');

            fetch('/staff/available-coaches/')
                .then(response => response.json())
                .then(data => {
                    const select = document.getElementById('coachSelect');
                    select.innerHTML = `<option value="">Select a coach</option>`; // reset options

                    data.coaches.forEach(coach => {
                        const option = document.createElement('option');
                        option.value = coach.id;
                        option.textContent = coach.username;
                        select.appendChild(option);
                    });

                    // Show modal
                    const assignModal = new bootstrap.Modal(document.getElementById('assignCoachModal'));
                    assignModal.show();
                });
        }
    });

    // Enable the assign button only when a coach is selected
    document.getElementById('coachSelect').addEventListener('change', function () {
        const assignBtn = document.getElementById('assignCoachBtn');
        assignBtn.disabled = !this.value;
    });

    // Assign coach - this handler is added **only once**
    document.getElementById('assignCoachBtn').addEventListener('click', function () {
        const coachId = document.getElementById('coachSelect').value;

        fetch(`/staff/assign-coach/${coachId}/${selectedShooterId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(data.warning || 'Coach assigned successfully!');
                location.reload();
            } else {
                alert('Failed: ' + data.error);
            }
        });
    });

        // Handle click on "Unassign Coach" button: Show confirm modal
        document.addEventListener('click', function(e) {
            if (e.target && e.target.classList.contains('unassign-coach-btn')) {
                const coachId = e.target.getAttribute('data-coach-id');
                const shooterId = e.target.getAttribute('data-shooter-id');
        
                // Save these values to the modal's confirm button
                const modalBtn = document.querySelector('#unassignCoachModal .confirm-unassign-btn');
                modalBtn.setAttribute('data-coach-id', coachId);
                modalBtn.setAttribute('data-shooter-id', shooterId);
        
                // Then open the modal
                const modal = new bootstrap.Modal(document.getElementById('unassignCoachModal'));
                modal.show();
            }
        });

        // Confirm Unassign: Make POST request
        document.querySelector('.confirm-unassign-btn').addEventListener('click', function() {
            const coachId = this.getAttribute('data-coach-id');
            const shooterId = this.getAttribute('data-shooter-id');
        
            fetch(`/staff/unassign-coach/${coachId}/${shooterId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken(),
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Coach unassigned successfully.');
                    location.reload();
                    // Optionally reload or update relation-display
                } else {
                    alert(data.error || 'Unassign failed.');
                }
            });
        });

    // CSRF token helper
    function getCSRFToken() {
        const name = 'csrftoken';
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            if (cookie.trim().startsWith(name + '=')) {
                return decodeURIComponent(cookie.trim().substring(name.length + 1));
            }
        }
        return '';
    }
});

//end of chats
