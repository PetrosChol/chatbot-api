document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    let sessionId = localStorage.getItem('chatSessionId');

    function addMessage(message, sender) {
        const messageContainerDiv = document.createElement('div');
        messageContainerDiv.classList.add('message', sender === 'user' ? 'user-message' : 'bot-message');
        
        const messageContentDiv = document.createElement('div');
        messageContentDiv.innerHTML = marked.parse(message); 
        
        messageContainerDiv.appendChild(messageContentDiv);
        chatMessages.appendChild(messageContainerDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

    }

    function showTypingIndicator() {
        if (document.getElementById('typing-indicator')) return;

        const typingContainerDiv = document.createElement('div');
        typingContainerDiv.classList.add('message', 'bot-message', 'loading-dots');
        typingContainerDiv.id = 'typing-indicator';
        
        const innerDiv = document.createElement('div');
        innerDiv.innerHTML = '<span></span><span></span><span></span>';
        typingContainerDiv.appendChild(innerDiv);
        
        chatMessages.appendChild(typingContainerDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    async function sendMessage() {
        const messageText = userInput.value.trim();
        if (messageText === '') return;

        addMessage(messageText, 'user'); 
        userInput.value = '';
        userInput.focus();
        showTypingIndicator();

        try {
            const requestBody = {
                user_message: messageText, // Send raw Markdown to backend
            };
            if (sessionId) {
                requestBody.session_id = sessionId;
            }

            const response = await fetch('/api/v1/chat', { 
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody),
            });

            removeTypingIndicator();

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Σφάλμα δικτύου ή μη έγκυρο JSON.' }));
                const errorMessage = errorData.detail || `Σφάλμα: ${response.status} ${response.statusText}`;
                addMessage(`**Σφάλμα:** Επικοινωνίας με τον server: ${errorMessage}`, 'bot');
                console.error('Server error:', errorData);
                return;
            }

            const data = await response.json();
            addMessage(data.bot_reply, 'bot'); 
            
            if (data.session_id) {
                sessionId = data.session_id;
                localStorage.setItem('chatSessionId', sessionId);
            }

        } catch (error) {
            removeTypingIndicator();
            addMessage('**Παρουσιάστηκε σφάλμα** κατά την αποστολή του μηνύματος. Παρακαλώ δοκιμάστε ξανά.', 'bot');
            console.error('Fetch error:', error);
        }
    }

    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) { // Send on Enter, allow Shift+Enter for newline
            event.preventDefault(); 
            sendMessage();
        }
    });

    // Initial greeting message from Alex
    addMessage("Χαίρεται! Είμαι ο **Alex**, ο βοηθός σας για το *ThessalonikiGuide.gr*. Πώς μπορώ να σε βοηθήσω σήμερα;", "bot");

    userInput.focus();
});