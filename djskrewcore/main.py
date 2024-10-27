import threading
import librosa
import soundfile as sf
import numpy as np
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
        while len(self.history) > self.current_index + 1:
            self.history.pop()
        self.history.append((state, operations))
        self.current_index = len(self.history) - 1
        
    def can_undo(self):
        return self.current_index > 0
        
    def can_redo(self):
        return self.current_index < len(self.history) - 1
        
    def undo(self):
        if self.can_undo():
            self.current_index -= 1
            return self.history[self.current_index]
        return None
        
    def redo(self):
        if self.can_redo():
            self.current_index += 1
            return self.history[self.current_index]
        return None
        
    def current(self):
        if self.current_index >= 0:
            return self.history[self.current_index]
        return None
        
    def get_operations_history(self):
        return [ops for _, ops in list(self.history)[:self.current_index + 1]]
        
    def cleanup(self):
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
        self.current_file_path = file_path  # Initialize current_file_path
        self.load_audio(file_path)
        
    def load_audio(self, file_path):
        if self.current_file_path != file_path:
            self.current_file_path = file_path
            try:
                audio_data, sr = sf.read(file_path, dtype='float32')
                if len(audio_data.shape) == 1:
                    self.audio_data = audio_data.reshape(-1, 1)
                else:
                    self.audio_data = audio_data
                self.current_position = min(self.current_position, len(self.audio_data)) if hasattr(self, 'current_position') else 0
            except Exception as e:
                print(f"Error loading audio: {str(e)}")
                self.audio_data = np.zeros((1024, 1), dtype='float32')
                self.current_position = 0

    def new_file_available(self, new_file_path):
        """Reload audio data only when a new file is available."""
        self.load_audio(new_file_path)
        
    def play_callback(self, outdata, frames, time, status):
        if status:
            print(status)
        if self.audio_data is None or self.current_position >= len(self.audio_data):
            self.current_position = 0
        try:
            remaining = len(self.audio_data) - self.current_position
            if remaining < frames:
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
                blocksize=2048,
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
    def __init__(self, file_path, config_file='commands.txt'):
        self.config_file = config_file
        self.commands = self.load_commands()
        self.original_file = file_path
        self.temp_dir = tempfile.mkdtemp()
        self.y, self.sr = librosa.load(file_path)
        self.working_file = os.path.join(self.temp_dir, 'working.wav')
        sf.write(self.working_file, self.y, self.sr)
        self.playback = AudioPlayback(self.working_file, self.sr)
        self.history = AudioHistory()
        self.history.add(self.working_file, [])
        self.input_buffer = ""
        self.playback_thread = threading.Thread(target=self.playback.start_playback)
        self.playback_thread.daemon = True
        self.playback_thread.start()

    def load_commands(self):
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
        instructions = instructions.strip()
        print(f"Processing instructions: '{instructions}'")

        if len(instructions) == 2 and instructions.endswith(';'):
            command = instructions[0]
            if command == 'q':
                print("Exiting the program...")
                sys.exit(0)
            elif command == 's':
                self.save_current_state()
                print("\nCurrent state saved.")
                return True
            elif command == 'a':
                self.apply_changes()
                print("\nChanges applied.")
                return True
            elif command == 'p':
                if self.playback:
                    self.playback.toggle_playback()
                    print("\nPlayback toggled.")
                else:
                    print("Playback instance not initialized.")
                return True
            elif command == 'u':
                self.undo()
                return True
            elif command == 'r':
                self.redo()
                return True
            elif command == 'l':
                self.load_new_file()
                return True
            elif command == 'h':
                self.print_help()
                return True

        if not instructions.endswith(';'):
            print("Incomplete instruction.")
            return True

        for command_name, command_value in self.commands.items():
            instructions = instructions.replace(command_name + ';', command_value + ';')

        operations = self.parse_instructions(instructions)
        if operations:
            self.execute_operations(operations)
        else:
            raise Exception("Couldn't parse instructions from " + instructions) 
            
        return True

    def execute_operations(self, operations):
        try:
            position = self.playback.current_position
            was_playing = self.playback.is_playing
            
            if was_playing:
                self.playback.pause_playback()
            
            for operation in operations:
                if operation['type'] == 'revert':
                    self.handle_revert_operation(operation)
                    return

            y, sr = sf.read(self.working_file)
            
            print("Applying operations...")
            for op in operations:
                print(f"Applying operation: {op['type']} with values {op['values']}")
            y = self.apply_operations(y, operations)
            print("Operations applied.")
            
            temp_file = os.path.join(self.temp_dir, f'temp_{datetime.now().strftime("%Y%m%d%H%M%S")}.wav')
            sf.write(temp_file, y, sr)
            
            self.history.add(temp_file, operations)
            self.working_file = temp_file
            
            self.notify_playback(self.working_file)
            
            if was_playing:
                self.playback.start_playback(position)
            
            print("\nOperations applied successfully")
            
        except Exception as e:
            print(f"\nError processing audio: {str(e)}")

    def handle_revert_operation(self, operation):
        steps = int(operation['values'][0])
        if steps > 0 and self.history.can_undo():
            for _ in range(steps):
                previous_state = self.history.undo()
                if previous_state:
                    file_path, _ = previous_state
                    shutil.copy2(file_path, self.working_file)
                    self.playback.load_audio(self.working_file)
        elif steps < 0 and self.history.can_redo():
            for _ in range(-steps):
                next_state = self.history.redo()
                if next_state:
                    file_path, _ = next_state
                    shutil.copy2(file_path, self.working_file)
                    self.playback.load_audio(self.working_file)
        self.print_history_status()

    def apply_operations(self, y, operations):
        y_original = y.copy()
        tempo, beats = librosa.beat.beat_track(y=y, sr=self.sr)
        beat_length = 60.0 / tempo  # Length of one beat in seconds
        
        for op in operations:
            try:
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
                    y = AudioEffects.reverse_by_beats(y, self.sr, beats, int(value1), int(value2), int(value3))
                elif op['type'] == 'speed':
                    y = AudioEffects.time_stretch(y, rate=float(value1))
                elif op['type'] == 'stut':
                    y = AudioEffects.add_stutter(y, self.sr, beats, int(value1), int(value2), int(value3))
                elif op['type'] == 'echo':
                    delay = value1 if value1 > 0 else beat_length
                    y = AudioEffects.add_echo(y, self.sr, delay, int(value2), value3)
                elif op['type'] == 'loop':
                    y = AudioEffects.create_loop(y, self.sr, beats, int(value1), int(value2), int(value3))
                elif op['type'] == 'chop':
                    y = AudioEffects.chop_and_rearrange(y, self.sr, beats, int(value1), int(value2), int(value3))
                elif op['type'] == 'mute':
                    y = AudioEffects.apply_frequency_muting(y, self.sr, threshold_db=value1)
                elif op['type'] == 'trig':
                    y = AudioEffects.apply_trigger_muting(y, self.sr, sensitivity=value1, beats=beats)
                elif op['type'] == 'del':
                    y = AudioEffects.delete_beat_parts(y, self.sr, beats, int(value1), int(value2), int(value3))
                elif op['type'] == 'n':
                    threshold = value1
                    preserve_ranges = [
                        (80, 1200),    # Voice fundamental frequencies
                        (2000, 4000)   # Voice harmonics and clarity
                    ]
                    y = AudioEffects.spectral_gate(y, self.sr, threshold_db=threshold, preserve_freq_ranges=preserve_ranges)
                elif op['type'] == 'perc':
                    y = AudioEffects.extract_percussive_track(y, self.sr)
                elif op['type'] == 'mash':
                    y = AudioEffects.random_mix_beats(y, self.sr, beats, int(value1), int(value2), int(value3))
                elif op['type'] == 'bpm':
                    target_bpm = value1
                    source_bpm = AudioEffects.estimate_bpm(y, self.sr)
                    y = AudioEffects.match_bpm(y, self.sr, source_bpm, target_bpm)
                elif op['type'] == 'a':
                    y = AudioEffects.resample_time(y, self.sr, rate=value1)
                else:
                    print(f"Warning: Unknown operation {op['type']}")

            except Exception as e:
                print(f"Warning: Operation {op['type']}:{values} failed: {str(e)}")
                continue

        return y

    
    def save_current_state(self):
        processed_dir = 'processed'
        os.makedirs(processed_dir, exist_ok=True)  # Ensure  the directory exists

        base_name = os.path.splitext(os.path.basename(self.original_file))[0]
        
        operations_history = []
        for _, ops in list(self.history.history)[:self.history.current_index + 1]:
            operations_history.extend(ops)
        
        if operations_history:
            operations_str = "_".join([f"{op['type']}{'_'.join(map(str, op['values']))}" for op in operations_history])
        else:
            operations_str = "no_ops"
            
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        if "processed_" in base_name:
            base_name = base_name.split("_")
            output_name = f'{base_name[0]}_{operations_str}_{timestamp}_{("_").join(base_name[2:])}'
        else:
            output_name = f'processed_{operations_str}_{timestamp}_{base_name}'
            
        output_name = ''.join(c for c in output_name if c.isalnum() or c in ('_', '-'))  # Keep only valid characters

        output_name = too_long_name_truncation(output_name)

        output_wav_file = os.path.join(processed_dir, output_name + ".wav")
        output_mp3_file = os.path.join(processed_dir, output_name + ".mp3")

        try:
            shutil.copy2(self.working_file, output_wav_file)
            
            from pydub import AudioSegment
            sound = AudioSegment.from_wav(output_wav_file)
            sound.export(output_mp3_file, format="mp3")
            
            print(f"\nSaved WAV as: {output_wav_file}")
            print(f"Saved MP3 as: {output_mp3_file}")
            
        except Exception as e:
            print(f"\nError saving files: {str(e)}")

    def cleanup(self):
        try:
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"Error cleaning up temporary files: {str(e)}")

    def print_history_status(self):
        current = self.history.current_index + 1
        total = len(self.history.history)
        _, ops = self.history.current()
        ops_str = " → ".join([f"{op['type']}:{'_'.join(map(str, op['values']))}" for op in ops]) if ops else "Original"
        print(f"\nState {current}/{total}: {ops_str}")
        print("> " + self.input_buffer, end='', flush=True)

    def apply_changes(self):
        y, sr = sf.read(self.working_file)
        operations = self.history.current()[1]  # Get the operations from the current state
        y = self.apply_operations(y, operations)
        temp_file = os.path.join(self.temp_dir, f'temp_{datetime.now().strftime("%Y%m%d%H%M%S")}.wav')
        sf.write(temp_file, y, sr)
        self.history.add(temp_file, operations)
        shutil.copy2(temp_file, self.working_file)
        self.playback.load_audio(self.working_file)

    def parse_instructions(self, instructions):
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

    def undo(self):
        if self.history.can_undo():
            previous_state = self.history.undo()
            if previous_state:
                file_path, _ = previous_state
                shutil.copy2(file_path, self.working_file)
                self.playback.load_audio(self.working_file)
                print("\nUndo successful.")
            self.print_history_status()
        else:
            print("\nCannot undo further.")

    def redo(self):
        if self.history.can_redo():
            next_state = self.history.redo()
            if next_state:
                file_path, _ = next_state
                shutil.copy2(file_path, self.working_file)
                self.playback.load_audio(self.working_file)
                print("\nRedo successful.")
            self.print_history_status()
        else:
            print("\nCannot redo further.")

    def load_new_file(self):
        new_file = input("Enter the path to the new audio file: ").strip()
        if os.path.exists(new_file):
            self.__init__(new_file, self.config_file)
            print(f"\nLoaded new file: {new_file}")
        else:
            print(f"\nFile not found: {new_file}")

    def notify_playback(self, new_file_path):
        """Notify the playback instance that a new file is ready."""
        self.playback.new_file_available(new_file_path)

    def print_help(self):
        print("\nAvailable commands:")
        print("q; - Quit the program")
        print("s; - Save current state")
        print("a; - Apply changes")
        print("p; - Toggle playback")
        print("u; - Undo last operation")
        print("r; - Redo last undone operation")
        print("l; - Load a new audio file")
        print("h; - Print this help message")
        print("\nFor other operations, use the format: operation:value1,value2,value3;")
        print("Example: p:2; (pitch shift by 2 semitones)")

def too_long_name_truncation(name, max_length=200):
    """Truncate the name if it's too long"""
    if len(name) <= max_length:
        return name
    
    # Split the name into parts
    parts = name.split('_')
    
    # Keep the first and last parts, and truncate the middle
    return f"{parts[0]}_{parts[1]}_.._{parts[-2]}_{parts[-1]}"
    def notify_playback(self, new_file_path):
        """Notify the playback instance that a new file is ready."""
        self.playback.new_file_available(new_file_path)
