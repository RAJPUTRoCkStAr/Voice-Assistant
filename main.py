from datetime import datetime, date, timedelta, timezone
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pytz
import speech_recognition as sr
import pyttsx3
import subprocess

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
MONTHS = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']
DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
DAY_EXTENSIONS = ["nd", "rd", "th", "st"]

def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def get_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)
        said = ""
        try:
            said = r.recognize_google(audio)
            print(said)
        except Exception as e:
            print("Exception: " + str(e))
    return said.lower()

def authenticate_google():
    creds = None
    service = None
    
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())
    
    try:
        service = build("calendar", "v3", credentials=creds)
    except Exception as e:
        print(f"Exception while building service: {e}")

    return service

def get_events(day, service):
    start_of_day = datetime.combine(day, datetime.min.time())
    end_of_day = datetime.combine(day, datetime.max.time())
    utc = pytz.UTC
    start_of_day = start_of_day.astimezone(utc)
    end_of_day = end_of_day.astimezone(utc)
    
    try:
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=start_of_day.isoformat(),
                timeMax=end_of_day.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            print("No events found for the specified day.")
        else:
            speak(f"you have {len(events)} events on this day")

        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            print(start, event["summary"])
            start_time = str(start.split("T")[1].split("-")[0])
            if int(start_time.split(":")[0])<12:
                start_time = start_time + "am"
            else:
                start_time = str(int(start_time.split(":")[0])- 12) + start_time.split(":")[1]
                start_time = start_time + "pm"
            
            speak(event["summary"] + "at" + start_time)
    except HttpError as error:
        print(f"An error occurred: {error}")

def get_date(text):
    text = text
    today = date.today()

    if "today" in text:
        return today

    day = -1
    day_of_week = -1
    month = -1 
    year = today.year

    for word in text.split():
        if word in MONTHS:
            month = MONTHS.index(word) + 1
        elif word in DAYS:
            day_of_week = DAYS.index(word)
        elif word.isdigit():
            day = int(word)
        else:
            for ext in DAY_EXTENSIONS:
                found = word.find(ext)
                if found > 0:
                    try:
                        days = int(word[:found])
                    except ValueError:
                        pass

    if month < today.month and month != -1:
        year += 1
    if day < today.day and month == -1 and day != -1:
        month += 1
    if month == -1 and day == -1 and day_of_week != -1:
        current_day_of_week = today.weekday()
        dif = day_of_week - current_day_of_week
        if dif < 0:
            dif += 7
            if "next" in text:
                dif += 7
        return today + timedelta(days=dif)

    return date(year, month, day)

def note(text):
    date = datetime.now()
    file_name = str(date).replace(":","-")+"-note.txt"
    with open(file_name,"w") as f:
        f.write(text)
    vscode = "C:\\Users\\sumit\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe"
    # subprocess.Popen(["notepad.exe",file_name])
    subprocess.Popen([vscode,file_name])

wake = "hey jarvis"
service = authenticate_google()
print("start")

# if service:
#     text = get_audio()
#     get_events(get_date(text), service)
# else:
#     print("Failed to initialize Google Calendar service.")
while True:
    text = get_audio()
    if text.count(wake) > 0:
        speak("kaizer is ready sir ")
        print("kaizer is ready sir ")
        text = get_audio()
        if service:
            note_str = ["make a note","remember this"]
            for pharse in note_str:
                if pharse in text :
                    speak("what would you like me to write down ?")
                    note_txt = get_audio()
                    note(note_txt)
                    speak("I have noted that")
            calender_str = [
            "what do I have ",
            "do I have any plans ",
            "tell me my schedule for",
            "events on"
            ]
            for pharse in calender_str:
                if pharse in text:
                    date = get_date(text)
                    if date:
                        get_events(date, service)
                    else:
                        speak("please Try Again")
        else:
            print("Failed to initialize Google Calendar service.")