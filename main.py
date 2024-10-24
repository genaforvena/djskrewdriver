import librosa
import soundfile as sf
import numpy as np
import re
import os
import sys
import sounddevice as sd
from yt_downloader import download_video
from datetime import datetime

class AudioProcessor:
    def __init__(self, file_path):
        self.original_file = file_path
        self.y, self.sr = librosa.load(file_path)
        self.original_y = self.y.copy()
        self.current_y = self.y.copy()
        self.is_playing = False
        
    def reset_to_original(self):
        """Reset audio to original state"""
        self.current_y = self.original_y.copy()
        print("Reset to original audio")
        return self.current_y

    def play_audio(self, audio_data=None):
        """Play the current or specified audio"""
        if audio_data is None:
            audio_data = self.current_y
        
        # Stop any currently playing audio
        sd.stop()
        
        # Play the audio
        sd.play(audio_data, self.sr)
        print("Playing audio... Press 'q' to stop")
        
        # Wait for playback to finish
        try:
            while sd.get_stream().active:
                user_input = input()
                if user_input.lower() == 'q':
                    sd.stop()
                    print("Playback stopped")
                    break
        except KeyboardInterrupt:
            sd.stop()
            print("\nPlayback stopped")

    def preview_operations(self, operations):
        """Preview the result of operations without saving"""
        temp_y = self.current_y.copy()
        
        try:
            processed_y = self.apply_operations(temp_y, operations)
            print("\nPlaying preview... Press 'q' to stop")
            self.play_audio(processed_y)
            
            while True:
                choice = input("\nDo you want to:\n1. Apply these changes\n2. Discard and try different operations\nChoice (1/2): ")
                if choice == '1':
                    self.current_y = processed_y
                    return True
                elif choice == '2':
                    return False
                else:
                    print("Invalid choice. Please enter 1 or 2.")
        except Exception as e:
            print(f"Preview failed: {str(e)}")
            return False

    def apply_operations(self, audio_data, operations):
        """Apply audio operations to the given audio data"""
        y = audio_data.copy()
        y_original = audio_data.copy()

        for op in operations:
            try:
                if op['type'] == 'p':  # pitch shift
                    y = pitch_shift(y, self.sr, op['value'])
                elif op['type'] == 't':  # time stretch
                    y = time_stretch(y, op['value'])
                elif op['type'] == 'r':  # resample
                    rate = max(0.1, float(op['value']))
                    target_sr = int(self.sr * rate)
                    y = resample(y, self.sr, target_sr)
                    y = librosa.resample(y, orig_sr=target_sr, target_sr=self.sr)
                elif op['type'] == 'rt':  # resample-based time stretch
                    y = resample_time(y, self.sr, op['value'])
            except Exception as e:
                print(f"Warning: Operation {op['type']}:{op['value']} failed: {str(e)}")
                continue

        # Match frequency characteristics and loudness
        y = match_frequency_profile(y, y_original, self.sr)
        y = match_loudness(y, y_original, self.sr)
        
        return y

    def save_current(self, operations=None):
        """Save the current state of the audio"""
        processed_dir = 'processed'
        os.makedirs(processed_dir, exist_ok=True)

        date_str = datetime.now().strftime("%Y%m%d%H%M%S")
        base_name = os.path.splitext(os.path.basename(self.original_file))[0]
        operations_str = "_".join([f"{op['type']}{op['value']}" for op in operations]) if operations else "no_ops"

        if "processed_" in base_name:
            base_name = base_name.split("_")
            output_name = f'{base_name[0]}_{operations_str}_{("_").join(base_name[2:])}'
        else:
            output_name = f'processed_{operations_str}_{base_name}'

        output_wav_file = os.path.join(processed_dir, output_name + ".wav")
        output_mp3_file = os.path.join(processed_dir, output_name + ".mp3")

        # Save WAV file
        sf.write(output_wav_file, self.current_y, self.sr)
        print(f"Processed audio (WAV) saved as {output_wav_file}")

        # Convert and save MP3 file
        from pydub import AudioSegment
        sound = AudioSegment.from_wav(output_wav_file)
        sound.export(output_mp3_file, format="mp3")
        print(f"Processed audio (MP3) saved as {output_mp3_file}")

        return output_wav_file

def match_frequency_profile(modified, original, sr):
    """Match the frequency profile of the modified audio to the original using STFT"""
    S_original = librosa.stft(original)
    S_modified = librosa.stft(modified)
    
    mag_original = np.abs(S_original)
    mag_modified = np.abs(S_modified)
    
    avg_original = np.mean(mag_original, axis=1, keepdims=True)
    avg_modified = np.mean(mag_modified, axis=1, keepdims=True)
    
    scaling = avg_original / (avg_modified + 1e-8)
    S_matched = S_modified * scaling
    
    return librosa.istft(S_matched)

def match_loudness(modified, original, sr):
    """Match the loudness of the modified audio to the original"""
    rms_original = np.sqrt(np.mean(original**2))
    rms_modified = np.sqrt(np.mean(modified**2))
    scaling_factor = rms_original / (rms_modified + 1e-8)
    return modified * scaling_factor

def pitch_shift(y, sr, n_steps):
    """Shift the pitch by n semitones"""
    return librosa.effects.pitch_shift(y, sr=sr, n_steps=n_steps)

def time_stretch(y, rate):
    """Time stretch by rate"""
    rate = max(0.1, float(rate))
    return librosa.effects.time_stretch(y, rate=rate)

def resample(y, orig_sr, target_sr):
    """Resample the audio"""
    if target_sr <= 0:
        raise ValueError('Target sample rate must be positive')
    return librosa.resample(y, orig_sr=orig_sr, target_sr=target_sr)

def resample_time(y, sr, rate):
    """Time stretch using resampling"""
    rate = max(0.1, float(rate))
    intermediate_sr = int(sr * rate)
    y_changed = librosa.resample(y, orig_sr=sr, target_sr=intermediate_sr)
    return librosa.resample(y_changed, orig_sr=intermediate_sr, target_sr=sr)

def parse_instructions(instructions):
    """Parse the instruction string into operations"""
    operations = []
    pattern = r"(rt|[ptr]):(-?\d*[.,]?\d+);?"
    matches = re.finditer(pattern, instructions)

    for match in matches:
        cmd_type, value = match.groups()
        value = float(value.replace(',', '.'))
        operations.append({'type': cmd_type, 'value': value})

    return operations

def print_menu():
    """Print the main menu options"""
    print("\nAvailable commands:")
    print("1. Enter new operations")
    print("2. Play current audio")
    print("3. Reset to original")
    print("4. Save current state")
    print("5. Exit")
    
def print_operation_help():
    """Print help for operation syntax"""
    print("\nEnter your instructions using the following syntax:")
    print("p:<semitones>; for pitch shift (any number of semitones)")
    print("t:<rate>; for time stretch using librosa's time_stretch")
    print("r:<rate>; for resampling (affects both time and pitch)")
    print("rt:<rate>; for time stretch using resampling")
    print("\nRates: 1.0 = normal, 2.0 = double speed, 0.5 = half speed")
    print("Example: p:2;rt:0.75;r:1.5;")
    print("Note: Use either dot (.) or comma (,) as decimal separator")

def main():
    # Handle input file or YouTube URL
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg.startswith('https'):
            url = arg
            output_path = "."
            file_path = download_video(url, output_path)
        else:
            file_path = arg
    else:
        file_path = input("Enter the path to your audio file (or leave blank to download from YouTube): ")
        if not file_path:
            url = input("Enter the YouTube video URL: ")
            output_path = "."
            file_path = download_video(url, output_path)

    # Initialize audio processor
    processor = AudioProcessor(file_path)
    print(f"\nLoaded audio file: {file_path}")

    while True:
        print_menu()
        choice = input("\nEnter your choice (1-5): ")

        if choice == '1':
            print_operation_help()
            instructions = input("\nInstructions: ")
            if instructions:
                operations = parse_instructions(instructions)
                if operations:
                    if processor.preview_operations(operations):
                        print("Operations applied successfully")
                else:
                    print("No valid instructions found. Please check your input.")
                    
        elif choice == '2':
            processor.play_audio()
            
        elif choice == '3':
            processor.reset_to_original()
            print("Audio reset to original state")
            
        elif choice == '4':
            operations = []  # You might want to keep track of applied operations
            processor.save_current(operations)
            
        elif choice == '5':
            print("Exiting...")
            break
            
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")

if __name__ == "__main__":
    main()