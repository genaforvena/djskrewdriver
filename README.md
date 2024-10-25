# DJ Screwdriver 🎚️

A Python-based audio manipulation tool that lets you experiment with track speeds, pitches, and beat-synchronized effects using different algorithms. Perfect for creating remixes, vaporwave-style edits, rhythmic chops, or any creative audio experiments. Explore interesting audio artifacts through iterative processing, spectral manipulation, and beat-synchronized effects.

## ✨ Features

- Process local audio files or download directly from YouTube
- Automatic BPM detection for rhythm-synchronized effects
- Multiple audio manipulation algorithms:
  - Pitch shifting (semitone-based adjustment using librosa.effects.pitch_shift)
  - Time stretching (using either librosa.effects.time_stretch or resampling method)
  - Resampling (classic speed change using librosa.resample)
  - Beat-synchronized effects (looping, chopping, stutters, echoes)
- Chain multiple operations in sequence
- Automatic output in both WAV and MP3 formats
- Timestamped output files for easy organization
- FFT-based frequency characteristic preservation
- Original loudness level matching
- Unique audio artifacts through iterative processing

## 🎮 Command Syntax

Structure your audio manipulation instructions using this syntax:
```
command:value1:value2:value3;
```
Each command can have up to three values that control different aspects of the effect. All commands must end with a semicolon (;).

### Basic Operations:
- `p:X;` - Shift pitch by X semitones
- `t:X;` - Time stretch with rate X using librosa.effects.time_stretch
- `rt:X;` - Time stretch with rate X using resampling method
- `r:X;` - Resample with rate X (affects both time and pitch)

### Beat-Synchronized Effects:

- **Loop (`loop:X:Y:Z;`)**
  - X: Interval between loops (beats)
  - Y: Length of each loop (beats)
  - Z: Pattern repeat interval (beats)
  - Example: `loop:1:12:2;` = Create loops every 1 beat, 12 beats long, repeating every 2 beats

- **Chop (`chop:X:Y:Z;`)**
  - X: Length of each chunk (beats)
  - Y: Step size between chunks (beats)
  - Z: Pattern repeat interval (beats)
  - Example: `chop:2:12:4;` = 2-beat chunks, 12-beat step size, repeat every 4 beats

- **Reverse (`rev:X:Y:Z;`)**
  - X: Interval between reversals (beats)
  - Y: Length of reversed section (beats)
  - Z: Pattern repeat interval (beats)
  - Example: `rev:1:12:3;` = Reverse every 1 beat, 12 beats per reversal, repeat every 3 beats

- **Stutter (`stut:X:Y:Z;`)**
  - X: Stutters per beat
  - Y: Stutter length (beats)
  - Z: Pattern repeat interval (beats)
  - Example: `stut:2:1:4;` = 2 stutters per beat, 1 beat long, repeat every 4 beats

- **Echo (`echo:X:Y:Z;`)**
  - X: Delay time (seconds, 0 = auto)
  - Y: Number of echoes
  - Z: Echo decay rate
  - Example: `echo:0.3:3:0.5;` = 300ms delay, 3 echoes, 0.5 decay rate

For rate values:
- 1.0 = original speed/pitch
- 2.0 = double speed/higher pitch
- 0.5 = half speed/lower pitch

## 🎵 Example Commands

1. Create layered beat-synchronized effects:
```bash
loop:1:8:2;chop:2:4:1;echo:0.3:3:0.5;
```
This will:
- Create 8-beat loops every beat, repeating every 2 beats
- Chop into 2-beat chunks with 4-beat steps
- Add echo with 300ms delay, 3 echoes, and 0.5 decay

2. Create complex rhythmic patterns:
```bash
rev:1:4:2;stut:2:1:4;loop:2:8:4;
```
This will:
- Reverse every beat for 4 beats, repeating every 2 beats
- Add 2 stutters per beat, 1 beat long, every 4 beats
- Create 8-beat loops every 2 beats, repeating every 4 beats

3. Classic vaporwave effect with modern twist:
```bash
p:-5;rt:0.8;loop:2:16:4;echo:0.2:4:0.6;
```
This will:
- Lower pitch by 5 semitones
- Slow down to 80% speed
- Create 16-beat loops every 2 beats, repeating every 4 beats
- Add echoes with 200ms delay, 4 echoes, and 0.6 decay

## 🔬 Technical Details

- Automatic BPM detection for rhythmically coherent effects
- Uses FFT-based analysis to maintain spectral characteristics
- Implements spectrogram matching for frequency preservation
- Preserves original loudness levels through RMS matching
- Creates unique artifacts through multiple processing iterations
- Beat-synchronized effects for musically coherent modifications
- Crossfading between modified sections for smooth transitions
- Perfect for experimental sound design and audio research

## 💫 Usage

Interactive mode:
```bash
python main.py
```

Direct file processing:
```bash
python main.py path/to/your/audio.mp3
```

YouTube processing:
```bash
python main.py https://youtube.com/watch?v=...
```

Then type your commands in the interactive prompt, ending each with a semicolon (;).
Use space to play/pause, arrow keys to navigate history, and 's;' to save.

## 📝 License

[Your license information here]