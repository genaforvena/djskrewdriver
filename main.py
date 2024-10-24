import librosa
import soundfile as sf
import numpy as np
import re
import os
import sys
import sounddevice as sd
import keyboard
import threading
import time
from yt_downloader import download_video
from datetime import datetime
from collections import deque

class AudioPlayback:
    def __init__(self, sr):
        self.sr = sr
        self.is_playing = False
        self.current_position = 0
        self.playback_thread = None
        self.stream = None
        
    def play_callback(self, outdata, frames, time, status):
        if status:
            print(status)
        
        if self.current_position >= len(self.audio_data):
            self.current_position = 0
            raise sd.CallbackStop()
            
        if len(self.audio_data) - self.current_position < frames:
            outdata[:len(self.audio_data) - self.current_position] = \
                self.audio_data[self.current_position:].reshape(-1, 1)
            outdata[len(self.audio_data) - self.current_position:] = 0
            raise sd.CallbackStop()
        else:
            outdata[:] = self.audio_data[self.current_position:self.current_position + frames].reshape(-1, 1)
            self.current_position += frames

    def start_playback(self, audio_data, position=None):
        if position is not None:
            self.current_position = position
        else:
            self.current_position = 0
            
        self.audio_data = audio_data
        
        if self.stream is not None:
            self.stream.close()
            
        self.stream = sd.OutputStream(
            samplerate=self.sr,
            channels=1,
            callback=self.play_callback
        )
        self.stream.start()
        self.is_playing = True

    def pause_playback(self):
        if self.stream is not None:
            self.stream.close()
            self.is_playing = False
            
    def toggle_playback(self, audio_data):
        if self.is_playing:
            self.pause_playback()
        else:
            self.start_playback(audio_data, self.current_position)

    def reset_position(self):
        self.current_position = 0

class AudioHistory:
    def __init__(self, max_size=50):
        self.history = deque(maxlen=max_size)
        self.current_index = -1
        
    def add(self, state, operations):
        """Add a new state and its operations to history"""
        # Remove any future states if we're not at the end
        while len(self.history) > self.current_index + 1:
            self.history.pop()
            
        self.history.append((state.copy(), operations))
        self.current_index = len(self.history) - 1
        
    def can_undo(self):
        return self.current_index > 0
        
    def can_redo(self):
        return self.current_index < len(self.history) - 1
        
    def undo(self):
        """Move back one state"""
        if self.can_undo():
            self.current_index -= 1
            return self.history[self.current_index]
        return None
        
    def redo(self):
        """Move forward one state"""
        if self.can_redo():
            self.current_index += 1
            return self.history[self.current_index]
        return None
        
    def current(self):
        """Get current state"""
        if self.current_index >= 0:
            return self.history[self.current_index]
        return None
    
    def get_operations_history(self):
        """Get list of all operations up to current point"""
        return [ops for _, ops in list(self.history)[:self.current_index + 1]]


class AudioProcessor:
    def __init__(self, file_path):
        self.original_file = file_path
        self.y, self.sr = librosa.load(file_path)
        self.original_y = self.y.copy()
        self.current_y = self.y.copy()
        self.history = AudioHistory()
        self.history.add(self.original_y, [])
        self.playback = AudioPlayback(self.sr)
        self.input_buffer = ""
        
    def process_input(self, key_event):
        """Process input character by character"""
        if key_event.event_type == 'down':
            if key_event.name == 'space':
                self.playback.toggle_playback(self.current_y)
                return True
                
            elif key_event.name == 'up':
                self.playback.reset_position()
                self.playback.start_playback(self.current_y)
                return True
                
            elif key_event.name == 'left' and self.history.can_undo():
                state, ops = self.history.undo()
                self.current_y = state.copy()
                self.print_history_status()
                return True
                
            elif key_event.name == 'right' and self.history.can_redo():
                state, ops = self.history.redo()
                self.current_y = state.copy()
                self.print_history_status()
                return True
                
            elif key_event.name == 'enter':
                # Only process if buffer ends with semicolon
                if self.input_buffer.strip().endswith(';'):
                    result = self.process_instructions(self.input_buffer)
                    self.input_buffer = ""
                    print("\n> ", end='', flush=True)
                    return result
                else:
                    # Add newline if Enter without semicolon
                    print("\n> " + self.input_buffer, end='', flush=True)
                return True
                
            elif key_event.name == 'backspace':
                if self.input_buffer:
                    self.input_buffer = self.input_buffer[:-1]
                    print('\r> ' + self.input_buffer + ' \b', end='', flush=True)
                return True
                
            elif len(key_event.name) == 1:  # Single character
                self.input_buffer += key_event.name
                print(key_event.name, end='', flush=True)
                return True
                
        return True

    def process_instructions(self, instructions):
        """Process instruction string"""
        instructions = instructions.strip()
        if instructions == 'q;':
            return False
            
        if not instructions.endswith(';'):
            return True
            
        operations = parse_instructions(instructions)
        if operations:
            try:
                position = self.playback.current_position
                was_playing = self.playback.is_playing
                
                self.current_y = self.apply_operations(self.current_y, operations)
                self.history.add(self.current_y, operations)
                
                if was_playing:
                    self.playback.start_playback(self.current_y, position)
                    
                print("\nOperations applied successfully")
            except Exception as e:
                print(f"\nError processing audio: {str(e)}")
        else:
            print("\nNo valid instructions found. Please check your input.")
            
        return True

    def print_history_status(self):
        """Print current position in history"""
        current = self.history.current_index + 1
        total = len(self.history.history)
        ops = self.history.current()[1]
        ops_str = " → ".join([f"{op['type']}:{op['value']}" for op in ops]) if ops else "Original"
        print(f"\nState {current}/{total}: {ops_str}")
        print("> " + self.input_buffer, end='', flush=True) 

    def play_audio(self, audio_data=None):
        """Play the current or specified audio"""
        if audio_data is None:
            audio_data = self.current_y
        
        sd.stop()
        sd.play(audio_data, self.sr)
        print("Playing audio... Press 'q' to stop")
        
        try:
            while sd.get_stream().active:
                if keyboard.is_pressed('q'):
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
                    self.history.add(self.current_y, operations)
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
                if op['type'] == 'p':
                    y = pitch_shift(y, self.sr, op['value'])
                elif op['type'] == 't':
                    y = time_stretch(y, op['value'])
                elif op['type'] == 'r':
                    rate = max(0.1, float(op['value']))
                    target_sr = int(self.sr * rate)
                    y = resample(y, self.sr, target_sr)
                    y = librosa.resample(y, orig_sr=target_sr, target_sr=self.sr)
                elif op['type'] == 'rt':
                    y = resample_time(y, self.sr, op['value'])
            except Exception as e:
                print(f"Warning: Operation {op['type']}:{op['value']} failed: {str(e)}")
                continue

        y = match_frequency_profile(y, y_original, self.sr)
        y = match_loudness(y, y_original, self.sr)
        
        return y

    def save_current(self):
        """Save the current state of the audio"""
        processed_dir = 'processed'
        os.makedirs(processed_dir, exist_ok=True)

        date_str = datetime.now().strftime("%Y%m%d%H%M%S")
        base_name = os.path.splitext(os.path.basename(self.original_file))[0]
        
        # Get all operations up to current point
        all_operations = []
        for ops in self.history.get_operations_history():
            all_operations.extend(ops)
        
        operations_str = "_".join([f"{op['type']}{op['value']}" for op in all_operations]) if all_operations else "no_ops"

        if "processed_" in base_name:
            base_name = base_name.split("_")
            output_name = f'{base_name[0]}_{operations_str}_{("_").join(base_name[2:])}'
        else:
            output_name = f'processed_{operations_str}_{base_name}'

        output_wav_file = os.path.join(processed_dir, output_name + ".wav")
        output_mp3_file = os.path.join(processed_dir, output_name + ".mp3")

        sf.write(output_wav_file, self.current_y, self.sr)
        print(f"Processed audio (WAV) saved as {output_wav_file}")

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

def print_controls():
    """Print available controls"""
    print("\nControls:")
    print("Space: Play/Pause")
    print("Up Arrow: Restart playback")
    print("Left/Right Arrows: Navigate history")
    print("Enter: New line (instructions must end with ;)")
    print("q;: Exit")
    print("\nInstructions syntax:")
    print("p:<semitones>; for pitch shift")
    print("t:<rate>; for time stretch")
    print("r:<rate>; for resampling")
    print("rt:<rate>; for time stretch using resampling")
    print("\nRates: 1.0 = normal, 2.0 = double speed, 0.5 = half speed")
    print("Example: p:2;rt:0.75;")
    print("\nNote: All instructions must end with a semicolon (;)")

def main():
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

    processor = AudioProcessor(file_path)
    print(f"\nLoaded audio file: {file_path}")
    print_controls()
    print("\n> ", end='', flush=True)

    try:
        while True:
            event = keyboard.read_event(suppress=True)
            if not processor.process_input(event):
                break
    except KeyboardInterrupt:
        pass
    finally:
        processor.playback.pause_playback()
        print("\nExiting...")

if __name__ == "__main__":
    main()