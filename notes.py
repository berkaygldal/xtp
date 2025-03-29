import tkinter as tk
from tkinter import ttk
import pyttsx3
from vosk import Model, KaldiRecognizer, SetLogLevel
import pyaudio
import json
import google.generativeai as genai
import sv_ttk
import pywinstyles, sys

genai.configure(api_key="NO-FREE-API-KEY-FOR-YOU")
SetLogLevel(-1)

try:
    vosk_model = Model(lang="tr")
except Exception as e:
    vosk_model = None
    print("Vosk model could not be loaded:", e)

root = tk.Tk()
root.title("XTPnotes")
root.geometry("500x475")

root.iconbitmap("xtp.ico")

def applyTitleBarTheme(root):
    version = sys.getwindowsversion()
    if version.major == 10 and version.build >= 22000:
        pywinstyles.change_header_color(root, "#1c1c1c" if sv_ttk.get_theme() == "dark" else "#fafafa")
    elif version.major == 10:
        pywinstyles.apply_style(root, "dark" if sv_ttk.get_theme() == "dark" else "normal")
        root.wm_attributes("-alpha", 0.99)
        root.wm_attributes("-alpha", 1)

text_area = tk.Text(root, wrap=tk.WORD, width=50, height=15, font=("Arial", 12))
text_area.place(relx=0.5, rely=0.1, anchor="n")
text_area.config(bg="#2e2e2e", fg="white")
text_area.config(yscrollcommand=lambda f, l: None)
text_area.config(xscrollcommand=lambda f, l: None)

listeningActive = False
mic = None
stream = None
voskRecognizer = None

def startListening():
    global listeningActive, mic, stream, voskRecognizer
    if not vosk_model:
        text_area.insert(tk.END, "\n Error: Vosk model could not be loaded!\n")
        return
    if not listeningActive:
        root.update()
        mic = pyaudio.PyAudio()
        stream = mic.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4096)
        stream.start_stream()
        voskRecognizer = KaldiRecognizer(vosk_model, 16000)
        listeningActive = True
        root.after(100, listeningLoop)
    else:
        root.update()
        if stream:
            stream.stop_stream()
            stream.close()
        if mic:
            mic.terminate()
        listeningActive = False

def listeningLoop():
    global listeningActive, stream, voskRecognizer
    if not listeningActive:
        return
    data = stream.read(4096, exception_on_overflow=False)
    if voskRecognizer.AcceptWaveform(data):
        result = json.loads(voskRecognizer.Result())
        text = result["text"]
        if text.strip():
            text_area.insert(tk.END, text + " ")
            root.update()
    root.after(100, listeningLoop)

def summarizeText():
    text = text_area.get("1.0", tk.END).strip()
    if len(text) < 50:
        text_area.insert(tk.END, "\n Not enough data for summary!\n")
        return
    text_area.delete("1.0", tk.END)
    text_area.insert(tk.END, "\n Summarizing...\n")
    text_area.delete("1.0", tk.END)
    root.update()
    
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(f"Summarize this text, ignore the 'Listening started' and 'Listening stopped' commands, if the text is not English, summarize it in that language, DO NOT USE ANY FORMATTING, JUST USE PLAIN TEXT: {text}")
        summary = response.text
        text_area.delete("1.0", tk.END)
        text_area.insert(tk.END, f"\n{summary}\n")
    except Exception as e:
        text_area.insert(tk.END, f"\n Error: {str(e)}\n")

def clearText():
    text_area.delete("1.0", tk.END)

def readTextAloud():
    text = text_area.get("1.0", tk.END).strip()
    if text:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()

button_frame = ttk.Frame(root)
button_frame.place(relx=0.5, rely=0.9, anchor="s")

btnStart = ttk.Button(button_frame, text=" Start / Stop Listening ", command=startListening)
btnStart.grid(row=0, column=0, padx=10)
btnSummarize = ttk.Button(button_frame, text=" Summarize ", command=summarizeText)
btnSummarize.grid(row=0, column=1, padx=10)

btnClear = ttk.Button(button_frame, text=" Clear Text ", command=clearText)
btnClear.grid(row=1, column=0, padx=10, pady=10)

btnRead = ttk.Button(button_frame, text=" Read Text ", command=readTextAloud)
btnRead.grid(row=1, column=1, padx=10, pady=10)

sv_ttk.set_theme("dark")
applyTitleBarTheme(root)
root.mainloop()
