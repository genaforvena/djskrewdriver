import librosa
import soundfile as sf
import numpy as np
import re
import os
import sys
from yt_downloader import download_video  

def change_speed(y, sr, speed_factor, preserve_pitch=True):
    if preserve_pitch:
        return librosa.effects.time_stretch(y, rate=speed_factor)
    else:
        return librosa.resample(y, orig_sr=sr, target_sr=int(sr * speed_factor))  # Use keyword arguments

def process_audio(file_path, operations=None):
    y, sr = librosa.load(file_path)
    
    if operations:
        for op in operations:
            speed_factor = 1 + op['change'] / 100
            y = change_speed(y, sr, speed_factor, op['preserve_pitch'])
    
    # Create the processed directory if it doesn't exist
    processed_dir = 'processed'
    os.makedirs(processed_dir, exist_ok=True)

    # Get the current date for filename
    from datetime import datetime
    date_str = datetime.now().strftime("%Y%m%d%H%M%S")

    # Change the output file path to save in the processed folder with date
    base_name = os.path.splitext(os.path.basename(file_path))[0]
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
    pattern = r"(SPEED|SLOW):(\d+):(PITCH|NOPITCH);"
    matches = re.finditer(pattern, instructions)
    
    for match in matches:
        action, percentage, pitch_option = match.groups()
        change = int(percentage)
        if action == "SLOW":
            change = -change
        preserve_pitch = (pitch_option == "PITCH")
        operations.append({'change': change, 'preserve_pitch': preserve_pitch})
    
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
            print("Enter your instructions using the following syntax:")
            print("SPEED:<percentage>:PITCH; or SPEED:<percentage>:NOPITCH; to speed up")
            print("SLOW:<percentage>:PITCH; or SLOW:<percentage>:NOPITCH; to slow down")
            print("Example: SLOW:10:PITCH;SPEED:20:NOPITCH;")
            instructions = input("Instructions (optional): ")
            if not instructions:
                process_audio(file_path)
                print("No instructions provided. Audio processed without modifications.")
                break  # Exit the loop if no instructions are provided
        operations = parse_instructions(instructions)
        if operations:
            file_path = process_audio(file_path, operations)
            print("Audio processed with modifications.")
        else:
            print("No valid instructions found. Please check your input.")
            break  # Exit the loop if no valid instructions are found
