const toggleBtn = document.getElementById("chat-toggle");
const chatWidget = document.getElementById("chat-widget");
const closeBtn = document.getElementById("chat-close");
const typingIndicator = document.getElementById("typing-indicator");
const chatInput = document.getElementById("chat-input").querySelector("input");
const sendButton = document.getElementById("chat-input").querySelector("button");

// Event-Listener für das Öffnen/Schließen des Chat-Widgets
toggleBtn.addEventListener("click", () => {
    if (chatWidget.style.display === "none") {
        chatWidget.style.display = "flex";
        toggleBtn.style.display = "none";
        
        // Startnachrichten hinzufügen
        setTimeout(() => {
            addMessage("Es werden keine personenbezogenen Daten gespeichert.", "bot", "bot-red-message");
            setTimeout(() => {
                addMessage("Terminanfragen hier möglich.", "bot", "bot-green-message");
                setTimeout(() => {
                    addMessage("Wie kann ich Ihnen behilflich sein?", "bot");
                }, 500); 
            }, 500);
        }, 300);
    }
});

closeBtn.addEventListener("click", () => {
    chatWidget.style.display = "none";
    toggleBtn.style.display = "flex";
});

// Event-Listener für das Senden der Nachricht mit Enter
chatInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
        sendMessage();
    }
});

// Event-Listener für das Senden der Nachricht mit dem Button
sendButton.addEventListener("click", sendMessage);


// Funktion zum Hinzufügen einer Nachricht zum Chat-Fenster
function addMessage(htmlContent, sender, extraClass = null) {
    const chat = document.getElementById("chat-messages");
    const msgDiv = document.createElement("div");
    msgDiv.classList.add("message", sender);
    
    // Füge die zusätzliche Klasse hinzu, falls vorhanden
    if (extraClass) {
        msgDiv.classList.add(extraClass);
    }

    const avatar = document.createElement("div");
    avatar.classList.add("avatar");
    avatar.innerText = (sender === "user") ? "🧍" : "🤖"; 

    const bubble = document.createElement("div");
    bubble.classList.add("bubble"); 
    bubble.innerHTML = htmlContent;
    
    if (sender === "user") {
        msgDiv.appendChild(bubble);
        msgDiv.appendChild(avatar);
    } else {
        msgDiv.appendChild(avatar);
        msgDiv.appendChild(bubble);
    }
    
    chat.appendChild(msgDiv);
    // Scrolle zum neuesten Element
    chat.scrollTop = chat.scrollHeight;
}


// --- Wichtige Änderungen hier: sendMessage-Funktion verarbeitet die JSON-Antwort ---
async function sendMessage() {
    const userMessage = chatInput.value.trim();
    if (!userMessage) return;

    addMessage(userMessage, "user");
    chatInput.value = "";
    typingIndicator.style.display = "block";

    try {
        const response = await fetch("https://chatbot-app.vercel.app/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: userMessage }),
        });

        const data = await response.json();
        
        setTimeout(() => {
            // Überprüfe den "type"-Wert in der JSON-Antwort
            if (data.type === "calendar_slots") {
                let htmlContent = 'Bitte wählen Sie einen freien Termin: <br>';
                data.slots.forEach(slot => {
                    htmlContent += `<button class="slot-button" onclick="selectSlot('${slot.start}')">${slot.display}</button>`;
                });
                addMessage(htmlContent, 'bot');
            } else {
                addMessage(data.reply, "bot");
            }
            typingIndicator.style.display = "none";
        }, 500);
    } catch (error) {
        console.error("Fehler beim Senden der Nachricht:", error);
        addMessage("Entschuldigung, ich kann gerade nicht antworten.", "bot");
    } finally {
        typingIndicator.style.display = "none";
    }
}

// --- Neue Funktion zum Senden des ausgewählten Termins ---
async function selectSlot(isoDate) {
    addMessage(isoDate, "user"); 
    typingIndicator.style.display = "block";
    
    try {
        const response = await fetch("https://chatbot-app.vercel.app/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: isoDate }),
        });

        const data = await response.json();
        
        setTimeout(() => {
            addMessage(data.reply, "bot");
            typingIndicator.style.display = "none";
        }, 500);
    } catch (error) {
        console.error("Fehler beim Senden des Termins:", error);
        addMessage("Entschuldigung, ich kann diesen Termin gerade nicht buchen.", "bot");
    } finally {
        typingIndicator.style.display = "none";
    }
}
