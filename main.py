import librosa
import soundfile as sf
import numpy as np
import re
import os
import sys
from yt_downloader import download_video  

def pitch_shift(y, sr, n_steps):
    """Shift the pitch by n semitones"""
    return librosa.effects.pitch_shift(y, sr=sr, n_steps=n_steps)

def time_stretch(y, rate):
    """Time stretch by rate (1.0 = original speed, 2.0 = twice as fast, 0.5 = half speed)"""
    return librosa.effects.time_stretch(y, rate=rate)

def resample(y, orig_sr, target_sr):
    """Resample the audio (target_sr/orig_sr determines speed change)"""
    return librosa.resample(y, orig_sr=orig_sr, target_sr=target_sr)

def process_audio(file_path, operations=None):
    y, sr = librosa.load(file_path)

    if operations:
        for op in operations:
            if op['type'] == 'p':  # pitch shift
                y = pitch_shift(y, sr, op['value'])
            elif op['type'] == 't':  # time stretch
                y = time_stretch(y, op['value'])
            elif op['type'] == 'r':  # resample
                target_sr = int(sr * op['value'])
                y = resample(y, sr, target_sr)
                y = librosa.resample(y, orig_sr=target_sr, target_sr=sr)

    # Create the processed directory if it doesn't exist
    processed_dir = 'processed'
    os.makedirs(processed_dir, exist_ok=True)

    # Get the current date for filename
    from datetime import datetime
    date_str = datetime.now().strftime("%Y%m%d%H%M%S")

    # Change the output file path to save in the processed folder with date
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    if 'processed_' in base_name:
        output_wav_file = os.path.join(processed_dir, f'{base_name}_{date_str}.wav')
        output_mp3_file = os.path.join(processed_dir, f'{base_name}_{date_str}.mp3')
    else:    
        output_wav_file = os.path.join(processed_dir, f'processed_{date_str}_{base_name}.wav')
        output_mp3_file = os.path.join(processed_dir, f'processed_{date_str}_{base_name}.mp3')

    # Save WAV file
    sf.write(output_wav_file, y, sr)
    print(f"Processed audio (WAV) saved as {output_wav_file}")

    # Convert and save MP3 file
    from pydub import AudioSegment
    sound = AudioSegment.from_wav(output_wav_file)
    sound.export(output_mp3_file, format="mp3")
    print(f"Processed audio (MP3) saved as {output_mp3_file}")

    return output_wav_file

def parse_instructions(instructions):
    operations = []
    # Pattern for floating point values
    pattern = r"([ptr]):(-?\d*\.?\d+);?"
    matches = re.finditer(pattern, instructions)

    for match in matches:
        cmd_type, value = match.groups()
        value = float(value)
        operations.append({'type': cmd_type, 'value': value})

    return operations

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg.startswith('https'):
            url = arg
            output_path = "."  
            mp3_file = download_video(url, output_path)  
            print(f"Downloaded MP3 file: {mp3_file}")
            file_path = mp3_file 
        else:
            file_path = arg
    else:
        file_path = input("Enter the path to your audio file (or leave blank to download from YouTube): ")
        if not file_path: 
            url = input("Enter the YouTube video URL: ")
            output_path = "."  
            mp3_file = download_video(url, output_path)  
            print(f"Downloaded MP3 file: {mp3_file}")
            file_path = mp3_file 

    while True:
        if len(sys.argv) > 2:
            instructions = sys.argv[2]
        else:
            print("\nEnter your instructions using the following syntax:")
            print("p:<semitones>; for pitch shift (any number of semitones)")
            print("t:<rate>; for time stretch (1.0 = normal, 2.0 = double speed, 0.5 = half speed)")
            print("r:<rate>; for resampling (1.0 = normal, 2.0 = double speed, 0.5 = half speed)")
            print("Example: p:2;t:0.75;r:1.5;")
            print("This will:")
            print("- Shift pitch up by 2 semitones")
            print("- Slow down to 75% speed")
            print("- Speed up by 1.5x using resampling")
            instructions = input("\nInstructions (optional): ")
            if not instructions:
                process_audio(file_path)
                print("No instructions provided. Audio processed without modifications.")
                break

        operations = parse_instructions(instructions)
        if operations:
            file_path = process_audio(file_path, operations)
            print("Audio processed with modifications.")
        else:
            print("No valid instructions found. Please check your input.")
            break