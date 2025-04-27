document.addEventListener("DOMContentLoaded", function () {
  const messageForm = document.getElementById("messageForm");
  const userMessageInput = document.getElementById("userMessage");
  const sendButton = document.getElementById("sendButton");
  const messageContainer = document.getElementById("messageContainer");
  const chatId = document.getElementById("chatId").value;

  let botMessageDiv = null; // To track the live updating bot message

  scrollToBottom();

  messageForm.addEventListener("submit", function (e) {
    e.preventDefault();

    const messageText = userMessageInput.value.trim();
    if (!messageText) return;

    userMessageInput.disabled = true;
    sendButton.disabled = true;

    // Add user message immediately
    addMessage(messageText, true);

    userMessageInput.value = "";

    showTypingIndicator();

    // Start streaming bot response
    streamMessage(messageText);
  });

  function addMessage(content, isUser, timestamp = null) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${isUser ? "user-message" : "bot-message"}`;

    const formattedContent = isUser ? content : formatBotMessage(content);

    const messageTime =
      timestamp ||
      new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    messageDiv.innerHTML = `
            <div class="message-content">${formattedContent}</div>
            <div class="message-time text-end">${messageTime}</div>
        `;

    messageContainer.appendChild(messageDiv);

    if (!isUser) {
      botMessageDiv = messageDiv.querySelector(".message-content"); // Save for live updating
    }

    scrollToBottom();
  }

  function updateBotMessageChunk(contentChunk) {
    if (botMessageDiv) {
      botMessageDiv.innerHTML += formatBotMessage(contentChunk);
      scrollToBottom();
    }
  }

  function showTypingIndicator() {
    const typingDiv = document.createElement("div");
    typingDiv.className = "message bot-message";
    typingDiv.id = "typingIndicator";

    typingDiv.innerHTML = `
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;

    messageContainer.appendChild(typingDiv);
    scrollToBottom();
  }

  function removeTypingIndicator() {
    const typingIndicator = document.getElementById("typingIndicator");
    if (typingIndicator) {
      typingIndicator.remove();
    }
  }

  function streamMessage(message) {
    fetch("/api/send_message", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: message,
        chat_id: chatId,
      }),
    })
      .then((response) => {
        if (!response.body) throw new Error("No response body for streaming.");

        removeTypingIndicator();
        addMessage("", false); // Create an empty bot message first

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        function read() {
          reader.read().then(({ done, value }) => {
            if (done) {
              userMessageInput.disabled = false;
              sendButton.disabled = false;
              userMessageInput.focus();
              return;
            }
            const chunk = decoder.decode(value, { stream: true });
            updateBotMessageChunk(chunk);
            read();
          });
        }
        read();
      })
      .catch((error) => {
        console.error("Streaming error:", error);
        removeTypingIndicator();
        addMessage(
          "Sorry, there was an error processing your request. Please try again.",
          false
        );
        userMessageInput.disabled = false;
        sendButton.disabled = false;
      });
  }

  function formatBotMessage(content) {
    try {
      return marked.parseInline(content); // Use parseInline for better chunking
    } catch (error) {
      console.error("Error parsing markdown:", error);
      return content;
    }
  }

  function scrollToBottom() {
    messageContainer.scrollTop = messageContainer.scrollHeight;
  }

  userMessageInput.addEventListener("input", function () {
    this.style.height = "auto";
    this.style.height =
      (this.scrollHeight < 150 ? this.scrollHeight : 150) + "px";
  });

  userMessageInput.focus();
});
