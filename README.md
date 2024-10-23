# DJ Screwdriver 🎚️

A Python-based audio manipulation tool that lets you experiment with track speeds using different algorithms. Perfect for creating remixes, vaporwave-style edits, or any creative audio experiments.

## ✨ Features

- Process local audio files or download directly from YouTube
- Multiple speed manipulation algorithms:
  - Preserve pitch while changing speed (like a DJ's tempo control)
  - Classic speed change with pitch shift (think vaporwave-style effects)
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
python main.py path/to/your/audio.mp3 "SLOW:10:PITCH;SPEED:20:NOPITCH;"

# YouTube processing
python main.py https://youtube.com/watch?v=... "SLOW:10:PITCH;"
```

### 🎮 Command Syntax

Structure your speed instructions using this syntax:
- `SPEED:X:PITCH;` - Speed up by X% while preserving pitch
- `SPEED:X:NOPITCH;` - Speed up by X% with pitch shift
- `SLOW:X:PITCH;` - Slow down by X% while preserving pitch
- `SLOW:X:NOPITCH;` - Slow down by X% with pitch shift

Example:
```bash
SLOW:10:PITCH;SPEED:20:NOPITCH;
```
This will:
1. Slow down the track by 10% (keeping original pitch)
2. Then speed it up by 20% (with pitch shift)

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

1. Create a slowed + reverb style edit:
   ```bash
   python main.py song.mp3 "SLOW:15:NOPITCH;"
   ```

2. Speed up for chipmunk effect:
   ```bash
   python main.py song.mp3 "SPEED:30:NOPITCH;"
   ```

3. Complex sequence:
   ```bash
   python main.py song.mp3 "SLOW:20:PITCH;SPEED:10:NOPITCH;SLOW:5:PITCH;"
   ```

## 🤝 Contributing

Feel free to open issues or submit pull requests if you have suggestions for improvements!

## 📝 License

This project is open source and available under the MIT License.