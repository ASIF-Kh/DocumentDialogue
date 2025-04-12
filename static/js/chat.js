document.addEventListener('DOMContentLoaded', function() {
    const messageForm = document.getElementById('messageForm');
    const userMessageInput = document.getElementById('userMessage');
    const sendButton = document.getElementById('sendButton');
    const messageContainer = document.getElementById('messageContainer');
    const chatId = document.getElementById('chatId').value;
    
    // Initialize - scroll to bottom of chat
    scrollToBottom();
    
    // Handle message submission
    messageForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const messageText = userMessageInput.value.trim();
        if (!messageText) return;
        
        // Disable form during submission
        userMessageInput.disabled = true;
        sendButton.disabled = true;
        
        // Show message immediately
        addMessage(messageText, true);
        
        // Clear input
        userMessageInput.value = '';
        
        // Show typing indicator
        showTypingIndicator();
        
        // Send message to server
        sendMessage(messageText);
    });
    
    // Function to add a message to the chat UI
    function addMessage(content, isUser, timestamp = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
        
        // Format the content for bot messages (potential markdown)
        const formattedContent = isUser ? content : formatBotMessage(content);
        
        // Get current time if timestamp not provided
        const messageTime = timestamp || new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        messageDiv.innerHTML = `
            <div class="message-content">
                ${formattedContent}
            </div>
            <div class="message-time text-end">
                ${messageTime}
            </div>
        `;
        
        messageContainer.appendChild(messageDiv);
        scrollToBottom();
    }
    
    // Format bot message - handle markdown and code blocks
    function formatBotMessage(content) {
        try {
            // Convert markdown to HTML
            return marked.parse(content);
        } catch (error) {
            console.error('Error parsing markdown:', error);
            return content;
        }
    }
    
    // Show typing indicator
    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot-message';
        typingDiv.id = 'typingIndicator';
        
        typingDiv.innerHTML = `
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        
        messageContainer.appendChild(typingDiv);
        scrollToBottom();
    }
    
    // Remove typing indicator
    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    // Send message to the server
    function sendMessage(message) {
        fetch('/api/send_message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                chat_id: chatId
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Remove typing indicator
            removeTypingIndicator();
            
            // Add bot message with the response
            addMessage(data.bot_message.content, false, formatTimestamp(data.bot_message.timestamp));
            
            // Re-enable the form
            userMessageInput.disabled = false;
            sendButton.disabled = false;
            
            // Focus the input field
            userMessageInput.focus();
        })
        .catch(error => {
            console.error('Error:', error);
            
            // Remove typing indicator
            removeTypingIndicator();
            
            // Add error message
            addMessage('Sorry, there was an error processing your request. Please try again.', false);
            
            // Re-enable the form
            userMessageInput.disabled = false;
            sendButton.disabled = false;
        });
    }
    
    // Format ISO timestamp to local time
    function formatTimestamp(isoTimestamp) {
        return new Date(isoTimestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }
    
    // Scroll to the bottom of the message container
    function scrollToBottom() {
        messageContainer.scrollTop = messageContainer.scrollHeight;
    }
    
    // Auto-resize textarea as user types
    userMessageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight < 150 ? this.scrollHeight : 150) + 'px';
    });
    
    // Focus input on page load
    userMessageInput.focus();
});
