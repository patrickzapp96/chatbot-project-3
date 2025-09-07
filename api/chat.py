from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import smtplib
from email.message import EmailMessage
import re # Importiere das re-Modul für reguläre Ausdrücke

app = Flask(__name__)
CORS(app)

# Globale Variable zur Speicherung des Konversationsstatus
user_states = {}

# FAQ-Datenbank
faq_db = {
    "fragen": [
        # Deine vorhandenen FAQ-Einträge...
        {"keywords": ["öffnungszeiten", "wann geöffnet", "wann offen", "arbeitszeit"], "antwort": "Wir sind Montag–Freitag von 9:00 bis 18:00 Uhr und Samstag von 9:00 bis 14:00 Uhr für Sie da. Sonntag ist Ruhetag."},
        {"keywords": ["termin", "vereinbaren", "buchen", "reservieren", "online"], "antwort": "Wenn Sie einen Termin vereinbaren möchten, geben Sie bitte zuerst Ihren vollständigen Namen ein."},
        {"keywords": ["adresse", "wo", "anschrift", "finden", "lage"], "antwort": "Unsere Adresse lautet: Musterstraße 12, 10115 Berlin. Wir sind zentral und gut erreichbar."},
        {"keywords": ["preise", "kosten", "gebühren", "haarschnitt"], "antwort": "Ein Damenhaarschnitt kostet ab 25 €, Herrenhaarschnitt ab 20 €. Färben ab 45 €. Die komplette Preisliste finden Sie im Salon."},
        {"keywords": ["zahlung", "karte", "bar", "visa", "mastercard", "paypal", "kartenzahlung", "kontaktlos", "bezahlen"], "antwort": "Sie können bar, mit EC-Karte, Kreditkarte (Visa/Mastercard) und sogar kontaktlos per Handy bezahlen."},
        {"keywords": ["parkplatz", "parken", "auto", "stellplatz"], "antwort": "Vor unserem Salon befinden sich kostenlose Parkplätze. Alternativ erreichen Sie uns auch gut mit den öffentlichen Verkehrsmitteln."},
        {"keywords": ["waschen", "föhnen", "styling", "legen"], "antwort": "Natürlich – wir bieten Waschen, Föhnen und individuelles Styling an. Perfekt auch für Events oder Fotoshootings."},
        {"keywords": ["färben", "farbe", "farben", "strähnen", "blondieren", "haartönung"], "antwort": "Wir färben und tönen Haare in allen Farben, inklusive Strähnen, Balayage und Blondierungen. Unsere Stylisten beraten Sie individuell."},
        {"keywords": ["dauerwelle", "dauerwellen", "locken", "lockenfrisur"], "antwort": "Ja, wir bieten auch Dauerwellen und Locken-Stylings an."},
        {"keywords": ["hochzeit", "brautfrisur", "brautfrisuren", "hochsteckfrisur"], "antwort": "Wir stylen wunderschöne Braut- und Hochsteckfrisuren. Am besten buchen Sie hierfür rechtzeitig einen Probetermin."},
        {"keywords": ["bart", "rasur", "bartpflege"], "antwort": "Für Herren bieten wir auch Bartpflege und Rasuren an."},
        {"keywords": ["haarpflege", "produkte", "verkaufen", "shampoo", "pflege"], "antwort": "Wir verwenden hochwertige Markenprodukte und verkaufen auch Haarpflegeprodukte, Shampoos und Stylingprodukte im Salon."},
        {"keywords": ["team", "stylist", "friseur", "mitarbeiter"], "antwort": "Unser Team besteht aus erfahrenen Stylisten, die regelmäßig an Weiterbildungen teilnehmen, um Ihnen die neuesten Trends anbieten zu können."},
        {"keywords": ["wartezeit", "sofort", "heute", "spontan"], "antwort": "Kommen Sie gerne vorbei – manchmal haben wir auch spontan freie Termine. Am sichersten ist es aber, vorher kurz anzurufen."},
        {"keywords": ["verlängern", "extensions"], "antwort": "Ja, wir bieten auch Haarverlängerungen und Verdichtungen mit hochwertigen Extensions an."},
        {"keywords": ["glätten", "keratin", "straightening"], "antwort": "Wir bieten professionelle Keratin-Glättungen für dauerhaft glatte und gepflegte Haare an."},
        {"keywords": ["gutschein", "gutscheine", "verschenken", "geschenk"], "antwort": "Ja, Sie können bei uns Gutscheine kaufen – ideal als Geschenk für Freunde und Familie!"},
        {"keywords": ["kinder", "kids", "jungen", "mädchen", "sohn", "tochter"], "antwort": "Natürlich schneiden wir auch Kinderhaare. Der Preis für einen Kinderhaarschnitt startet ab 15 €."},
        {"keywords": ["hygiene", "corona", "masken", "sicherheit"], "antwort": "Ihre Gesundheit liegt uns am Herzen. Wir achten auf höchste Hygienestandards und desinfizieren regelmäßig unsere Arbeitsplätze."},
        {"keywords": ["kontakt", "telefon", "nummer", "anrufen"], "antwort": "Sie erreichen uns telefonisch unter 030-123456 oder per E-Mail unter info@friseur-muster.de."}
    ],
    "fallback": "Das weiß ich leider nicht. Bitte rufen Sie uns direkt unter 030-123456 an, wir helfen Ihnen gerne persönlich weiter."
}

def send_appointment_request(request_data):
    """
    Diese Funktion sendet eine E-Mail mit der Terminanfrage.
    """
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")
    receiver_email = os.environ.get("RECEIVER_EMAIL")

    if not all([sender_email, sender_password, receiver_email]):
        print("E-Mail-Konfiguration fehlt. E-Mail kann nicht gesendet werden.")
        return False

    msg = EmailMessage()
    msg['Subject'] = "Neue Terminanfrage über den Chatbot"
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Reply-To'] = request_data.get('email', 'no-reply@example.com')

    msg.set_content(
        f"Neue Terminanfrage:\n\n"
        f"Name: {request_data['name']}\n"
        f"E-Mail: {request_data.get('email', 'nicht angegeben')}\n"
        f"Service: {request_data.get('service', 'nicht angegeben')}\n"
        f"Datum und Uhrzeit: {request_data.get('date_time', 'nicht angegeben')}\n"
    )

    try:
        with smtplib.SMTP_SSL("smtp.web.de", 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"Fehler beim Senden der E-Mail: {e}")
        return False

@app.route('/api/chat', methods=['POST'])
def chat_handler():
    try:
        if not request.is_json:
            return jsonify({"error": "Fehlende JSON-Nachricht"}), 400

        user_message = request.json.get('message', '').lower()
        user_ip = request.remote_addr
     
        if user_ip not in user_states:
            user_states[user_ip] = {"state": "initial"}

        current_state = user_states[user_ip]["state"]
        response_text = faq_db['fallback']

        # Überprüfe den aktuellen Konversationsstatus
        if current_state == "initial":
            user_words = set(user_message.split())
            best_match_score = 0
            
            # Priorität für die Terminvereinbarung
            if any(keyword in user_message for keyword in ["termin", "buchen", "vereinbaren"]):
                response_text = "Gerne. Wie lautet Ihr vollständiger Name?"
                user_states[user_ip] = {"state": "waiting_for_name"}
            else:
                for item in faq_db['fragen']:
                    keyword_set = set(item['keywords'])
                    intersection = user_words.intersection(keyword_set)
                    score = len(intersection)
                    
                    if score > best_match_score:
                        best_match_score = score
                        response_text = item['antwort']
            
        elif current_state == "waiting_for_name":
            user_states[user_ip]["name"] = user_message
            response_text = "Vielen Dank. Wie lautet Ihre E-Mail-Adresse?"
            user_states[user_ip]["state"] = "waiting_for_email"

        elif current_state == "waiting_for_email":
            # Validierung der E-Mail-Adresse mit regulärem Ausdruck
            email_regex = r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
            if re.match(email_regex, user_message):
                user_states[user_ip]["email"] = user_message
                response_text = "Alles klar. Welchen Service möchten Sie buchen (z.B. Haarschnitt, Färben, Bartpflege)?"
                user_states[user_ip]["state"] = "waiting_for_service"
            else:
                response_text = "Das scheint keine gültige E-Mail-Adresse zu sein. Bitte geben Sie eine korrekte E-Mail-Adresse ein."
                # Bleibt im gleichen Zustand, damit der Benutzer es erneut versuchen kann.
        
        elif current_state == "waiting_for_service":
            user_states[user_ip]["service"] = user_message
            response_text = "Wann (Datum und Uhrzeit) würden Sie den Termin gerne wahrnehmen?"
            user_states[user_ip]["state"] = "waiting_for_datetime"

        elif current_state == "waiting_for_datetime":
            user_states[user_ip]["date_time"] = user_message
            
            # Sammle alle Daten und erstelle die Bestätigungsnachricht
            data = user_states[user_ip]
            response_text = (
                f"Bitte überprüfen Sie Ihre Angaben:\n"
                f"Name: {data.get('name', 'N/A')}\n"
                f"E-Mail: {data.get('email', 'N/A')}\n"
                f"Service: {data.get('service', 'N/A')}\n"
                f"Datum und Uhrzeit: {data.get('date_time', 'N/A')}\n\n"
                f"Möchten Sie die Anfrage so absenden? Bitte antworten Sie mit 'Ja' oder 'Nein'."
            )
            user_states[user_ip]["state"] = "waiting_for_confirmation"
        
        elif current_state == "waiting_for_confirmation":
            # Verarbeitung der Bestätigung oder Ablehnung
            if user_message in ["ja", "ja, das stimmt", "bestätigen", "ja bitte"]:
                request_data = {
                    "name": user_states[user_ip].get("name", "N/A"),
                    "email": user_states[user_ip].get("email", "N/A"),
                    "service": user_states[user_ip].get("service", "N/A"),
                    "date_time": user_states[user_ip].get("date_time", "N/A"),
                }
                
                if send_appointment_request(request_data):
                    response_text = "Vielen Dank! Ihre Terminanfrage wurde erfolgreich übermittelt. Wir werden uns in Kürze bei Ihnen melden."
                else:
                    response_text = "Entschuldigung, es gab ein Problem beim Senden Ihrer Anfrage. Bitte rufen Sie uns direkt an."
                
                # Konversation beenden und Zustand zurücksetzen
                user_states[user_ip]["state"] = "initial"
            
            elif user_message in ["nein", "abbrechen", "falsch"]:
                response_text = "Die Terminanfrage wurde abgebrochen. Falls Sie die Eingabe korrigieren möchten, beginnen Sie bitte erneut mit 'Termin vereinbaren'."
                # Konversation beenden und Zustand zurücksetzen
                user_states[user_ip]["state"] = "initial"
            
            else:
                response_text = "Bitte antworten Sie mit 'Ja' oder 'Nein'."
                # Bleibt im gleichen Zustand, damit der Benutzer es erneut versuchen kann.
        
        return jsonify({"reply": response_text})

    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")
        return jsonify({"error": "Interner Serverfehler"}), 500

if __name__ == '__main__':
    app.run(debug=True)
