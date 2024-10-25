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
import tempfile
import shutil

class AudioHistory:
    def __init__(self, max_size=50):
        self.history = deque(maxlen=max_size)
        self.current_index = -1
        
    def add(self, state, operations):
        """Add a new state and its operations to history"""
        # Remove any future states if we're not at the end
        while len(self.history) > self.current_index + 1:
            self.history.pop()
            
        # Change this line to append the state directly
        self.history.append((state, operations))  # Removed .copy()
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
        
    def cleanup(self):
        """Remove all temporary files"""
        for _, file_path in self.history:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass

class AudioPlayback:
    def __init__(self, file_path, sr):
        self.sr = sr
        self.is_playing = False
        self.stream = None
        self.audio_data = None
        self.current_position = 0
        self.load_audio(file_path)
        
    def load_audio(self, file_path):
        """Load entire audio file into memory for playback"""
        try:
            # Explicitly load as float32 array
            audio_data, sr = sf.read(file_path, dtype='float32')
            
            # Ensure audio is 2D array (samples x channels)
            if len(audio_data.shape) == 1:
                self.audio_data = audio_data.reshape(-1, 1)
            else:
                self.audio_data = audio_data
                
            # Keep current position if reloading while playing
            if hasattr(self, 'current_position'):
                self.current_position = min(self.current_position, len(self.audio_data))
            else:
                self.current_position = 0
                
        except Exception as e:
            print(f"Error loading audio: {str(e)}")
            self.audio_data = np.zeros((1024, 1), dtype='float32')  # Safe fallback
            self.current_position = 0
        
    def play_callback(self, outdata, frames, time, status):
        if status:
            print(status)
        
        if self.audio_data is None or self.current_position >= len(self.audio_data):
            self.current_position = 0
            
        try:
            remaining = len(self.audio_data) - self.current_position
            if remaining < frames:
                # Handle end of file
                outdata[:remaining] = self.audio_data[self.current_position:]
                outdata[remaining:] = 0
                self.current_position = 0
            else:
                outdata[:] = self.audio_data[self.current_position:self.current_position + frames]
                self.current_position += frames
        except Exception as e:
            print(f"Playback error: {str(e)}")
            outdata.fill(0)
            
    def start_playback(self, position=None):
        if position is not None:
            self.current_position = min(position, len(self.audio_data))
            
        if hasattr(self, 'stream') and self.stream is not None:
            self.stream.close()
            
        try:
            self.stream = sd.OutputStream(
                samplerate=self.sr,
                channels=self.audio_data.shape[1] if len(self.audio_data.shape) > 1 else 1,
                callback=self.play_callback,
                blocksize=2048,  # Larger block size for more stable playback
                dtype=self.audio_data.dtype
            )
            self.stream.start()
            self.is_playing = True
        except Exception as e:
            print(f"Error starting playback: {str(e)}")
            self.is_playing = False

    def pause_playback(self):
        if hasattr(self, 'stream') and self.stream is not None:
            try:
                self.stream.close()
                self.stream = None
                self.is_playing = False
            except Exception as e:
                print(f"Error pausing playback: {str(e)}")
            
    def toggle_playback(self):
        if self.is_playing:
            self.pause_playback()
        else:
            self.start_playback(self.current_position)

    def reset_position(self):
        self.current_position = 0
        if self.is_playing:
            self.start_playback(0)


class AudioProcessor:
    def __init__(self, file_path):
        self.original_file = file_path
        self.temp_dir = tempfile.mkdtemp()
        
        # Load original audio
        self.y, self.sr = librosa.load(file_path)
        
        # Save working copy
        self.working_file = os.path.join(self.temp_dir, 'working.wav')
        sf.write(self.working_file, self.y, self.sr)
        
        # Initialize playback with working file
        self.playback = AudioPlayback(self.working_file, self.sr)
        
        # Initialize history and input buffer
        self.history = AudioHistory()
        self.history.add(self.working_file, [])
        self.input_buffer = ""

    def process_instructions(self, instructions):
        instructions = instructions.strip()
        if instructions == 'q;':
            return False
            
        if not instructions.endswith(';'):
            return True
            
        operations = parse_instructions(instructions)
        if operations:
            try:
                # Store playback state
                position = self.playback.current_position
                was_playing = self.playback.is_playing
                
                if was_playing:
                    self.playback.pause_playback()
                
                # Load current working file
                y, sr = sf.read(self.working_file)
                
                # Apply operations
                y = self.apply_operations(y, operations)
                
                # Save to new temporary file
                temp_file = os.path.join(self.temp_dir, f'temp_{datetime.now().strftime("%Y%m%d%H%M%S")}.wav')
                sf.write(temp_file, y, sr)
                
                # Add to history and update working file
                self.history.add(temp_file, operations)
                shutil.copy2(temp_file, self.working_file)
                
                # Update playback
                self.playback.load_audio(self.working_file)
                
                # Restore playback state
                if was_playing:
                    self.playback.start_playback(position)
                
                print("\nOperations applied successfully")
                
            except Exception as e:
                print(f"\nError processing audio: {str(e)}")
        else:
            print("\nNo valid instructions found. Please check your input.")
            
        return True

    def process_input(self, key_event):
        """Process input character by character"""
        if key_event.event_type == 'down':
            if key_event.name == 'space':
                self.playback.toggle_playback()
                    
            elif key_event.name == 'up':
                self.playback.reset_position()
                self.playback.start_playback()
                    
            elif key_event.name == 'left' and self.history.can_undo():
                file_path, ops = self.history.undo()
                if file_path:
                    # Store playback state
                    position = self.playback.current_position
                    was_playing = self.playback.is_playing
                        
                    if was_playing:
                        self.playback.pause_playback()
                        
                    shutil.copy2(file_path, self.working_file)
                    self.playback.load_audio(self.working_file)
                        
                    if was_playing:
                        self.playback.start_playback(position)
                        
                    self.print_history_status()
                    
            elif key_event.name == 'right' and self.history.can_redo():
                file_path, ops = self.history.redo()
                if file_path:
                    # Store playback state
                    position = self.playback.current_position
                    was_playing = self.playback.is_playing
                        
                    if was_playing:
                        self.playback.pause_playback()
                        
                    shutil.copy2(file_path, self.working_file)
                    self.playback.load_audio(self.working_file)
                        
                    if was_playing:
                        self.playback.start_playback(position)
                        
                    self.print_history_status()
                    
            elif key_event.name == 'enter':
                if self.input_buffer.strip() == 'q;':
                    return False
                if self.input_buffer.strip().endswith(';'):
                    instructions = self.input_buffer
                    self.input_buffer = ""
                    print("\n> ", end='', flush=True)
                    # Process instructions and continue regardless of result
                    self.process_instructions(instructions)
                else:
                    print("\n> " + self.input_buffer, end='', flush=True)
                    
            elif key_event.name == 'backspace':
                if self.input_buffer:
                    self.input_buffer = self.input_buffer[:-1]
                    print('\r> ' + self.input_buffer + ' \b', end='', flush=True)
                    
            elif len(key_event.name) == 1:
                self.input_buffer += key_event.name
                print(key_event.name, end='', flush=True)
        
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
                # Store playback state
                position = self.playback.current_position
                was_playing = self.playback.is_playing
                
                if was_playing:
                    self.playback.pause_playback()
                
                # Load current working file
                y, sr = sf.read(self.working_file)
                
                # Apply operations
                y = self.apply_operations(y, operations)
                
                # Save to new temporary file
                temp_file = os.path.join(self.temp_dir, f'temp_{datetime.now().strftime("%Y%m%d%H%M%S")}.wav')
                sf.write(temp_file, y, sr)
                
                # Add to history and update working file
                self.history.add(temp_file, operations)
                shutil.copy2(temp_file, self.working_file)
                
                # Update playback
                self.playback.load_audio(self.working_file)
                
                # Restore playback state
                if was_playing:
                    self.playback.start_playback(position)
                
                print("\nOperations applied successfully")
                
            except Exception as e:
                print(f"\nError processing audio: {str(e)}")
        else:
            print("\nNo valid instructions found. Please check your input.")
            
        return True

    def cleanup(self):
        """Clean up temporary files"""
        # self.playback.pause_playback()  # Remove this line if not needed
        try:
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"Error cleaning up temporary files: {str(e)}")

    def apply_operations(self, y, operations):
        """Apply audio operations"""
        y_original = y.copy()
        
        for op in operations:
            try:
                if op['type'] == 'p':
                    y = librosa.effects.pitch_shift(y, sr=self.sr, n_steps=op['value'])
                elif op['type'] == 't':
                    y = librosa.effects.time_stretch(y, rate=float(op['value']))
                elif op['type'] == 'r':
                    rate = max(0.1, float(op['value']))
                    target_sr = int(self.sr * rate)
                    y = librosa.resample(y, orig_sr=self.sr, target_sr=target_sr)
                    y = librosa.resample(y, orig_sr=target_sr, target_sr=self.sr)
                elif op['type'] == 'rt':
                    y = resample_time(y, self.sr, op['value'])
            except Exception as e:
                print(f"Warning: Operation {op['type']}:{op['value']} failed: {str(e)}")
                continue

        # Match characteristics
        y = match_frequency_profile(y, y_original, self.sr)
        y = match_loudness(y, y_original, self.sr)
        
        return y

    def print_history_status(self):
        current = self.history.current_index + 1
        total = len(self.history.history)
        ops = self.history.current()[0]  # Operations are now first in tuple
        ops_str = " → ".join([f"{op['type']}:{op['value']}" for op in ops]) if ops else "Original"
        print(f"\nState {current}/{total}: {ops_str}")
        print("> " + self.input_buffer, end='', flush=True)

class AudioHistory:
    def __init__(self, max_size=50):
        self.history = deque(maxlen=max_size)
        self.current_index = -1
        
    def add(self, state, operations):
        """Add a new state and its operations to history"""
        # Remove any future states if we're not at the end
        while len(self.history) > self.current_index + 1:
            self.history.pop()
            
        # Change this line to append the state directly
        self.history.append((state, operations))  # Removed .copy()
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
        processor.cleanup()
        print("\nExiting...")

if __name__ == "__main__":
    main()

