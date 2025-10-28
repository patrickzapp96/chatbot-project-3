from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re
import json
from datetime import datetime, timedelta

# Google API-Importe
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError

app = Flask(__name__)
CORS(app)

# Globale Variable zur Speicherung des Konversationsstatus
user_states = {}

# FAQ-Datenbank
faq_db = {
    "fragen": [
        {
            "id": 1,
            "kategorie": "Öffnungszeiten",
            "titel": "Öffnungszeiten",
            "keywords": ["öffnungszeiten", "wann", "geöffnet", "offen", "arbeitszeit"],
            "antwort": "Wir sind Montag–Freitag von 9:00 bis 18:00 Uhr und Samstag von 9:00 bis 14:00 Uhr für Sie da. Sonntag ist Ruhetag."
        },
        {
            "id": 2,
            "kategorie": "Terminbuchung",
            "titel": "Termin vereinbaren",
            "keywords": ["termin", "buchen", "vereinbaren", "ausmachen", "reservieren", "online"],
            "antwort": "Wenn Sie einen Termin vereinbaren möchten, geben Sie bitte 'termin vereinbaren' ein oder rufen sie uns an unter 030-123456."
        },
        {
            "id": 3,
            "kategorie": "Allgemein",
            "titel": "Adresse",
            "keywords": ["adresse", "wo", "anschrift", "finden", "lage"],
            "antwort": "Unsere Adresse lautet: Musterstraße 12, 10115 Berlin. Wir sind zentral und gut erreichbar."
        },
        {
            "id": 4,
            "kategorie": "Preise",
            "titel": "Preise und Kosten",
            "keywords": ["preise", "kosten", "kostet", "gebühren", "haarschnitt", "herrenhaarschnitt", "damenhaarschnitt"],
            "antwort": "Ein Damenhaarschnitt kostet ab 25 €, Herrenhaarschnitt ab 20 €. Färben ab 45 €. Die komplette Preisliste finden Sie im Salon."
        },
        {
            "id": 5,
            "kategorie": "Zahlung",
            "titel": "Zahlungsmethoden",
            "keywords": ["zahlung", "karte", "bar", "visa", "mastercard", "paypal", "kartenzahlung", "kontaktlos", "bezahlen"],
            "antwort": "Sie können bar, mit EC-Karte, Kreditkarte (Visa/Mastercard) und sogar kontaktlos per Handy bezahlen."
        },
        {
            "id": 6,
            "kategorie": "Allgemein",
            "titel": "Parkmöglichkeiten",
            "keywords": ["parkplätze", "parkplatz", "parken", "auto", "stellplatz"],
            "antwort": "Vor unserem Salon befinden sich kostenlose Parkplätze. Alternativ erreichen Sie uns auch gut mit den öffentlichen Verkehrsmitteln."
        },
        {
            "id": 7,
            "kategorie": "Services",
            "titel": "Waschen und Föhnen",
            "keywords": ["waschen", "föhnen", "styling", "legen"],
            "antwort": "Natürlich – wir bieten Waschen, Föhnen und individuelles Styling an. Perfekt auch für Events oder Fotoshootings."
        },
        {
            "id": 8,
            "kategorie": "Services",
            "titel": "Haare färben",
            "keywords": ["färben", "farbe", "farben", "strähnchen", "blondieren", "haartönung"],
            "antwort": "Wir färben und tönen Haare in allen Farben, inklusive Strähnchen, Balayage und Blondierungen. Unsere Stylisten beraten Sie individuell."
        },
        {
            "id": 9,
            "kategorie": "Services",
            "titel": "Dauerwelle",
            "keywords": ["dauerwelle", "dauerwellen", "lockenfrisuren", "locken", "lockenfrisur"],
            "antwort": "Ja, wir bieten auch Dauerwellen und Locken-Stylings an."
        },
        {
            "id": 10,
            "kategorie": "Services",
            "titel": "Braut- und Hochsteckfrisuren",
            "keywords": ["hochzeit", "brautfrisur", "brautfrisuren", "hochsteckfrisur"],
            "antwort": "Wir stylen wunderschöne Braut- und Hochsteckfrisuren. Am besten buchen Sie hierfür rechtzeitig einen Probetermin."
        },
        {
            "id": 11,
            "kategorie": "Services",
            "titel": "Bartpflege",
            "keywords": ["bart", "rasur", "bartpflege"],
            "antwort": "Für Herren bieten wir auch Bartpflege und Rasuren an."
        },
        {
            "id": 12,
            "kategorie": "Produkte",
            "titel": "Verkauf von Haarpflegeprodukten",
            "keywords": ["haarpflege", "produkte", "verkaufen", "shampoo", "pflege"],
            "antwort": "Wir verwenden hochwertige Markenprodukte und verkaufen auch Haarpflegeprodukte, Shampoos und Stylingprodukte im Salon."
        },
        {
            "id": 13,
            "kategorie": "Allgemein",
            "titel": "Das Team",
            "keywords": ["team", "stylist", "friseur", "mitarbeiter"],
            "antwort": "Unser Team besteht aus erfahrenen Stylisten, die regelmäßig an Weiterbildungen teilnehmen, um Ihnen die neuesten Trends anbieten zu können."
        },
        {
            "id": 14,
            "kategorie": "Terminbuchung",
            "titel": "Spontane Termine",
            "keywords": ["warten", "wartezeit", "sofort", "heute", "spontan"],
            "antwort": "Kommen Sie gerne vorbei – manchmal haben wir auch spontan freie Termine. Am sichersten ist es aber, vorher kurz anzurufen unter 030-123456"
        },
        {
            "id": 15,
            "kategorie": "Services",
            "titel": "Haarverlängerung",
            "keywords": ["verlängern", "extensions", "haarverlängerungen", "verlängerung", "haarverlängerung"],
            "antwort": "Ja, wir bieten auch Haarverlängerungen und Verdichtungen mit hochwertigen Extensions an."
        },
        {
            "id": 16,
            "kategorie": "Services",
            "titel": "Haar glätten",
            "keywords": ["glätten", "keratin", "straightening"],
            "antwort": "Wir bieten professionelle Keratin-Glättungen für dauerhaft glatte und gepflegte Haare an."
        },
        {
            "id": 17,
            "kategorie": "Produkte",
            "titel": "Gutscheine kaufen",
            "keywords": ["gutschein", "gutscheine", "verschenken", "geschenk"],
            "antwort": "Ja, Sie können bei uns Gutscheine kaufen – ideal als Geschenk für Freunde und Familie!"
        },
        {
            "id": 18,
            "kategorie": "Services",
            "titel": "Kinderhaarschnitt",
            "keywords": ["kinder", "kids", "jungen", "mädchen", "sohn", "tochter"],
            "antwort": "Natürlich schneiden wir auch Kinderhaare. Der Preis für einen Kinderhaarschnitt startet ab 15 €."
        },
        {
            "id": 19,
            "kategorie": "Hygiene",
            "titel": "Hygienestandards",
            "keywords": ["hygiene", "corona", "masken", "sicherheit"],
            "antwort": "Ihre Gesundheit liegt uns am Herzen. Wir achten auf höchste Hygienestandards und desinfizieren regelmäßig unsere Arbeitsplätze."
        },
        {
            "id": 20,
            "kategorie": "Allgemein",
            "titel": "Kontakt",
            "keywords": ["kontakt", "kontaktdaten", "telefonnummer", "telefon", "nummer", "anrufen"],
            "antwort": "Sie erreichen uns telefonisch unter 030-123456 oder per E-Mail unter info@friseur-muster.de."
        },
        {
            "id": 21,
            "kategorie": "Services",
            "titel": "Balayage und Strähnchen",
            "keywords": ["balayage", "strähnchen", "highlights", "lowlights"],
            "antwort": "Wir sind Spezialisten für Balayage, Highlights und Lowlights. Unsere Stylisten kreieren natürliche Farbverläufe, die Ihr Haar zum Strahlen bringen."
        },
        {
            "id": 22,
            "kategorie": "Services",
            "titel": "Olaplex-Behandlung",
            "keywords": ["olaplex", "haarpflege", "kur", "stärkung", "haare reparieren", "reparieren"],
            "antwort": "Wir bieten eine professionelle Olaplex-Behandlung an, die Haarschäden repariert, die Haarstruktur stärkt und für gesundes, glänzendes Haar sorgt."
        },
        {
            "id": 23,
            "kategorie": "Services",
            "titel": "Trockenhaarschnitt",
            "keywords": ["trockenhaarschnitt", "trockenschnitt", "ohne waschen", "schnell"],
            "antwort": "Ein Trockenhaarschnitt ist bei uns nach Absprache möglich. Er ist ideal, wenn Sie wenig Zeit haben oder einfach nur die Spitzen geschnitten haben möchten."
        },
        {
            "id": 24,
            "kategorie": "Terminbuchung",
            "titel": "Termin stornieren",
            "keywords": ["stornieren", "termin stornieren", "termin absagen", "verschieben", "nicht kommen"],
            "antwort": "Sie können Ihren Termin bis zu 24 Stunden vorher telefonisch unter 030-123456 oder per E-Mail an info@friseur-muster.de absagen. Bei Nichterscheinen behalten wir uns vor, eine Ausfallgebühr zu berechnen."
        },
        {
            "id": 25,
            "kategorie": "Allgemein",
            "titel": "Barrierefreiheit",
            "keywords": ["rollstuhl", "barrierefrei", "zugang", "barrierefreiheit"],
            "antwort": "Unser Salon ist barrierefrei zugänglich, sodass auch Rollstuhlfahrer problemlos zu uns kommen können."
        },
        {
            "id": 26,
            "kategorie": "Allgemein",
            "titel": "Haustiere",
            "keywords": ["hund", "haustier", "tiere"],
            "antwort": "Aus hygienischen Gründen und im Interesse aller Kunden sind Haustiere in unserem Salon leider nicht gestattet."
        }
    ],
    "fallback": "Das weiß ich leider nicht. Bitte rufen Sie uns direkt unter 030-123456 an, wir helfen Ihnen gerne persönlich weiter."
}

# --- Google Calendar API Funktionen ---
def get_calendar_service():
    """Authentifiziert sich und gibt ein Google Calendar Service-Objekt zurück."""
    try:
        creds = Credentials.from_authorized_user_info(json.loads(os.environ['GOOGLE_TOKEN']), ["https://www.googleapis.com/auth/calendar.events"])
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        return build('calendar', 'v3', credentials=creds)
    except Exception as e:
        print(f"Auth-Fehler: {e}")
        return None

def create_calendar_event(service, name, email, service_type, start_time_iso, duration_minutes=60):
    """Erstellt einen neuen Termin im Google Kalender."""
    try:
        start_time = datetime.fromisoformat(start_time_iso)
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        event = {
            'summary': f"Termin mit {name} für {service_type}",
            'description': f"Kunde: {name}\nService: {service_type}\nE-Mail: {email}",
            'start': {'dateTime': start_time.isoformat(), 'timeZone': 'Europe/Berlin'},
            'end': {'dateTime': end_time.isoformat(), 'timeZone': 'Europe/Berlin'},
            'attendees': [{'email': 'patrick.zapp96@gmail.com'}],
            'reminders': {'useDefault': True},
        }
        
        event = service.events().insert(calendarId='primary', body=event).execute()
        return event.get('htmlLink')
    except HttpError as error:
        print(f'API-Fehler beim Erstellen des Termins: {error}')
        return None
    except Exception as e:
        print(f'Allgemeiner Fehler beim Erstellen des Termins: {e}')
        return None

def get_available_slots(service):
    """Ermittelt und gibt eine Liste freier Termine zurück."""
    now = datetime.utcnow()
    one_week_later = now + timedelta(days=7)
    
    # Beispiel für feste Öffnungszeiten (kann dynamisch angepasst werden)
    business_hours = {
        0: (9, 18),  # Montag
        1: (9, 18),  # Dienstag
        2: (9, 18),  # Mittwoch
        3: (9, 18),  # Donnerstag
        4: (9, 18),  # Freitag
        5: (9, 14),  # Samstag
        6: None,     # Sonntag
    }
    
    available_slots = []
    
    for i in range(7):
        day = now + timedelta(days=i)
        weekday = day.weekday()
        
        if business_hours.get(weekday):
            start_hour, end_hour = business_hours[weekday]
            
            for hour in range(start_hour, end_hour):
                slot_start = day.replace(hour=hour, minute=0, second=0, microsecond=0)
                
                # Check, ob der Slot in der Zukunft liegt
                if slot_start > now:
                    is_available = True
                    # Prüfe gegen vorhandene Termine (vereinfacht)
                    # Dies erfordert eine erweiterte API-Abfrage, um alle Termine zu prüfen
                    # Beispielhaft wird hier nur ein generischer Slot hinzugefügt
                    
                    if is_available:
                        # Formatierung für das Frontend
                        display_date = slot_start.strftime("%A, %d. %b. %H:%M Uhr")
                        available_slots.append({
                            "start": slot_start.isoformat(),
                            "display": display_date
                        })
    
    return available_slots


# --- Haupt-Chat-Handler ---
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

        # Logik für die Terminbuchung
        if current_state == "initial":
            if any(keyword in user_message for keyword in ["termin buchen", "termin vereinbaren", "termin ausmachen", "termin reservieren"]):
                user_states[user_ip] = {"state": "waiting_for_confirmation_start"}
                return jsonify({"reply": "Möchten Sie einen Termin vereinbaren? Bitte antworten Sie mit 'Ja' oder 'Nein'."})
            else:
                cleaned_message = re.sub(r'[^\w\s]', '', user_message)
                user_words = set(cleaned_message.split())
                best_match_score = 0
                best_match_answer = faq_db['fallback']

                for item in faq_db['fragen']:
                    keyword_set = set(item['keywords'])
                    intersection = user_words.intersection(keyword_set)
                    score = len(intersection)
                    
                    if score > best_match_score:
                        best_match_score = score
                        best_match_answer = item['antwort']
                
                return jsonify({"reply": best_match_answer})

        # --- Terminbuchungsablauf ---
        elif current_state == "waiting_for_confirmation_start":
            if user_message.lower() in ["ja", "ja, das stimmt", "bestätigen", "ja bitte"]:
                user_states[user_ip]["state"] = "waiting_for_name"
                return jsonify({"reply": "Gerne. Wie lautet Ihr vollständiger Name?"})
            else:
                user_states[user_ip]["state"] = "initial"
                return jsonify({"reply": "Die Terminanfrage wurde abgebrochen."})

        elif current_state == "waiting_for_name":
            user_states[user_ip]["name"] = user_message
            user_states[user_ip]["state"] = "waiting_for_email"
            return jsonify({"reply": "Vielen Dank. Wie lautet Ihre E-Mail-Adresse?"})

        elif current_state == "waiting_for_email":
            email_regex = r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
            if re.match(email_regex, user_message):
                user_states[user_ip]["email"] = user_message
                user_states[user_ip]["state"] = "waiting_for_service"
                return jsonify({"reply": "Alles klar. Welchen Service möchten Sie buchen (z.B. Haarschnitt, Färben, Bartpflege)?"})
            else:
                return jsonify({"reply": "Das scheint keine gültige E-Mail-Adresse zu sein. Bitte geben Sie eine korrekte E-Mail-Adresse ein."})

        elif current_state == "waiting_for_service":
            user_states[user_ip]["service"] = user_message
            calendar_service = get_calendar_service()
            
            if calendar_service:
                available_slots = get_available_slots(calendar_service)
                if available_slots:
                    user_states[user_ip]["state"] = "waiting_for_slot_selection"
                    return jsonify({"type": "calendar_slots", "slots": available_slots})
                else:
                    user_states[user_ip]["state"] = "initial"
                    return jsonify({"reply": "Entschuldigung, es sind in der nächsten Woche keine Termine verfügbar. Bitte versuchen Sie es später erneut oder rufen Sie uns an."})
            else:
                user_states[user_ip]["state"] = "initial"
                return jsonify({"reply": "Entschuldigung, es gab ein Problem beim Zugriff auf den Kalender. Bitte rufen Sie uns direkt an unter 030-123456."})
        
        elif current_state == "waiting_for_slot_selection":
            user_states[user_ip]["date_time_iso"] = user_message
            data = user_states[user_ip]
            response_text = (
                f"Bitte überprüfen Sie Ihre Angaben:\n"
                f"Name: {data.get('name', 'N/A')}\n"
                f"E-Mail: {data.get('email', 'N/A')}\n"
                f"Service: {data.get('service', 'N/A')}\n"
                f"Datum und Uhrzeit: {data.get('date_time_iso', 'N/A')}\n\n"
                f"Möchten Sie die Anfrage so absenden? Bitte antworten Sie mit 'Ja' oder 'Nein'."
            )
            user_states[user_ip]["state"] = "waiting_for_confirmation"
            return jsonify({"reply": response_text})
        
        elif current_state == "waiting_for_confirmation":
            if user_message in ["ja", "ja, das stimmt", "bestätigen", "ja bitte"]:
                calendar_service = get_calendar_service()
                if calendar_service:
                    event_link = create_calendar_event(
                        calendar_service,
                        user_states[user_ip].get("name", "N/A"),
                        user_states[user_ip].get("email", "N/A"),
                        user_states[user_ip].get("service", "N/A"),
                        user_states[user_ip].get("date_time_iso", "N/A")
                    )
                    if event_link:
                        response_text = f"Vielen Dank! Ihr Termin wurde erfolgreich gebucht. Sie finden ihn hier: {event_link}"
                    else:
                        response_text = "Entschuldigung, es gab ein Problem beim Buchen Ihres Termins. Bitte rufen Sie uns direkt an unter 030-123456."
                else:
                    response_text = "Entschuldigung, es gab ein Problem beim Zugriff auf den Kalender. Bitte rufen Sie uns direkt an unter 030-123456."
                
                user_states[user_ip]["state"] = "initial"
                return jsonify({"reply": response_text})

            elif user_message in ["nein", "abbrechen", "falsch"]:
                user_states[user_ip]["state"] = "initial"
                return jsonify({"reply": "Die Terminanfrage wurde abgebrochen."})
            
            else:
                return jsonify({"reply": "Bitte antworten Sie mit 'Ja' oder 'Nein'."})

    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")
        return jsonify({"error": "Interner Serverfehler"}), 500

if __name__ == '__main__':
    app.run(debug=True)




