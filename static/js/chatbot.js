document.addEventListener('DOMContentLoaded', () => {
    const sendButton = document.getElementById('sendButton');
    const messageInput = document.getElementById('messageInput');
    const chatMessages = document.getElementById('chatMessages');

    function addMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.innerHTML = content;
        chatMessages.appendChild(messageDiv);

        // Handle large tables
        const tables = messageDiv.querySelectorAll('table.data-table');
        tables.forEach(table => {
            const tbody = table.querySelector('tbody');
            if (tbody) {
                const rows = tbody.querySelectorAll('tr');
                const totalRows = rows.length;
                let visibleRows = 5;
                if (totalRows > visibleRows) {
                    for (let i = visibleRows; i < totalRows; i++) {
                        rows[i].style.display = 'none';
                    }
                    const seeMoreButton = document.createElement('button');
                    seeMoreButton.textContent = 'See More';
                    seeMoreButton.className = 'see-more-button';
                    seeMoreButton.addEventListener('click', () => {
                        const nextBatch = visibleRows + 5;
                        for (let i = visibleRows; i < nextBatch && i < totalRows; i++) {
                            rows[i].style.display = '';
                        }
                        visibleRows = nextBatch;
                        if (visibleRows >= totalRows) {
                            seeMoreButton.remove();
                        }
                    });
                    table.parentNode.insertBefore(seeMoreButton, table.nextSibling);
                }
            }
        });

        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    sendButton.addEventListener('click', async () => {
        const message = messageInput.value.trim();
        if (!message) return;

        // Display user message
        addMessage(message, 'user');
        messageInput.value = '';

        // Send to backend and get response
        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: message })
            });
            const data = await response.json();
            addMessage(data.text, 'ai');
        } catch (error) {
            addMessage(`Error: ${error.message}`, 'ai');
        }
    });

    // Allow sending message with Enter key
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendButton.click();
        }
    });
});