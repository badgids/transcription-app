# Transcription App

This is a transcription application that listens to audio input from the microphone using OpenAI's Whisper, transcribes it into text, and simulates typing the transcription in real-time wherever your cursor is on the screen.

# Table of Contents

- [Transcription App](#transcription-app)
- [Table of Contents](#table-of-contents)
  - [Installation](#installation)
    - [Using Conda (Recommended)](#using-conda-recommended)
      - [Windows](#windows)
        - [One-Click Install (Windows Only)](#one-click-install-windows-only)
      - [Linux and Mac](#linux-and-mac)
  - [Usage](#usage)
  - [Troubleshooting](#troubleshooting)
  - [Contributing](#contributing)
  - [License](#license)

## Installation

### Using Conda (Recommended)

#### Windows

1. Install Miniconda or Anaconda if you haven't already. You can download Miniconda from [here](https://docs.conda.io/en/latest/miniconda.html).

2. Clone this repository to your local machine:
   ```bash
   git clone https://github.com/badgids/transcription-app.git
   ```

3. Navigate to the project directory:
   ```bash
   cd transcription-app
   ```

4. Create a conda environment and install the required packages:
   ```bash
   conda create -n transcribe python=3.10
   ```

5. Activate the conda environment:
   ```bash
   conda activate transcribe
   ```

6. Install additional requirements:
   ```bash
   pip install -r requirements.txt
   ```

7. Run the program:
   ```bash
   python transcribe.py
   ```

##### One-Click Install (Windows Only)

1. If you don't have Miniconda or Anaconda installed, download and run the `install.bat` file from the project's root directory. Follow the on-screen instructions to install Miniconda and set up the environment.

2. Once Miniconda is installed, double-click the `start.bat` file to activate the environment and run the program.

#### Linux and Mac

1. Follow steps 2-5 above for Windows.

2. Install additional requirements:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the program:
   ```bash
   python transcribe.py
   ```

## Usage

- Upon running the program, a GUI window will appear.
- Select your microphone from the dropdown menu.
- Choose the model size (tiny, base, small, medium, large) for transcription.
- Click the "Start Transcription" button to begin transcription.
- The program will transcribe the audio input from the microphone in real-time and simulate typing the transcription wherever your cursor is on the screen.

## Troubleshooting

- If you encounter any issues with the installation or running the program, please [open an issue](https://github.com/badgids/transcription-app/issues) on GitHub.

## Contributing

Contributions are welcome! If you find any bugs or have suggestions for improvement, please [open a pull request](https://github.com/badgids/transcription-app/pulls) or [create an issue](https://github.com/badgids/transcription-app/issues) on GitHub.

## License

This project is licensed under the [MIT License](LICENSE).