DJ Screwdriver 👻

A real-time audio manipulation tool designed for live performance and creative sound design. Perfect for DJs, producers, and sound artists looking to create unique remixes, transitions, and audio effects on the fly. Transform tracks with beat-synchronized effects, pitch/time manipulation, and experimental processing chains.
🚀 Installation

Ensure Python 3.8+ is installed
Install required libraries:

bashCopypip install librosa soundfile numpy sounddevice keyboard pydub

Clone the repository:

bashCopygit clone https://github.com/yourusername/djscrewdriver.git
cd djscrewdriver
✨ Features

Real-time playback control with instant effect preview
Process local audio files or download directly from YouTube
Beat-synchronized effects with automatic BPM detection
Multiple audio manipulation algorithms:

Pitch shifting using librosa.effects.pitch_shift
Time stretching using librosa.effects.time_stretch or resampling
Beat-synchronized effects (loops, chops, stutters, echoes)


Non-destructive processing with instant undo/redo
Automatic output in both WAV and MP3 formats
FFT-based frequency characteristic preservation


Important Note About Loudness: DJ Screwdriver focuses on time and pitch manipulation rather than volume control. This is because DJs typically control volume through their mixer/audio interface, while timing and pitch effects require specialized audio processing. Use your DJ mixer or audio interface for volume control, and DJ Screwdriver for creative sound manipulation.

💫 Usage
bashCopy# Interactive mode
python main.py

# Direct file processing
python main.py input.mp3 "p:-2;rt:0.8;"

# YouTube processing
python main.py https://youtube.com/watch?v=... "bpm:128;stut:2:1:2;"
Live Controls

Space: Play/Pause (instant response)
Up Arrow: Reset to Start
Left/Right Arrows: Undo/Redo Effect
Enter: Execute Effect
s;: Save Current State
q;: Exit Program

🎮 Effect Reference
Each command executes immediately using syntax: command:value1:value2:value3;
Basic Operations
Copyp:X;              # Pitch shift (semitones)
t:X;              # Time stretch (rate)
rt:X;             # Resample time stretch (rate)
r:X;              # Resample (rate)
bpm:X;            # Match to target BPM
Beat-Synchronized Effects
Loop Effect (loop:interval:length:repeat;)
bashCopyloop:1:8:4;       # Create loops every beat, 8 beats long, repeat every 4 beats
[Rest of the effects documentation remains the same...]
🎵 Performance Techniques
Quick Transitions
bashCopy# Energy build
stut:4:1:2;echo:0.1:4:0.9;

# Break down
rt:0.5;p:-12;echo:0.3:4:0.95;

# Drop prep
chop:1:4:2;rev:1:2:1;
Live Effect Layering
bashCopy# Layer 1: Rhythm
stut:2:1:2;
s;  # Save state

# Layer 2: Space
echo:0.2:3:0.7;
s;  # Save state

# Layer 3: Texture
mash:4:1:2;
s;  # Save state
Tempo Matching
bashCopy# Match tempos for smooth transition
bpm:128;          # House
bpm:174;          # DnB
bpm:140;          # Trap
🎯 Performance Tips

Prepare Your Set

Test effects combinations beforehand
Practice common transitions
Know your escape routes (undo)


During Performance

Build effects gradually
Save reliable states
Keep rhythm coherent
Monitor your output through the mixer


Effect Combinations

Start simple, add complexity
Stack compatible effects
Use your mixer's EQ with effects
Build and release intensity



🔧 Technical Details

Zero-latency playback system
Real-time effect processing
Non-destructive audio manipulation
State preservation system
FFT-based processing
Automatic beat detection

⚠️ Best Practices

Process Order

bashCopybpm:128;          # Global tempo first
p:-2;             # Then pitch
rt:0.9;           # Then time stretching
loop:2:8:4;       # Then beat effects
echo:0.2:3:0.7;   # Then details

Rate Values


1.0 = original speed/pitch
2.0 = double speed/higher pitch
0.5 = half speed/lower pitch

🔌 Integration Tips

Use with any DJ mixer/interface
Control volume through your mixer
Effects chain into mixer channel
Process tracks before your set
Create preprocessed versions
Save states for quick recall

📝 License
[Your license information here]