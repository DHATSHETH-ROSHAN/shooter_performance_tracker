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


// Function to handle the chat window opening and message sending
document.querySelectorAll(".open-chat").forEach(button => {
    button.addEventListener("click", function() {
        const userId = this.getAttribute("data-user-id");
        const chatWindow = document.getElementById("chat-window");
        const conversationId = [userId, '{{ request.user.id }}'].sort().join('_');
        
        console.log('userid', userId);
        console.log('chatwindow', chatWindow);
        console.log('conversationid', conversationId)

        // Remove active class from all cards and add to current
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
        .then(data => {
            // Hide unread badge when messages are marked as read
            const unreadBadge = this.querySelector('.unread-badge');
            if (unreadBadge) {
                unreadBadge.style.display = 'none';
            }
        })
        .catch(error => console.error('Error marking messages as read:', error));
        
        // Load chat content
        fetch(`/message/chat/${userId}/`)
            .then(response => response.text())
            .then(data => {
                chatWindow.innerHTML = data;
                
                // Scroll to bottom of messages after loading chat
                const messagesDiv = document.getElementById('chat-messages');
                if (messagesDiv) {
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                }
                
                // Initialize WebSocket connection
                const chatSocket = new WebSocket(
                    'ws://' + window.location.host + '/ws/chat/' + conversationId + '/'
                );

                chatSocket.onopen = function(e) {
                    console.log('WebSocket connection established');
                };

                chatSocket.onmessage = function(e) {
                    console.log('Received message:', e.data);
                    const data = JSON.parse(e.data);
                    
                    // Get the messages container
                    const messagesDiv = document.getElementById('chat-messages');
                    if (!messagesDiv) {
                        console.error('Messages container not found');
                        return;
                    }

                    // Create new message element
                    const messageDiv = document.createElement('div');
                    messageDiv.className = data.sender === '{{ request.user.username }}' ? 'sent-message' : 'received-message';
                    
                    // Format the timestamp
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

                    // If this is a received message and chat is active, mark it as read
                    if (data.sender !== '{{ request.user.username }}' && this.classList.contains('active')) {
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
                    // Attempt to reconnect after a delay
                    setTimeout(() => {
                        console.log('Attempting to reconnect...');
                        const newSocket = new WebSocket(
                            'ws://' + window.location.host + '/ws/chat/' + conversationId + '/'
                        );
                        // Copy over the event handlers to the new socket
                        newSocket.onopen = chatSocket.onopen;
                        newSocket.onmessage = chatSocket.onmessage;
                        newSocket.onerror = chatSocket.onerror;
                        newSocket.onclose = chatSocket.onclose;
                        chatSocket = newSocket;
                    }, 3000);
                };

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
                        console.log('Sending message:', messageData);
                        chatSocket.send(JSON.stringify(messageData));
                        messageInput.value = '';
                    }
                }

                if (sendButton) {
                    sendButton.onclick = sendMessage;
                }

                if (messageInput) {
                    messageInput.onkeyup = function(e) {
                        if (e.keyCode === 13) {  // enter, return
                            sendMessage();
                        }
                    };
                }
            })
            .catch(error => console.error("Error loading chat:", error));
    });
});

// Keep track of active WebSocket connections
let activeWebSockets = {};

// Function to establish WebSocket connections for all chats
function connectAllChats() {
    document.querySelectorAll(".message-card").forEach(card => {
        const userId = card.getAttribute("data-user-id");
        if (!activeWebSockets[userId]) {
            const socket = new WebSocket(
                'ws://' + window.location.host + '/ws/chat/' + userId + '/'
            );

            socket.onmessage = function(e) {
                const data = JSON.parse(e.data);
                
                // Update unread badge for the conversation
                if (data.sender !== '{{ request.user.username }}') {
                    const conversationCard = document.querySelector(`.message-card[data-user-id="${userId}"]`);
                    if (conversationCard) {
                        // Only update badge if chat is not active
                        if (!conversationCard.classList.contains('active')) {
                            const unreadBadge = conversationCard.querySelector('.unread-badge');
                            if (unreadBadge) {
                                const currentCount = parseInt(unreadBadge.textContent) || 0;
                                unreadBadge.textContent = currentCount + 1;
                                unreadBadge.style.display = 'inline';
                            }
                        }

                        // If this chat is currently open, append the message
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
                            messagesDiv.scrollTop = messagesDiv.scrollHeight;
                        }
                    }
                }
            };

            socket.onerror = function(e) {
                console.error('WebSocket error:', e);
            };

            socket.onclose = function(e) {
                console.error('WebSocket connection closed:', e);
                delete activeWebSockets[userId];
                // Attempt to reconnect
                setTimeout(() => connectAllChats(), 3000);
            };

            activeWebSockets[userId] = socket;
        }
    });
}

// Connect to all chats when the page loads
document.addEventListener('DOMContentLoaded', connectAllChats);

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