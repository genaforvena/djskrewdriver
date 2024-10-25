import librosa
import soundfile as sf
import numpy as np
import re
import os
import sys
import sounddevice as sd
from datetime import datetime
from collections import deque
from .audio import *
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


# Standalone audio processing functions
def pitch_shift(y, sr, n_steps):
    return librosa.effects.pitch_shift(y, sr=sr, n_steps=n_steps)

def time_stretch(y, rate):
    return librosa.effects.time_stretch(y, rate=rate)

def resample_audio(y, sr, rate):
    target_sr = int(sr * rate)
    y = librosa.resample(y, orig_sr=sr, target_sr=target_sr)
    return librosa.resample(y, orig_sr=target_sr, target_sr=sr)

def reverse_by_beats(y, sr, beats, value1, value2, value3):
    # Implement the reverse logic here
    pass

def add_stutter(y, sr, beats, value1, value2, value3):
    # Implement the stutter logic here
    pass

def add_echo(y, sr, delay, beats, value1, value2, value3):
    # Implement the echo logic here
    pass

def create_loop(y, sr, beats, value1, value2, value3):
    # Implement the loop logic here
    pass

def chop_and_rearrange(y, sr, beats, value1, value2, value3):
    # Implement the chop logic here
    pass

def apply_frequency_muting(y, sr, threshold_db):
    # Implement the frequency muting logic here
    pass

def apply_trigger_muting(y, sr, sensitivity, beats):
    # Implement the trigger muting logic here
    pass

def delete_beat_parts(y, sr, beats, value1, value2, value3):
    # Implement the delete logic here
    pass

def extract_percussive_track(y, sr):
    # Implement the percussive track extraction logic here
    pass

def random_mix_beats(y, sr, beats, value1, value2, value3):
    # Implement the random mix logic here
    pass

def spectral_gate(y, sr, threshold_db, preserve_freq_ranges):
    # Implement the spectral gate logic here
    pass

def match_frequency_profile(y, y_original, sr):
    # Implement the frequency profile matching logic here
    pass

def match_loudness(y, y_original, sr):
    # Implement the loudness matching logic here
    pass

# AudioProcessor class
class AudioProcessor:
    def __init__(self, file_path, config_file='commands.txt'):
        self.config_file = config_file
        self.commands = self.load_commands()
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

    def load_commands(self):
        """Load commands from the configuration file"""
        commands = {}
        try:
            with open(self.config_file, 'r') as file:
                for line in file:
                    parts = line.strip().split(';')
                    if len(parts) == 2:
                        command_name, command_value = parts
                        commands[command_name] = command_value
        except FileNotFoundError:
            print(f"Config file '{self.config_file}' not found. No custom commands loaded.")
        return commands

    def process_instructions(self, instructions):
        """Process instruction string"""
        instructions = instructions.strip()
        print(f"Processing instructions: '{instructions}'")  # Debugging line

        # Check for exit command
        if instructions == 'q;':
            print("Exiting the program...")
            sys.exit(0)  # Exit the program

        # Check for save command
        elif instructions == 's;':
            self.save_current_state()  # Save the current state
            print("\nCurrent state saved.")
            return True  # Continue processing instructions
        # Check for apply command
        elif instructions == 'a;':
            self.apply_changes()  # Apply changes to the track
            print("\nChanges applied.")
            return True  # Continue processing instructions
        # Check for playback toggle command
        elif instructions == 'p;':
            self.playback.toggle_playback()  # Toggle playback
            print("\nPlayback toggled.")
            return True  # Continue processing instructions

        # Check for incomplete instruction
        if not instructions.endswith(';'):
            print("Incomplete instruction.")  # Debugging line
            return True  # Continue processing if not a complete instruction

        # Replace custom commands with their values
        for command_name, command_value in self.commands.items():
            instructions = instructions.replace(command_name + ';', command_value + ';')

        # Parse and process other operations
        operations = self.parse_instructions(instructions)
        if operations:
            self.execute_operations(operations)
        else:
            raise Exception("Couldn't parse instructions from " + instructions) 
            
        return True  # Continue processing

    def execute_operations(self, operations):
        """Execute parsed operations on the audio"""
        try:
            # Store playback state
            position = self.playback.current_position
            was_playing = self.playback.is_playing
            
            if was_playing:
                self.playback.pause_playback()
            
            # Process each operation
            for operation in operations:
                if operation['type'] == 'revert':
                    self.handle_revert_operation(operation)
                    return  # Exit the function instead of continuing a loop

            # Load current working file
            y, sr = sf.read(self.working_file)
            
            print("Applying operations...")
            for op in operations:
                print(f"Applying operation: {op['type']} with values {op['values']}")
            # Apply other operations
            y = self.apply_operations(y, operations)
            print("Operations applied.")
            
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

    def handle_revert_operation(self, operation):
        """Handle revert operation"""
        steps = int(operation['values'][0])  # Get the number of steps
        if steps > 0 and self.history.can_undo():
            for _ in range(steps):
                file_path, ops = self.history.undo()
                if file_path:
                    # Load the previous state
                    shutil.copy2(file_path, self.working_file)
                    self.playback.load_audio(self.working_file)
        elif steps < 0 and self.history.can_redo():
            for _ in range(-steps):
                file_path, ops = self.history.redo()
                if file_path:
                    # Load the next state
                    shutil.copy2(file_path, self.working_file)
                    self.playback.load_audio(self.working_file)
        self.print_history_status()

    def apply_operations(self, y, operations):
        """Apply audio operations"""
        y_original = y.copy()
    
        # Detect BPM at the start
        tempo, beats = librosa.beat.beat_track(y=y, sr=self.sr)
        beat_length = 60.0 / tempo  # Length of one beat in seconds
    
        for op in operations:
            try:
                # Extract values with defaults
                values = op['values']
                value1 = values[0] if len(values) > 0 else 1
                value2 = values[1] if len(values) > 1 else 4
                value3 = values[2] if len(values) > 2 else 1
            
                if op['type'] == 'p':
                    y = AudioEffects.pitch_shift(y, self.sr, value1)
                elif op['type'] == 't':
                    y = AudioEffects.time_stretch(y, rate=float(value1))
                elif op['type'] == 'r':
                    y = AudioEffects.resample_time(y, self.sr, rate=float(value1))
                elif op['type'] == 'rt':
                    y = AudioEffects.resample_time(y, self.sr, value1)
                elif op['type'] == 'rev':
                    y = AudioEffects.reverse_by_beats(y, self.sr, beats, value1, value2, value3)
                elif op['type'] == 'speed':
                    y = AudioEffects.time_stretch(y, rate=float(value1))
                elif op['type'] == 'stut':
                    y = AudioEffects.add_stutter(y, self.sr, beats, value1, value2, value3)
                elif op['type'] == 'echo':
                    delay = value1 if value1 > 0 else beat_length
                    y = AudioEffects.add_echo(y, self.sr, delay, beats, value1, value2, value3)
                elif op['type'] == 'loop':
                    y = AudioEffects.create_loop(y, self.sr, beats, value1, value2, value3)
                elif op['type'] == 'chop':
                    y = AudioEffects.chop_and_rearrange(y, self.sr, beats, value1, value2, value3)
                elif op['type'] == 'mute':
                    y = AudioEffects.apply_frequency_muting(y, self.sr, threshold_db=value1)
                elif op['type'] == 'trig':
                    y = AudioEffects.apply_trigger_muting(y, self.sr, sensitivity=value1, beats=beats)
                elif op['type'] == 'del':
                    y = AudioEffects.delete_beat_parts(y, self.sr, beats, value1, value2, value3)
                elif op['type'] == 'n':
                    threshold = value1
                    preserve_ranges = [
                        (80, 1200),    # Voice fundamental frequencies
                        (2000, 4000)   # Voice harmonics and clarity
                    ]
                    y = AudioEffects.spectral_gate(y, self.sr, threshold_db=threshold, preserve_freq_ranges=preserve_ranges)
                elif op['type'] == 'perc':
                    y = AudioEffects.extract_percussive_track(y, self.sr)
                elif op['type'] == 'copy':
                    start_byte = int(value1)
                    num_bytes = int(value2)
                    y[start_byte:start_byte + num_bytes] = y[start_byte]
                elif op['type'] == 'mash':
                    y = AudioEffects.random_mix_beats(y, self.sr, beats, value1, value2, value3)
    
            except Exception as e:
                print(f"Warning: Operation {op['type']}:{values} failed: {str(e)}")
                continue

        return y

    def process_input(self):
        """Process input and wait for Enter key press"""
        while True:
            command = input("> ").strip()
            if command:
                # Check if the command is a configurable command
                if command in self.commands:
                    command = self.commands[command]
                
                # Split the command into individual instructions
                instructions = command.split(';')
                for instruction in instructions:
                    if instruction:
                        # Process the instruction
                        operations = self.parse_instructions(instruction + ';')
                        if operations:
                            self.execute_operations(operations)
                        else:
                            print("\nNo valid instructions found. Please check your input.")

        return True
    
    def save_current_state(self):
        """Save the current state with operation history in filename"""
        processed_dir = 'processed'
        os.makedirs(processed_dir, exist_ok=True)  # Ensure the directory exists

        # Get base name without extension
        base_name = os.path.splitext(os.path.basename(self.original_file))[0]
        
        # Get all operations up to current point
        operations_history = []
        for _, ops in list(self.history.history)[:self.history.current_index + 1]:
            operations_history.extend(ops)
        
        # Create operations string for filename
        if operations_history:
            operations_str = "_".join([f"{op['type']}{'_'.join(map(str, op['values']))}" for op in operations_history])  # Use 'values' instead of 'value'
        else:
            operations_str = "no_ops"
            
        # Create timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Create output filenames
        if "processed_" in base_name:
            base_name = base_name.split("_")
            output_name = f'{base_name[0]}_{operations_str}_{timestamp}_{("_").join(base_name[2:])}'
        else:
            output_name = f'processed_{operations_str}_{timestamp}_{base_name}'
            
        # Sanitize the output name to avoid invalid characters
        output_name = ''.join(c for c in output_name if c.isalnum() or c in ('_', '-'))  # Keep only valid characters

        # Truncate the output name if it's too long
        output_name = too_long_name_truncation(output_name)

        output_wav_file = os.path.join(processed_dir, output_name + ".wav")
        output_mp3_file = os.path.join(processed_dir, output_name + ".mp3")

        try:
            # Copy current working file
            shutil.copy2(self.working_file, output_wav_file)
            
            # Convert to MP3
            from pydub import AudioSegment
            sound = AudioSegment.from_wav(output_wav_file)
            sound.export(output_mp3_file, format="mp3")
            
            print(f"\nSaved WAV as: {output_wav_file}")
            print(f"Saved MP3 as: {output_mp3_file}")
            
        except Exception as e:
            print(f"\nError saving files: {str(e)}")

    def cleanup(self):
        """Clean up temporary files"""
        # self.playback.pause_playback()  # Remove this line if not needed
        try:
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"Error cleaning up temporary files: {str(e)}")

    def print_history_status(self):
        current = self.history.current_index + 1
        total = len(self.history.history)
        ops = self.history.current()[0]  # Operations are now first in tuple
        ops_str = " → ".join([f"{op['type']}:{'_'.join(map(str, op['values']))}" for op in ops]) if ops else "Original"
        print(f"\nState {current}/{total}: {ops_str}")
        print("> " + self.input_buffer, end='', flush=True)

    def apply_changes(self):
        """Apply changes to the track"""
        y, sr = sf.read(self.working_file)
        operations = self.history.current()[1]  # Get the operations from the current state
        y = self.apply_operations(y, operations)
        temp_file = os.path.join(self.temp_dir, f'temp_{datetime.now().strftime("%Y%m%d%H%M%S")}.wav')
        sf.write(temp_file, y, sr)
        self.history.add(temp_file, operations)
        shutil.copy2(temp_file, self.working_file)
        self.playback.load_audio(self.working_file)

    def parse_instructions(self, instructions):
        """Parse the instruction string into operations"""
        print("parsing instructions...", instructions)
        operations = []
        parts = instructions.split(';')
        for part in parts:
            if ':' in part:
                cmd, *args = part.split(':')  # Use unpacking to handle multiple arguments
                values = [float(arg.replace(',', '.')) for arg in args if arg]  # Convert arguments to float
                operations.append({'type': cmd, 'values': values})
                print(f"Operation: {{'type': {cmd}, 'values': {values}}}")
            else:
                if part:  # Ensure the part is not empty
                    operations.append({'type': part, 'values': []})
                    print(f"Operation: {{'type': {part}, 'values': []}}")
        return operations





