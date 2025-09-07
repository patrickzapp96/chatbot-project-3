const toggleBtn = document.getElementById("chat-toggle");
const chatWidget = document.getElementById("chat-widget");
const closeBtn = document.getElementById("chat-close");
const typingIndicator = document.getElementById("typing-indicator");
const chatInputContainer = document.getElementById("chat-input");
const chatInput = document.getElementById("userMessage");

// NEUE ELEMENTE
const appointmentInputContainer = document.getElementById("appointment-input");
const dateInput = document.getElementById("date-input");
const timeInput = document.getElementById("time-input");
const sendAppointmentBtn = document.getElementById("send-appointment-btn");

let currentBotState = "initial"; // Variable, um den aktuellen Status zu speichern

toggleBtn.addEventListener("click", () => {
    if (chatWidget.style.display === "none") {
        chatWidget.style.display = "flex";
        toggleBtn.style.display = "none";
        
        setTimeout(() => {
            addMessage("Es werden keine personenbezogenen Daten gespeichert.", "bot");
            setTimeout(() => {
                addMessage("Terminanfragen hier möglich.", "bot");
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
    currentBotState = "initial"; // Zustand zurücksetzen
    // Alle Eingabeelemente ausblenden und Standard-Input anzeigen
    chatInputContainer.style.display = "flex";
    appointmentInputContainer.style.display = "none";
});

// Event-Listener für das normale Textfeld
chatInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
        sendMessage();
    }
});

// NEUER Event-Listener für den Senden-Button des Terminformulars
sendAppointmentBtn.addEventListener("click", () => {
    const date = dateInput.value;
    const time = timeInput.value;
    // Führe eine grundlegende Validierung durch
    if (date && time) {
        // Formatiere die Nachricht, um sie an den Bot zu senden
        const message = `${date} um ${time} Uhr`;
        sendMessage(message);
        // Blende die Formularfelder aus und zeige das normale Eingabefeld wieder an
        appointmentInputContainer.style.display = "none";
        chatInputContainer.style.display = "flex";
    } else {
        addMessage("Bitte geben Sie sowohl ein Datum als auch eine Uhrzeit ein.", "bot");
    }
});

async function sendMessage(messageOverride = null) {
    const msg = messageOverride || chatInput.value.trim();
    if (!msg) return;

    // Nur das normale Textfeld leeren
    if (!messageOverride) {
        chatInput.value = "";
    }
    
    addMessage(msg, "user");
    typingIndicator.style.display = "block";
    
    try {
        const res = await fetch("http://127.0.0.1:5000/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: msg, state: currentBotState })
        });

        if (!res.ok) {
            throw new Error(`Serverantwort war nicht okay: ${res.status}`);
        }

        const data = await res.json();
        // Aktualisiere den Zustand basierend auf der Antwort des Bots
        currentBotState = data.new_state; // Backend muss den neuen Zustand zurückgeben

        setTimeout(() => {
            addMessage(data.reply, "bot");
            typingIndicator.style.display = "none";

            // Überprüfe, ob der Bot jetzt Datum und Uhrzeit benötigt
            if (data.reply.includes("Datum und Uhrzeit")) {
                 chatInputContainer.style.display = "none";
                 appointmentInputContainer.style.display = "flex";
            } else {
                 chatInputContainer.style.display = "flex";
                 appointmentInputContainer.style.display = "none";
            }

        }, 500);
    } catch (error) {
        console.error("Fehler beim Senden der Nachricht:", error);
        addMessage("Entschuldigung, ich kann gerade nicht antworten.", "bot");
    } finally {
        typingIndicator.style.display = "none";
    }
}

function addMessage(text, sender) {
    const chat = document.getElementById("chat-messages");
    const msgDiv = document.createElement("div");
    msgDiv.classList.add("message", sender);

    const avatar = document.createElement("div");
    avatar.classList.add("avatar");

    if (sender === "user") {
        avatar.innerText = "🧍"; 
    } else {
        avatar.innerText = "🤖"; 
    }

    const bubble = document.createElement("div");
    bubble.innerText = text;

    if (sender === "user") {
        msgDiv.appendChild(bubble);
        msgDiv.appendChild(avatar);
    } else {
        msgDiv.appendChild(avatar);
        msgDiv.appendChild(bubble);
    }
    
    chat.appendChild(msgDiv);
    chat.scrollTop = chat.scrollHeight; // Scrollt automatisch nach unten
}
