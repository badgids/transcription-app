import argparse
import json
import numpy as np
import os
import speech_recognition as sr
import whisper
import torch
import pyautogui
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from datetime import datetime, timedelta
from queue import Queue
from threading import Thread
from time import sleep
from transformers import MarianMTModel, MarianTokenizer
from PIL import Image

class Translator:
    def __init__(self, source_lang: str, dest_lang: str) -> None:
        self.model_name = f'Helsinki-NLP/opus-mt-{source_lang}-{dest_lang}'
        self.model = MarianMTModel.from_pretrained(self.model_name)
        self.tokenizer = MarianTokenizer.from_pretrained(self.model_name)

    def translate(self, texts):
        tokens = self.tokenizer(list(texts), return_tensors="pt", padding=True)
        translate_tokens = self.model.generate(**tokens)
        return [self.tokenizer.decode(t, skip_special_tokens=True) for t in translate_tokens]

class TranscriptionApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Whisper Transcription App")
        self.master.iconbitmap('assets/images/appIcon.ico')
        self.master.geometry("400x275")  # Set initial window size
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)  # Bind close event to on_close method

        # Define icons for pin button
        self.unpinned_icon = ctk.CTkImage(Image.open('assets/images/unpinned.png'), size=(24,24))
        self.pinned_icon = ctk.CTkImage(Image.open('assets/images/pinned.png'), size=(24,24))
        
        # Center window on screen
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 275) // 2
        self.master.geometry("+{}+{}".format(x, y))

        # Create a frame for flexible resizing
        main_frame = ctk.CTkFrame(self.master)
        main_frame.pack(fill="both", expand=True)

        self.create_microphone_selection(main_frame)
        self.create_model_selection(main_frame)
        self.create_translation_options(main_frame)

        self.transcription_in_progress = False
        self.transcription_thread = None  # Initialize transcription thread variable
        self.stop_transcription_flag = False  # Flag to signal transcription thread to stop
        self.translation_active = False  # Flag to indicate if translation is active
        self.translator = None  # Initialize translator object

        self.loading_label = ctk.CTkLabel(main_frame, text="", font=("Arial", 12, "bold"), fg_color="transparent")
        self.loading_label.pack(pady=10)

        self.pin_button = ctk.CTkButton(self.master, text='', image=self.unpinned_icon, command=self.toggle_pin, width=20, corner_radius=0, bg_color="transparent", fg_color="transparent")
        self.pin_button.place(relx=1, rely=0, anchor="ne")

        self.start_button = ctk.CTkButton(main_frame, text="Start Transcription", command=self.toggle_transcription)
        self.start_button.pack(pady=10)

    def create_microphone_selection(self, frame):
        mic_frame = ctk.CTkFrame(frame)
        mic_frame.pack(pady=10)

        mic_label = ctk.CTkLabel(mic_frame, text="Select Microphone:")
        mic_label.grid(row=0, column=0, padx=10)

        self.mic_var = ctk.StringVar()
        mic_options = sr.Microphone.list_microphone_names()
        self.mic_dropdown = ctk.CTkComboBox(mic_frame, variable=self.mic_var, values=mic_options, state="readonly")
        self.mic_dropdown.set(mic_options[0])  # Set default value mic selection
        self.mic_dropdown.grid(row=0, column=1)

    def create_model_selection(self, frame):
        model_frame = ctk.CTkFrame(frame)
        model_frame.pack(pady=10)

        model_label = ctk.CTkLabel(model_frame, text="Select Model:")
        model_label.grid(row=0, column=0, padx=10)

        self.model_var = ctk.StringVar()
        model_options = ['Tiny', 'Base', 'Small', 'Medium', 'Large']
        self.model_dropdown = ctk.CTkComboBox(model_frame, variable=self.model_var, values=model_options, state="readonly")
        self.model_dropdown.set(model_options[3])  # Set default value to "medium"
        self.model_dropdown.grid(row=0, column=1)

    def create_translation_options(self, frame):
        translation_frame = ctk.CTkFrame(frame)
        translation_frame.pack(pady=10)

        self.translation_checkbox_var = ctk.BooleanVar()
        self.translation_checkbox = ctk.CTkCheckBox(translation_frame, text="Translate to Language:", variable=self.translation_checkbox_var, command=self.toggle_translation)
        self.translation_checkbox.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.translate_label = ctk.CTkLabel(translation_frame, text="Translate to Language:")
        self.translate_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.translate_label.grid_remove()
        self.languages = {
            "Spanish": "es",
            "French": "fr",
            "German": "de",
            "Dutch": "nl",
            "Japanese": "jap"
            }
        self.translate_var = ctk.StringVar()
        self.translate_dropdown = ctk.CTkComboBox(translation_frame, variable=self.translate_var, state="disabled")
        self.translate_dropdown.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        self.translate_dropdown.grid_remove()

    def toggle_translation(self):
        self.translation_active = self.translation_checkbox_var.get()
        if self.translation_active:
            self.translate_label.grid()
            self.translate_dropdown.grid()
            self.translate_dropdown.configure(values=list(self.languages.keys()), state="readonly")
            self.translate_var.set(list(self.languages.keys())[0])  # Set default translation language to Spanish
        else:
            self.translate_label.grid_remove()
            self.translate_dropdown.grid_remove()

    def load_translator_model(self, source_lang, dest_lang):
        self.translator = Translator(source_lang, dest_lang)

    def toggle_transcription(self):
        if not self.transcription_in_progress:
            self.master.iconbitmap('assets/images/appIcon_recording.ico') #set app icon to show recording emblem
            self.start_button.configure(text="Stop Transcription")
            self.transcription_in_progress = True
            self.stop_transcription_flag = False  # Reset stop transcription flag
            self.loading_label.configure(text="Loading Model...", fg_color="black", corner_radius=5)
            self.transcription_thread = Thread(target=self.start_transcription)
            self.transcription_thread.start()  # Start transcription thread
        else:
            self.master.iconbitmap('assets/images/appIcon.ico') #set app icon to remove recording emblem
            self.start_button.configure(text="Start Transcription")
            self.transcription_in_progress = False
            self.stop_transcription_flag = True  # Set stop transcription flag
            self.loading_label.configure(text="Transcribing Stopped", fg_color="red", corner_radius=5)

    def toggle_pin(self):
        if self.master.attributes('-topmost'):
            self.master.attributes('-topmost', False)
            self.pin_button.configure(image=self.unpinned_icon )
        else:
            self.master.attributes('-topmost', True)
            self.pin_button.configure(image=self.pinned_icon)

    def start_transcription(self):
        model = self.model_var.get().lower()
        mic_index = sr.Microphone.list_microphone_names().index(self.mic_var.get())
        selected_mic_name = sr.Microphone.list_microphone_names()[mic_index]

        # The last time a recording was retrieved from the queue.
        phrase_time = None
        # Thread safe Queue for passing data from the threaded recording callback.
        data_queue = Queue()
        # We use SpeechRecognizer to record our audio because it has a nice feature where it can detect when speech ends.
        recorder = sr.Recognizer()
        recorder.energy_threshold = 1000
        # Definitely do this, dynamic energy compensation lowers the energy threshold dramatically to a point where the SpeechRecognizer never stops recording.
        recorder.dynamic_energy_threshold = False

        # Microphone source
        source = sr.Microphone(sample_rate=16000, device_index=mic_index)

        # Load / Download model
        if model != "large":
            model = model + ".en"
        audio_model = whisper.load_model(model)

        record_timeout = 2
        phrase_timeout = 3

        print(f"\nSelected microphone: {selected_mic_name}\n")
        print("Model loaded.\n")

        # Update the loading label to show "Transcribing"
        self.loading_label.configure(text="Transcribing", fg_color="green", corner_radius=5)

        with source:
            recorder.adjust_for_ambient_noise(source)

        def record_callback(_, audio: sr.AudioData) -> None:
            """
            Threaded callback function to receive audio data when recordings finish.
            audio: An AudioData containing the recorded bytes.
            """
            # Grab the raw bytes and push it into the thread safe queue.
            data = audio.get_raw_data()
            data_queue.put(data)

        # Create a background thread that will pass us raw audio bytes.
        # We could do this manually but SpeechRecognizer provides a nice helper.
        recorder.listen_in_background(source, record_callback, phrase_time_limit=record_timeout)

        transcription = []  # Initialize transcription list

        while True:
            try:
                now = datetime.utcnow()
                # Pull raw recorded audio from the queue.
                if not data_queue.empty():
                    phrase_complete = False
                    # If enough time has passed between recordings, consider the phrase complete.
                    # Clear the current working audio buffer to start over with the new data.
                    if phrase_time and now - phrase_time > timedelta(seconds=phrase_timeout):
                        phrase_complete = True
                    # This is the last time we received new audio data from the queue.
                    phrase_time = now

                    # Combine audio data from queue
                    audio_data = b''.join(data_queue.queue)
                    data_queue.queue.clear()

                    # Convert in-ram buffer to something the model can use directly without needing a temp file.
                    # Convert data from 16 bit wide integers to floating point with a width of 32 bits.
                    # Clamp the audio stream frequency to a PCM wavelength compatible default of 32768hz max.
                    audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

                    # Read the transcription.
                    result = audio_model.transcribe(audio_np, fp16=torch.cuda.is_available())
                    text = result['text'].strip()

                    # If translation is active, translate the text
                    if self.translation_active:
                        translation_lang = self.languages[self.translate_var.get()]
                        self.load_translator_model('en', translation_lang)
                        text = self.translator.translate([text])[0]

                    # If we detected a pause between recordings, add a new item to our transcription.
                    # Otherwise, append the new transcription.
                    if phrase_complete:
                        transcription.append(text)
                        print(text, end=" ")  # Add a space after every complete phrase
                    else:
                        if transcription:  # Check if transcription list is not empty
                            transcription[-1] = text
                        else:
                            transcription.append(text)

                    # Simulate typing the transcription wherever the cursor is
                    pyautogui.typewrite(text + " ")  # Add a space after every complete phrase

                    # Infinite loops are bad for processors, must sleep.
                    sleep(0.25)
            except KeyboardInterrupt:
                break

            if self.stop_transcription_flag:  # Check if stop transcription flag is set
                break  # Exit transcription loop

        print("\n\nTranscription:")
        for line in transcription:
            print(line)

        self.start_button.configure(text="Start Transcription")  # Reset button text
        self.transcription_in_progress = False

    def on_close(self):
        self.stop_transcription_flag = True  # Set stop transcription flag
        self.master.destroy()  # Destroy tkinter window

def main():
    ctk.set_appearance_mode("System")  # Modes: system (default), light, dark
    ctk.set_default_color_theme("dark-blue")  # Themes: blue (default), dark-blue, green

    root = ctk.CTk()
    app = TranscriptionApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
