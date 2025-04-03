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

function viewShooter(shooterid) {
    //maek ajax request call to fetch details
    fetch(`/home/get-shooter-details/${shooterid}/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById("shooterName").textContent = data.username;
            document.getElementById("shooterEmail").textContent = data.email;
            document.getElementById("shooterMobile").textContent = data.mobile;
            document.getElementById("shooterCategory").textContent = data.category;
            document.getElementById("shooterGender").textContent = data.gender;

            var modal = new bootstrap.Modal(document.getElementById("shooterDetailsModal"));
            modal.show();

        })
        .catch(error => console.error("Error Fetching shooter details:", error));
};

function viewCoach(coachid) {
    // make the ajax call request to collect the datas and display it 
    fetch(`/home/get-coach-details/${coachid}/`)
        .then(response =>response.json())
        .then(data => {
            document.getElementById("coachName").textContent = data.username;
            document.getElementById("coachEmail").textContent = data.email;
            document.getElementById("coachMobile").textContent = data.mobile;
            document.getElementById("coachExperience").textContent = data.experience;
            document.getElementById("coachSpecialization").textContent = data.Specialization;

            var modal = new bootstrap.Modal(document.getElementById("coachDetailsModal"));
            modal.show();
            
        })
        .catch(error => console.error("Error fetching the coach details:", error));

};


//end of chats