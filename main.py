import librosa
import soundfile as sf
import numpy as np
import re
import os
import sys
from yt_downloader import download_video  

def match_frequency_profile(modified, original, sr):
    """
    Match the frequency profile of the modified audio to the original using STFT
    """
    # Compute STFTs
    S_original = librosa.stft(original)
    S_modified = librosa.stft(modified)
    
    # Compute magnitude spectrograms
    mag_original = np.abs(S_original)
    mag_modified = np.abs(S_modified)
    
    # Compute average spectral envelope
    avg_original = np.mean(mag_original, axis=1, keepdims=True)
    avg_modified = np.mean(mag_modified, axis=1, keepdims=True)
    
    # Compute scaling factors
    scaling = avg_original / (avg_modified + 1e-8)  # Adding small constant to prevent division by zero
    
    # Apply scaling to modified spectrogram
    S_matched = S_modified * scaling
    
    # Inverse STFT
    return librosa.istft(S_matched)

def match_loudness(modified, original, sr):
    """
    Match the loudness of the modified audio to the original
    """
    # Compute RMS energy for both signals
    rms_original = np.sqrt(np.mean(original**2))
    rms_modified = np.sqrt(np.mean(modified**2))
    
    # Calculate scaling factor
    scaling_factor = rms_original / (rms_modified + 1e-8)  # Adding small constant to prevent division by zero
    
    # Apply scaling
    return modified * scaling_factor

def process_audio(file_path, operations=None, preserve_characteristics=True):
    """
    Process audio with optional frequency and loudness preservation
    """
    y, sr = librosa.load(file_path)
    y_original = y.copy()  # Keep a copy of the original

    if operations:
        for op in operations:
            try:
                if op['type'] == 'p':  # pitch shift
                    y = pitch_shift(y, sr, op['value'])
                elif op['type'] == 't':  # time stretch
                    y = time_stretch(y, op['value'])
                elif op['type'] == 'r':  # resample (affects both time and pitch)
                    rate = max(0.1, float(op['value']))
                    target_sr = int(sr * rate)
                    y = resample(y, sr, target_sr)
                    y = librosa.resample(y, orig_sr=target_sr, target_sr=sr)
                elif op['type'] == 'rt':  # resample-based time stretch
                    y = resample_time(y, sr, op['value'])
            except Exception as e:
                print(f"Warning: Operation {op['type']}:{op['value']} failed: {str(e)}")
                continue

        if preserve_characteristics:
            # Match frequency characteristics
            print("Matching frequency characteristics...")
            y = match_frequency_profile(y, y_original, sr)
            
            # Match loudness
            print("Matching loudness levels...")
            y = match_loudness(y, y_original, sr)

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

def pitch_shift(y, sr, n_steps):
    """Shift the pitch by n semitones"""
    return librosa.effects.pitch_shift(y, sr=sr, n_steps=n_steps)

def time_stretch(y, rate):
    """Time stretch by rate (1.0 = original speed, 2.0 = twice as fast, 0.5 = half speed)"""
    rate = max(0.1, float(rate))  # Prevent rates too close to zero
    return librosa.effects.time_stretch(y, rate=rate)

def resample(y, orig_sr, target_sr):
    """Resample the audio (target_sr/orig_sr determines speed change)"""
    if target_sr <= 0:
        raise ValueError('Target sample rate must be positive')
    return librosa.resample(y, orig_sr=orig_sr, target_sr=target_sr)

def resample_time(y, sr, rate):
    """Time stretch using resampling, preserving original sample rate"""
    rate = max(0.1, float(rate))  # Prevent rates too close to zero
    # First resample to change speed
    intermediate_sr = int(sr * rate)
    y_changed = librosa.resample(y, orig_sr=sr, target_sr=intermediate_sr)
    # Then resample back to original sr to preserve timing
    return librosa.resample(y_changed, orig_sr=intermediate_sr, target_sr=sr)

def parse_instructions(instructions):
    operations = []
    # Updated pattern to include 'rt' command
    pattern = r"(rt|[ptr]):(-?\d*[.,]?\d+);?"
    matches = re.finditer(pattern, instructions)

    for match in matches:
        cmd_type, value = match.groups()
        # Replace comma with dot for decimal numbers
        value = float(value.replace(',', '.'))
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
            print("t:<rate>; for time stretch using librosa's time_stretch")
            print("r:<rate>; for resampling (affects both time and pitch)")
            print("rt:<rate>; for time stretch using resampling")
            print("\nRates: 1.0 = normal, 2.0 = double speed, 0.5 = half speed")
            print("Example: p:2;rt:0.75;r:1.5;")
            print("Note: Use either dot (.) or comma (,) as decimal separator")
            print("\nThis will:")
            print("- Shift pitch up by 2 semitones")
            print("- Slow down to 75% speed using resampling method")
            print("- Speed up by 1.5x with pitch change")
            instructions = input("\nInstructions (optional): ")
            if not instructions:
                process_audio(file_path)
                print("No instructions provided. Audio processed without modifications.")
                break

        operations = parse_instructions(instructions)
        if operations:
            try:
                file_path = process_audio(file_path, operations)
                print("Audio processed with modifications.")
            except Exception as e:
                print(f"Error processing audio: {str(e)}")
        else:
            print("No valid instructions found. Please check your input.")
            break