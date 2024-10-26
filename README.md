# DJ Screwdriver 🎚️

A Python-based audio manipulation tool that lets you experiment with track speeds, pitches, and beat-synchronized effects using different algorithms. Perfect for creating remixes, vaporwave-style edits, rhythmic chops, or any creative audio experiments. Explore interesting audio artifacts through iterative processing, spectral manipulation, and beat-synchronized effects.

## ✨ Features

- Process local audio files or download directly from YouTube
- Automatic BPM detection and matching for rhythm-synchronized effects
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

## 💫 Usage

```bash
# Interactive mode
python main.py

# Direct file processing
python main.py input.mp3 "p:-2;rt:0.8;"

# YouTube processing
python main.py https://youtube.com/watch?v=... "bpm:128;stut:2:1:2;"
```

### Playback Controls
- **Space**: Play/Pause
- **Up Arrow**: Restart playback
- **Left Arrow**: Undo last operation
- **Right Arrow**: Redo operation
- **Enter**: Execute command
- **s;**: Save current version
- **q;**: Exit program

## 🎮 Command Reference

Each command follows the syntax: `command:value1:value2:value3;`

### Basic Operations
```
p:X;              # Pitch shift (semitones)
t:X;              # Time stretch (rate)
rt:X;             # Resample time stretch (rate)
r:X;              # Resample (rate)
bpm:X;            # Match to target BPM
```

### Beat-Synchronized Effects

#### Loop Effect (loop:interval:length:repeat;)
Creates repeating loop patterns
```bash
loop:1:8:4;       # Create loops every beat, 8 beats long, repeat every 4 beats
```
- interval: Create loop every N beats
- length: Number of beats to loop
- repeat: Pattern repeats every N beats

#### Chop Effect (chop:size:step:repeat;)
Chops and rearranges audio in beat-sized chunks
```bash
chop:1:4:2;       # 1-beat chunks, 4-beat steps, repeat every 2 beats
```
- size: Length of each chunk in beats
- step: Distance between chops
- repeat: Pattern repeats every N beats

#### Stutter Effect (stut:count:length:repeat;)
Creates rapid repetitions of beat segments
```bash
stut:2:1:2;       # 2 stutters per beat, 1 beat long, repeat every 2 beats
```
- count: Number of stutters per beat
- length: Length of stutter section
- repeat: Pattern repeats every N beats

#### Echo Effect (echo:delay:count:decay;)
Adds tempo-synchronized echoes
```bash
echo:0.2:3:0.7;   # 200ms delay, 3 echoes, 0.7 decay rate
```
- delay: Time between echoes (seconds)
- count: Number of echo repeats
- decay: Volume reduction per echo (0-1)

#### Reverse Effect (rev:interval:length:repeat;)
Reverses audio in beat-synchronized chunks
```bash
rev:1:4:2;        # Reverse every beat, 4 beats long, repeat every 2 beats
```
- interval: Apply reverse every N beats
- length: Length of reversed section
- repeat: Pattern repeats every N beats

#### Mash Effect (mash:parts:beats:repeat;)
Randomly mixes beat segments
```bash
mash:4:2:4;       # Mix 4 parts every 2 beats, repeat every 4 beats
```
- parts: Number of segments to mix
- beats: Beat length to process
- repeat: Pattern repeats every N beats

## 🎵 Creative Examples

### Genre Transformations

```bash
# Vaporwave
p:-5;rt:0.8;echo:0.3:3:0.7;loop:2:8:4;

# Drill Beat
bpm:140;stut:3:1:3;echo:0.1:4:0.9;loop:2:4:2;

# DnB Rhythm
bpm:174;chop:1:2:2;loop:2:8:4;stut:2:1:2;
```

### Sound Design

```bash
# Ghost Texture
rt:0.25;p:-24;echo:0.4:8:0.99;rt:4.0;p:24;

# Granular Cloud
stut:16:1:1;echo:0.01:32:0.999;mash:8:1:1;

# Time Crystal
chop:1:1:1;stut:8:1:2;echo:0.05:16:0.99;
```

### Common Techniques

#### Enhance Loudness
```bash
stut:4:1:2;echo:0.05:8:0.95;  # Stack amplitudes with tight timing
```

#### Create Complex Rhythm
```bash
chop:1:4:2;rev:2:4:2;loop:2:8:4;  # Chop, reverse, and loop for patterns
```

#### Transform Character
```bash
p:12;stut:4:1:1;echo:0.05:8:0.95;p:-12;  # Process harmonics then restore
```

## 🔬 Technical Details

- Uses FFT-based analysis to maintain spectral characteristics
- Implements spectrogram matching for frequency preservation
- Preserves original loudness levels through RMS matching
- Creates unique artifacts through multiple processing iterations
- Beat-synchronized effects for musically coherent modifications
- Crossfading between modified sections for smooth transitions

## ⚠️ Best Practices

1. Process Order
```bash
bpm:128;          # Global tempo first
p:-2;             # Then pitch
rt:0.9;           # Then time stretching
loop:2:8:4;       # Then beat effects
echo:0.2:3:0.7;   # Then details
```

2. Save Frequently
```bash
effect:value;     # Test single effect
s;               # Save if good
```

3. Rate Values
- 1.0 = original speed/pitch
- 2.0 = double speed/higher pitch
- 0.5 = half speed/lower pitch

## 📝 License

[Your license information here]