# DJ Screwdriver 🎚️

A Python-based audio manipulation tool that lets you experiment with track speeds and pitches using different algorithms. Perfect for creating remixes, vaporwave-style edits, or any creative audio experiments.

## ✨ Features

- Process local audio files or download directly from YouTube
- Multiple audio manipulation algorithms:
  - Pitch shifting (semitone-based adjustment)
  - Time stretching (tempo changes while preserving pitch)
  - Resampling (classic speed change affecting both time and pitch)
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
python main.py path/to/your/audio.mp3 "p:2;t:-10;r:5;"

# YouTube processing
python main.py https://youtube.com/watch?v=... "p:-2;t:15;"
```

### 🎮 Command Syntax

Structure your audio manipulation instructions using this syntax:
- `p:X;` - Shift pitch by X semitones (positive = higher, negative = lower)
- `t:X;` - Time stretch by X percent (positive = faster, negative = slower)
- `r:X;` - Resample by X percent (positive = faster, negative = slower)

Commands can be chained together and will be applied in sequence.

Example:
```bash
p:2;t:-10;r:5;
```
This will:
1. Shift pitch up by 2 semitones
2. Slow down by 10% (preserving the new pitch)
3. Speed up by 5% using resampling (affects both time and pitch)

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
   python main.py song.mp3 "p:-2;t:-15;"
   ```

2. Create a nightcore-style edit (faster with higher pitch):
   ```bash
   python main.py song.mp3 "r:30;"
   ```

3. Complex sequence:
   ```bash
   python main.py song.mp3 "p:1;t:-10;r:5;p:-0.5;"
   ```

4. Download and process YouTube video:
   ```bash
   python main.py https://youtube.com/watch?v=... "p:-3;t:-20;"
   ```

## 🎯 Command Effects Guide

- **Pitch Shift (`p`)**: Adjusts the pitch without changing tempo. Each semitone represents a half-step in musical terms:
  - `p:12;` = Up one octave
  - `p:-12;` = Down one octave
  - `p:1;` = Up one semitone
  - `p:-1;` = Down one semitone

- **Time Stretch (`t`)**: Changes speed while preserving pitch:
  - `t:50;` = 50% faster
  - `t:-50;` = 50% slower
  - `t:100;` = Double speed
  - `t:-25;` = 25% slower

- **Resample (`r`)**: Classic speed change affecting both time and pitch:
  - `r:50;` = 50% faster (higher pitch)
  - `r:-50;` = 50% slower (lower pitch)

## 🤝 Contributing

Feel free to open issues or submit pull requests if you have suggestions for improvements!

## 📝 License

This project is open source and available under the MIT License.