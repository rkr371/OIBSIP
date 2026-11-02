# ==========================================================
# PYTHON VOICE ASSISTANT - COMPLETE PROJECT
# Google Colab Version
# ==========================================================

import speech_recognition as sr
import datetime
import threading
import urllib.request
import urllib.parse
import json
import os
import re
import base64
import subprocess
import tempfile
import time

from IPython.display import display, Javascript
from google.colab import output


# ==========================================================
# 1. CONFIGURATION
# ==========================================================

ASSISTANT_NAME = "Nova"
COMMAND_FILE = "custom_commands.json"

print("=" * 55)
print("       NOVA - PYTHON VOICE ASSISTANT")
print("=" * 55)


# ==========================================================
# 2. TEXT TO SPEECH
# ==========================================================

def speak(message):

    print(f"\n{ASSISTANT_NAME}: {message}")

    # Browser-based speech synthesis
    message_json = json.dumps(str(message))

    javascript = f"""
    const message = {message_json};

    window.speechSynthesis.cancel();

    const speech = new SpeechSynthesisUtterance(message);
    speech.lang = 'en-IN';
    speech.rate = 1;

    window.speechSynthesis.speak(speech);
    """

    try:
        output.eval_js(javascript)
    except Exception:
        print("Browser voice output unavailable.")


# ==========================================================
# 3. MICROPHONE VOICE INPUT
# ==========================================================

def listen():

    print("\n🎤 Click the microphone button to speak.")

    javascript = """
    async function recordAudio() {

        const stream = await navigator.mediaDevices.getUserMedia({
            audio: true
        });

        const recorder = new MediaRecorder(stream);
        const chunks = [];

        const div = document.createElement("div");
        const button = document.createElement("button");

        button.textContent = "🎤 Start Recording";
        button.style.padding = "15px";
        button.style.fontSize = "18px";

        div.appendChild(button);
        document.body.appendChild(div);

        return await new Promise((resolve, reject) => {

            let recording = false;

            button.onclick = () => {

                if (!recording) {

                    recorder.start();
                    recording = true;

                    button.textContent = "🔴 Stop Recording";

                } else {

                    recorder.stop();
                    button.disabled = true;
                    button.textContent = "Processing...";

                }
            };

            recorder.ondataavailable = event => {
                if (event.data.size > 0) {
                    chunks.push(event.data);
                }
            };

            recorder.onstop = async () => {

                const blob = new Blob(chunks, {
                    type: recorder.mimeType
                });

                const reader = new FileReader();

                reader.onloadend = () => {

                    const base64Audio =
                        reader.result.split(",")[1];

                    stream.getTracks().forEach(track => track.stop());

                    div.remove();

                    resolve(base64Audio);
                };

                reader.readAsDataURL(blob);
            };

            recorder.onerror = () => {
                stream.getTracks().forEach(track => track.stop());
                div.remove();
                reject("Recording failed");
            };

        });
    }

    recordAudio();
    """

    try:

        audio_base64 = output.eval_js(javascript)

        if not audio_base64:
            return ""

        audio_bytes = base64.b64decode(audio_base64)

        # Convert browser audio to WAV
        with tempfile.TemporaryDirectory() as temp_dir:

            webm_file = os.path.join(temp_dir, "recording.webm")
            wav_file = os.path.join(temp_dir, "recording.wav")

            with open(webm_file, "wb") as file:
                file.write(audio_bytes)

            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", webm_file,
                    "-ar", "16000",
                    "-ac", "1",
                    wav_file
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )

            recognizer = sr.Recognizer()

            with sr.AudioFile(wav_file) as source:
                audio = recognizer.record(source)

            command = recognizer.recognize_google(
                audio,
                language="en-IN"
            )

            print("\nYou:", command)

            return command.lower().strip()

    except sr.UnknownValueError:

        speak("Sorry, I could not understand your voice.")
        return ""

    except sr.RequestError:

        speak("Speech recognition service is unavailable.")
        return ""

    except Exception as error:

        print("Microphone error:", error)
        speak("Unable to process your recording.")
        return ""


# ==========================================================
# 4. DATE AND TIME
# ==========================================================

def get_time():

    current_time = datetime.datetime.now().strftime("%I:%M %p")

    speak("The current time is " + current_time)


def get_date():

    current_date = datetime.datetime.now().strftime(
        "%A, %d %B %Y"
    )

    speak("Today's date is " + current_date)


# ==========================================================
# 5. WEB SEARCH
# ==========================================================

def web_search(command):

    keywords = [
        "search for",
        "search",
        "google",
        "find",
        "look up"
    ]

    query = command

    for word in keywords:

        if word in query:
            query = query.replace(word, "", 1)
            break

    query = query.strip()

    if not query:
        speak("Please tell me what you want to search.")
        return

    search_url = (
        "https://www.google.com/search?q="
        + urllib.parse.quote_plus(query)
    )

    print("Search URL:", search_url)

    speak("I have prepared your Google search.")

    display(Javascript(
        "window.open(" + json.dumps(search_url) + ", '_blank');"
    ))


# ==========================================================
# 6. WEATHER SYSTEM
# ==========================================================

def get_weather(city):

    try:

        city = city.strip()

        if not city:
            speak("Please tell me the city name.")
            return

        geo_url = (
            "https://geocoding-api.open-meteo.com/v1/search?"
            + urllib.parse.urlencode({
                "name": city,
                "count": 1,
                "language": "en",
                "format": "json"
            })
        )

        request = urllib.request.Request(
            geo_url,
            headers={"User-Agent": "NovaVoiceAssistant/1.0"}
        )

        with urllib.request.urlopen(request, timeout=15) as response:
            location_data = json.loads(response.read().decode())

        if not location_data.get("results"):

            speak("Sorry, I could not find that city.")
            return

        location = location_data["results"][0]

        latitude = location["latitude"]
        longitude = location["longitude"]

        weather_url = (
            "https://api.open-meteo.com/v1/forecast?"
            + urllib.parse.urlencode({
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,"
                           "apparent_temperature,weather_code",
                "timezone": "auto"
            })
        )

        with urllib.request.urlopen(weather_url, timeout=15) as response:
            weather_data = json.loads(response.read().decode())

        current = weather_data["current"]

        temperature = current["temperature_2m"]
        humidity = current["relative_humidity_2m"]
        feels_like = current["apparent_temperature"]

        message = (
            f"The current temperature in {location['name']} "
            f"is {temperature} degrees Celsius. "
            f"It feels like {feels_like} degrees. "
            f"Humidity is {humidity} percent."
        )

        speak(message)

    except Exception as error:

        print("Weather error:", error)
        speak("Sorry, weather information is unavailable.")


# ==========================================================
# 7. REMINDER SYSTEM
# ==========================================================

def set_reminder(command):

    pattern = (
        r"remind me in (\d+)\s*"
        r"(seconds?|minutes?|hours?)\s+to\s+(.+)"
    )

    match = re.search(pattern, command)

    if not match:

        speak(
            "Please say, remind me in 10 seconds to study."
        )
        return

    amount = int(match.group(1))
    unit = match.group(2)
    task = match.group(3)

    if "second" in unit:
        seconds = amount

    elif "minute" in unit:
        seconds = amount * 60

    else:
        seconds = amount * 3600

    if seconds <= 0:
        speak("Please choose a positive reminder duration.")
        return

    speak(f"Reminder set for {amount} {unit}.")

    def reminder_alert():

        message = "Reminder! " + task

        print("\n🔔 REMINDER:", message)

        # Browser speaks the reminder after the delay.
        message_json = json.dumps(message)

        javascript = f"""
        const reminder = new SpeechSynthesisUtterance(
            {message_json}
        );
        reminder.lang = 'en-IN';
        window.speechSynthesis.speak(reminder);
        """

        try:
            output.eval_js(javascript)
        except Exception:
            print("Reminder alert:", message)

    timer = threading.Timer(seconds, reminder_alert)
    timer.daemon = True
    timer.start()


# ==========================================================
# 8. LOCAL KNOWLEDGE BASE
# ==========================================================

knowledge_base = {

    "python": (
        "Python is a high-level programming language "
        "used in AI, machine learning, automation and web development."
    ),

    "artificial intelligence": (
        "Artificial Intelligence is a technology that enables "
        "machines to perform tasks that normally require human intelligence."
    ),

    "machine learning": (
        "Machine learning is a branch of artificial intelligence "
        "that allows computers to learn patterns from data."
    ),

    "voice assistant": (
        "A voice assistant is a software application that "
        "understands spoken commands and responds to users."
    ),

    "html": (
        "HTML is the standard markup language used to structure web pages."
    ),

    "computer": (
        "A computer is an electronic device that processes data "
        "and performs calculations."
    )
}


def answer_question(command):

    for keyword, answer in knowledge_base.items():

        if keyword in command:

            speak(answer)
            return

    speak(
        "I do not have an answer in my local knowledge base. "
        "You can search the internet for more information."
    )


# ==========================================================
# 9. CUSTOM COMMAND SYSTEM
# ==========================================================

def load_custom_commands():

    if os.path.exists(COMMAND_FILE):

        try:

            with open(COMMAND_FILE, "r") as file:
                return json.load(file)

        except (json.JSONDecodeError, OSError):
            return {}

    return {}


custom_commands = load_custom_commands()


def save_custom_commands():

    try:

        with open(COMMAND_FILE, "w") as file:

            json.dump(
                custom_commands,
                file,
                indent=4
            )

        print("Custom commands saved.")

    except OSError as error:

        print("Save error:", error)


def add_custom_command():

    command = input("Enter your custom command: ").strip().lower()

    response = input("Enter assistant response: ").strip()

    if command and response:

        custom_commands[command] = response

        save_custom_commands()

        speak("Your custom command has been added.")

    else:

        speak("Command and response cannot be empty.")


# ==========================================================
# 10. NLP INTENT RECOGNITION
# ==========================================================

def recognize_intent(command):

    command = command.lower().strip()

    if not command:
        return "unknown"

    if command in ["exit", "quit", "stop", "goodbye"]:
        return "exit"

    if command == "add custom command":
        return "add_custom"

    if command.startswith("remind me in") or "set reminder" in command:
        return "reminder"

    if "weather" in command or "temperature" in command:
        return "weather"

    if command in custom_commands:
        return "custom"

    greetings = [
        "hello",
        "hi",
        "hey",
        "good morning",
        "good afternoon",
        "good evening"
    ]

    if any(command == greeting or command.startswith(greeting + " ")
           for greeting in greetings):
        return "greeting"

    if "time" in command or "clock" in command:
        return "time"

    if any(word in command.split()
           for word in ["date", "today", "day"]):
        return "date"

    if "who are you" in command or "your name" in command:
        return "identity"

    if any(word in command
           for word in ["search", "google", "look up", "find"]):
        return "search"

    if any(word in command.split()
           for word in ["what", "who", "why", "how", "explain"]):
        return "question"

    return "unknown"


# ==========================================================
# 11. COMMAND PROCESSING
# ==========================================================

def process_command(command):

    intent = recognize_intent(command)

    print("Detected Intent:", intent)

    if intent == "greeting":

        speak("Hello! I am Nova, your personal voice assistant.")

    elif intent == "time":

        get_time()

    elif intent == "date":

        get_date()

    elif intent == "identity":

        speak("I am Nova, your Python voice assistant.")

    elif intent == "search":

        web_search(command)

    elif intent == "weather":

        city_match = re.search(
            r"(?:weather|temperature)\s+(?:in|at|of)\s+(.+)",
            command
        )

        if city_match:
            city = city_match.group(1).strip()
            get_weather(city)

        else:
            city = input("Enter city name: ")
            get_weather(city)

    elif intent == "reminder":

        set_reminder(command)

    elif intent == "question":

        answer_question(command)

    elif intent == "add_custom":

        add_custom_command()

    elif intent == "custom":

        speak(custom_commands[command])

    elif intent == "unknown":

        speak(
            "Sorry, I do not understand that command. "
            "You can ask me to search the internet."
        )


# ==========================================================
# 12. MAIN VOICE ASSISTANT LOOP
# ==========================================================

def start_assistant():

    speak(
        "Hello! I am Nova. Your voice assistant is ready. "
        "How can I help you?"
    )

    while True:

        command = listen()

        if not command:
            continue

        process_command(command)

        if recognize_intent(command) == "exit":

            speak("Goodbye! Have a great day.")
            break


# ==========================================================
# START PROJECT
# ==========================================================

start_assistant()