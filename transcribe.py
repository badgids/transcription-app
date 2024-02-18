import argparse
import numpy as np
import speech_recognition as sr
import whisper
import torch
import pyautogui
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from queue import Queue
from threading import Thread
from time import sleep
import sys


class TranscriptionApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Whisper Transcription App")
        self.master.geometry("350x175")  # Set initial window size
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)  # Bind close event to on_close method

        # Center window on screen
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x = (screen_width - 300) // 2
        y = (screen_height - 175) // 2
        self.master.geometry("+{}+{}".format(x, y))

        # Create a frame for flexible resizing
        main_frame = tk.Frame(self.master)
        main_frame.pack(fill="both", expand=True)

        self.create_microphone_selection(main_frame)
        self.create_model_selection(main_frame)

        self.transcription_in_progress = False
        self.transcription_thread = None  # Initialize transcription thread variable
        self.stop_transcription_flag = False  # Flag to signal transcription thread to stop

        self.loading_label = tk.Label(main_frame, text="", font=("Arial", 12, "bold"), fg="black")
        self.loading_label.pack(pady=10)

        self.pin_button = tk.Button(self.master, text="📌", command=self.toggle_pin)
        self.pin_button.place(relx=1, rely=0, anchor="ne")

        self.start_button = tk.Button(main_frame, text="Start Transcription", command=self.toggle_transcription)
        self.start_button.pack(pady=10)

    def create_microphone_selection(self, frame):
        mic_frame = tk.Frame(frame)
        mic_frame.pack(pady=10)

        mic_label = tk.Label(mic_frame, text="Select Microphone:")
        mic_label.grid(row=0, column=0, padx=10)

        self.mic_var = tk.StringVar()
        mic_options = sr.Microphone.list_microphone_names()
        self.mic_dropdown = ttk.Combobox(mic_frame, textvariable=self.mic_var, values=mic_options, state="readonly")
        self.mic_dropdown.current(0)  # Set default value
        self.mic_dropdown.grid(row=0, column=1)

    def create_model_selection(self, frame):
        model_frame = tk.Frame(frame)
        model_frame.pack(pady=10)

        model_label = tk.Label(model_frame, text="Select Model:")
        model_label.grid(row=0, column=0, padx=10)

        self.model_var = tk.StringVar()
        model_options = ["tiny", "base", "small", "medium", "large"]
        self.model_dropdown = ttk.Combobox(model_frame, textvariable=self.model_var, values=model_options, state="readonly")
        self.model_dropdown.current(3)  # Set default value to "medium"
        self.model_dropdown.grid(row=0, column=1)

    def toggle_transcription(self):
        if not self.transcription_in_progress:
            self.start_button.config(text="Stop Transcription")
            self.transcription_in_progress = True
            self.stop_transcription_flag = False  # Reset stop transcription flag
            self.loading_label.config(text="Loading Model...", fg="black")
            self.transcription_thread = Thread(target=self.start_transcription)
            self.transcription_thread.start()  # Start transcription thread
        else:
            self.start_button.config(text="Start Transcription")
            self.transcription_in_progress = False
            self.stop_transcription_flag = True  # Set stop transcription flag
            self.loading_label.config(text="Transcribing Stopped", fg="red")

    def toggle_pin(self):
        if self.master.attributes('-topmost'):
            self.master.attributes('-topmost', False)
            self.pin_button.config(text="📌")
        else:
            self.master.attributes('-topmost', True)
            self.pin_button.config(text="🔴")

    def start_transcription(self):
        model = self.model_var.get()
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
        self.loading_label.config(text="Transcribing", fg="green")

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

        self.start_button.config(text="Start Transcription")  # Reset button text
        self.transcription_in_progress = False

    def on_close(self):
        self.stop_transcription_flag = True  # Set stop transcription flag
        self.master.destroy()  # Destroy tkinter window


def main():
    root = tk.Tk()
    app = TranscriptionApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()