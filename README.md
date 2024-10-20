# Audio Speed Changer

This Python script allows you to change the speed of audio files with or without preserving pitch. It uses a custom syntax for specifying the speed changes.

## Installation

1. Clone this repository:
   ```
   gh repo clone YourUsername/audio-speed-changer
   cd audio-speed-changer
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

Run the script:

```
python audio_processor.py
```

Follow the prompts to enter the path to your audio file and the instructions for processing.

### Instruction Syntax

- `SPEED:<percentage>:PITCH;` to speed up while preserving pitch
- `SPEED:<percentage>:NOPITCH;` to speed up without preserving pitch
- `SLOW:<percentage>:PITCH;` to slow down while preserving pitch
- `SLOW:<percentage>:NOPITCH;` to slow down without preserving pitch

Example: `SLOW:10:PITCH;SPEED:20:NOPITCH;`

This will first slow down the audio by 10% while preserving pitch, then speed it up by 20% without preserving pitch.
