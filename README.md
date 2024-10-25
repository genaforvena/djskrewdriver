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

## 🎨 Creative Effects

### 🌀 Iterative Processing
- Each processing cycle introduces unique audio characteristics
- Multiple iterations can create fascinating sound textures
- Experiment with repeated stretch/compress cycles for interesting artifacts
- For example, stretching to 2x length and compressing back creates subtle but noticeable effects

### 🎵 Beat-Synchronized Effects
- Automatic BPM detection for musically coherent modifications
- Beat-aligned loops and chops
- Rhythmic stutter effects
- Beat-synchronized echoes and reverses

### 🎯 Spectral Manipulation
- FFT-based processing preserves original frequency characteristics
- Spectrogram analysis ensures consistent sound quality
- Maintains core audio features while allowing creative manipulation
- Perfect for experimental sound design and texture creation

[Installation section remains the same...]

## 💫 Usage

Run the script in any of these ways:

```bash
# Interactive mode
python main.py

# Direct file processing
python main.py path/to/your/audio.mp3 "p:2;loop:4;chop:2;"

# YouTube processing
python main.py https://youtube.com/watch?v=... "stut:1;echo:0;"
```

### 🎮 Command Syntax

Structure your audio manipulation instructions using this syntax:

Basic Operations:
- `p:X;` - Shift pitch by X semitones (any positive or negative number)
- `t:X;` - Time stretch with rate X using librosa.effects.time_stretch
- `rt:X;` - Time stretch with rate X using resampling method
- `r:X;` - Resample with rate X (affects both time and pitch)

Beat-Synchronized Effects:
- `loop:X;` - Create loops of X beats (default: 4 beats if X=0)
- `chop:X;` - Chop and rearrange in X-beat chunks (default: 2 beats)
- `stut:X;` - Add stutter effect with X stutters per beat (default: 1)
- `echo:X;` - Add echo with X seconds delay (uses beat length if X=0)
- `rev:X;` - Reverse audio in X-beat chunks (default: 4 beats)

For rate values:
- 1.0 = original speed
- 2.0 = double speed
- 0.5 = half speed

Commands can be chained together and will be applied in sequence.

Example:
```bash
p:2;loop:4;chop:2;echo:0;
```
This will:
1. Shift pitch up by 2 semitones
2. Create 4-beat loops
3. Chop and rearrange in 2-beat chunks
4. Add beat-synchronized echo

[Output section remains the same...]

## 🎵 Examples

1. Create a classic vaporwave effect with beat-synchronized loops:
   ```bash
   python main.py song.mp3 "p:-5;rt:0.8;loop:4;"
   ```

2. Create a rhythmic chopped effect:
   ```bash
   python main.py song.mp3 "chop:2;stut:1;"
   ```

3. Create complex beat-synchronized patterns:
   ```bash
   python main.py song.mp3 "loop:8;chop:2;echo:0;"
   ```

4. Create interesting artifacts with beat-synced effects:
   ```bash
   python main.py song.mp3 "rev:4;stut:2;echo:0.3;"
   ```

## 🎯 Command Effects Guide

[Previous pitch shift, time stretch, and resample sections remain the same...]

Beat-Synchronized Effects:

- **Loop (`loop`)**: Creates beat-synchronized loops
  - Values are number of beats per loop
  - `loop:4;` = 4-beat loop
  - `loop:0;` = Default 4-beat loop
  - Uses crossfading for smooth transitions

- **Chop (`chop`)**: Chops and rearranges audio in beat-sized chunks
  - Values are beats per chunk
  - `chop:2;` = 2-beat chunks
  - Creates interesting rhythmic patterns
  - Maintains musical coherence

- **Stutter (`stut`)**: Adds beat-synchronized stutter effect
  - Values are stutters per beat
  - `stut:1;` = One stutter per beat
  - `stut:2;` = Two stutters per beat
  - Uses fade envelopes for clean transitions

- **Echo (`echo`)**: Adds beat-synchronized echo
  - Values are delay time in seconds
  - `echo:0;` = Uses one beat length as delay
  - `echo:0.3;` = 300ms delay
  - Multiple echoes with decreasing volume

- **Reverse (`rev`)**: Reverses audio in beat-synchronized chunks
  - Values are beats per reversed chunk
  - `rev:4;` = Reverse every 4 beats
  - Uses crossfading for smooth transitions

## 🔬 Technical Details

- Automatic BPM detection for rhythmically coherent effects
- Uses FFT-based analysis to maintain spectral characteristics
- Implements spectrogram matching for frequency preservation
- Preserves