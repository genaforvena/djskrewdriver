# DJ Screwdriver 🎚️

A Python-based audio manipulation tool that lets you experiment with track speeds and pitches using different algorithms. Perfect for creating remixes, vaporwave-style edits, or any creative audio experiments.

## ✨ Features

- Process local audio files or download directly from YouTube
- Multiple audio manipulation algorithms:
  - Pitch shifting (semitone-based adjustment using librosa.effects.pitch_shift)
  - Time stretching (using either librosa.effects.time_stretch or resampling method)
  - Resampling (classic speed change using librosa.resample)
- Chain multiple operations in sequence
- Automatic output in both WAV and MP3 formats
- Timestamped output files for easy organization

## 🚀 Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/genaforvena/djskrewdriver
   cd djskrewdriver
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 💫 Usage

Run the script in any of these ways:

```bash
# Interactive mode
python main.py

# Direct file processing
python main.py path/to/your/audio.mp3 "p:2;rt:0.75;r:1.5;"

# YouTube processing
python main.py https://youtube.com/watch?v=... "p:-2;rt:0.8;"
```

### 🎮 Command Syntax

Structure your audio manipulation instructions using this syntax:
- `p:X;` - Shift pitch by X semitones (any positive or negative number)
- `t:X;` - Time stretch with rate X using librosa.effects.time_stretch
- `rt:X;` - Time stretch with rate X using resampling method
- `r:X;` - Resample with rate X (affects both time and pitch)

For all rate values:
- 1.0 = original speed
- 2.0 = double speed
- 0.5 = half speed

Commands can be chained together and will be applied in sequence.

Example:
```bash
p:2;rt:0.75;r:1.5;
```
This will:
1. Shift pitch up by 2 semitones
2. Slow down to 75% speed using resampling method
3. Speed up by 1.5x with pitch change

### 📂 Output

Processed files are saved in a `processed` directory with timestamps:
- `processed_[timestamp]_[filename].wav`
- `processed_[timestamp]_[filename].mp3`

## 🛠️ Dependencies

- librosa - For audio processing
- soundfile - For WAV file handling
- pydub - For MP3 conversion
- youtube-dl - For YouTube downloads

## 🎵 Examples

1. Create a classic vaporwave effect (pitched down, slowed):
   ```bash
   python main.py song.mp3 "p:-5;rt:0.8;"
   ```

2. Create a nightcore-style edit (faster with higher pitch):
   ```bash
   python main.py song.mp3 "r:1.3;"
   ```

3. Compare time stretch methods:
   ```bash
   python main.py song.mp3 "t:0.75;"  # librosa time_stretch
   python main.py song.mp3 "rt:0.75;" # resampling method
   ```

## 🎯 Command Effects Guide

- **Pitch Shift (`p`)**: Uses librosa.effects.pitch_shift
  - Values are in semitones (half-steps)
  - `p:12;` = Up one octave
  - `p:-12;` = Down one octave
  - `p:1;` = Up one semitone
  - `p:-1;` = Down one semitone

- **Time Stretch (`t`)**: Uses librosa.effects.time_stretch
  - Values are rate multipliers where 1.0 is original speed
  - `t:2.0;` = Double speed
  - `t:0.5;` = Half speed
  - Best for preserving audio quality during tempo changes

- **Resampled Time Stretch (`rt`)**: Uses librosa.resample
  - Values are rate multipliers where 1.0 is original speed
  - `rt:2.0;` = Double speed
  - `rt:0.5;` = Half speed
  - May produce different artifacts compared to `t`
  - Useful for creating specific audio effects

- **Resample (`r`)**: Uses librosa.resample
  - Values are rate multipliers where 1.0 is original speed
  - `r:2.0;` = Double speed (up one octave)
  - `r:0.5;` = Half speed (down one octave)
  - Changes both speed and pitch together

## 🤝 Contributing

Feel free to open issues or submit pull requests if you have suggestions for improvements!

## 📝 License

This project is open source and available under the MIT License.