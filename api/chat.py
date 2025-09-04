from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import smtplib
from email.message import EmailMessage
import sqlite3

app = Flask(__name__)
CORS(app)

# ----------------- NEUER CODE: Datenbank-Setup und Verwaltung -----------------

DATABASE = 'faq_database.db'

def setup_database():
    """Erstellt die FAQ-Tabelle, falls sie nicht existiert, und füllt sie initial."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS faqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keywords TEXT NOT NULL,
            answer TEXT NOT NULL
        )
    """)
    
    # Füllen Sie die Datenbank mit den initialen Daten aus Ihrer Original-FAQ
    # Nur wenn die Tabelle leer ist
    cursor.execute("SELECT COUNT(*) FROM faqs")
    if cursor.fetchone()[0] == 0:
        faq_data = [
            ("öffnungszeiten,wann geöffnet,wann offen,arbeitszeit", "Wir sind Montag–Freitag von 9:00 bis 18:00 Uhr und Samstag von 9:00 bis 14:00 Uhr für Sie da. Sonntag ist Ruhetag."),
            ("termin,vereinbaren,buchen,reservieren,online", "Wenn Sie einen Termin vereinbaren möchten, geben Sie bitte zuerst Ihren vollständigen Namen ein."),
            ("adresse,wo,anschrift,finden,lage", "Unsere Adresse lautet: Musterstraße 12, 10115 Berlin. Wir sind zentral und gut erreichbar."),
            ("preise,kosten,gebühren,haarschnitt", "Ein Damenhaarschnitt kostet ab 25 €, Herrenhaarschnitt ab 20 €. Färben ab 45 €. Die komplette Preisliste finden Sie im Salon."),
            ("zahlung,karte,bar,visa,mastercard,paypal", "Sie können bar, mit EC-Karte, Kreditkarte (Visa/Mastercard) und sogar kontaktlos per Handy bezahlen."),
            ("parkplatz,parken,auto,stellplatz", "Vor unserem Salon befinden sich kostenlose Parkplätze. Alternativ erreichen Sie uns auch gut mit den öffentlichen Verkehrsmitteln."),
            ("waschen,föhnen,styling,legen", "Natürlich – wir bieten Waschen, Föhnen und individuelles Styling an. Perfekt auch für Events oder Fotoshootings."),
            ("färben,farbe,strähnen,blondieren,haartönung", "Wir färben und tönen Haare in allen Farben, inklusive Strähnen, Balayage und Blondierungen. Unsere Stylisten beraten Sie individuell."),
            ("dauerwelle,locken", "Ja, wir bieten auch Dauerwellen und Locken-Stylings an."),
            ("hochzeit,brautfrisur,hochsteckfrisur", "Wir stylen wunderschöne Braut- und Hochsteckfrisuren. Am besten buchen Sie hierfür rechtzeitig einen Probetermin."),
            ("bart,rasur,bartpflege", "Für Herren bieten wir auch Bartpflege und Rasuren an."),
            ("haarpflege,produkte,verkaufen,shampoo,pflege", "Wir verwenden hochwertige Markenprodukte und verkaufen auch Haarpflegeprodukte, Shampoos und Stylingprodukte im Salon."),
            ("team,stylist,friseur,mitarbeiter", "Unser Team besteht aus erfahrenen Stylisten, die regelmäßig an Weiterbildungen teilnehmen, um Ihnen die neuesten Trends anbieten zu können."),
            ("wartezeit,sofort,heute", "Kommen Sie gerne vorbei – manchmal haben wir auch spontan freie Termine. Am sichersten ist es aber, vorher kurz anzurufen."),
            ("verlängern,extensions", "Ja, wir bieten auch Haarverlängerungen und Verdichtungen mit hochwertigen Extensions an."),
            ("glätten,keratin,straightening", "Wir bieten professionelle Keratin-Glättungen für dauerhaft glatte und gepflegte Haare an."),
            ("gutschein,verschenken,geschenk", "Ja, Sie können bei uns Gutscheine kaufen – ideal als Geschenk für Freunde und Familie!"),
            ("kinder,kids,jungen,mädchen", "Natürlich schneiden wir auch Kinderhaare. Der Preis für einen Kinderhaarschnitt startet ab 15 €."),
            ("hygiene,corona,masken,sicherheit", "Ihre Gesundheit liegt uns am Herzen. Wir achten auf höchste Hygienestandards und desinfizieren regelmäßig unsere Arbeitsplätze."),
            ("kontakt,telefon,nummer,anrufen", "Sie erreichen uns telefonisch unter 030-123456 oder per E-Mail unter info@friseur-muster.de.")
        ]
        
        cursor.executemany("INSERT INTO faqs (keywords, answer) VALUES (?, ?)", faq_data)
        conn.commit()

    conn.close()

# ----------------- NEUER CODE: Fuzzy-Keyword-Matching -----------------

def find_faq_answer_fuzzy(user_message):
    """
    Sucht eine passende Antwort in der Datenbank mithilfe von Fuzzy-Matching.
    
    Diese Funktion prüft, ob ein Teil der Nutzernachricht den Keywords der FAQ-Einträge
    ähnelt, anstatt eine exakte Übereinstimmung zu fordern.
    """
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Zerlegen Sie die Nachricht in einzelne Wörter und prüfen Sie auf Übereinstimmungen
    message_words = set(user_message.lower().split())
    
    cursor.execute("SELECT keywords, answer FROM faqs")
    for keywords_str, answer in cursor.fetchall():
        faq_keywords = set(keywords_str.lower().split(','))
        
        # Berechnen Sie die Schnittmenge der Wörter
        common_words = message_words.intersection(faq_keywords)
        
        # Wenn eine signifikante Anzahl von Wörtern übereinstimmt, ist es ein Match
        if len(common_words) > 0:
            conn.close()
            return answer
    
    conn.close()
    return None

# Rufen Sie die Setup-Funktion beim Start der App auf
setup_database()

# Temporärer Speicher für den Konversationsstatus der Benutzer
user_states = {}

def send_appointment_request(request_data):
    # Diese Funktion bleibt unverändert
    ... [cite: 35, 36, 37]

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
        response_text = "Das weiß ich leider nicht. Bitte rufen Sie uns direkt unter 030-123456 an, wir helfen Ihnen gerne persönlich weiter." # Ihr Fallback-Text

        # Überprüfen Sie zuerst auf den Konversationsstatus für die Terminbuchung
        if current_state == "initial":
            if any(keyword in user_message for keyword in ["termin", "buchen", "vereinbaren"]):
                response_text = "Gerne. Wie lautet Ihr vollständiger Name?"
                user_states[user_ip] = {"state": "waiting_for_name"}
            else:
                # ----------------- ANGEPASSTER CODE: Datenbank-Suche -----------------
                faq_answer = find_faq_answer_fuzzy(user_message)
                if faq_answer:
                    response_text = faq_answer
        
        # Bestehende Konversationslogik für Terminbuchung bleibt unverändert
        elif current_state == "waiting_for_name":
            ... [cite: 42]
        elif current_state == "waiting_for_email":
            ... [cite: 43]
        elif current_state == "waiting_for_service":
            ... [cite: 44]
        elif current_state == "waiting_for_datetime":
            ... [cite: 46, 47]

        return jsonify({"reply": response_text})

    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")
        return jsonify({"error": "Interner Serverfehler"}), 500

if __name__ == '__main__':
    app.run(debug=True)
