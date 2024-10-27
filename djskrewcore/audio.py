from typing import Optional, List, Tuple, Dict, Any
import os
import threading
import queue
import tempfile
import shutil
from datetime import datetime
from collections import deque
import librosa
import soundfile as sf
import numpy as np
import sounddevice as sd
from djskrewcore.effects import AudioEffects
import re
import time
import traceback
from pydub import AudioSegment

class AudioHistory:
    def __init__(self, max_size: int = 50):
        self.history: deque = deque(maxlen=max_size)
        self.current_index: int = -1
        
    def add(self, state: str, operations: List[Dict[str, Any]]) -> None:
        # Only add to history if operations actually modify the state
        if operations and (not self.history or self.history[-1][0] != state):
            while len(self.history) > self.current_index + 1:
                self.history.pop()
            self.history.append((state, operations))
            self.current_index = len(self.history) - 1
        
    def can_undo(self) -> bool:
        return self.current_index > 0
        
    def can_redo(self) -> bool:
        return self.current_index < len(self.history) - 1
        
    def undo(self) -> Optional[Tuple[str, List[Dict[str, Any]]]]:
        if self.can_undo():
            self.current_index -= 1
            return self.history[self.current_index]
        return None
        
    def redo(self) -> Optional[Tuple[str, List[Dict[str, Any]]]]:
        if self.can_redo():
            self.current_index += 1
            return self.history[self.current_index]
        return None
        
    def current(self) -> Optional[Tuple[str, List[Dict[str, Any]]]]:
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

class AudioPlayer:
    def __init__(self, sr: int):
        self.sr = sr
        self.is_playing = False
        self.stream: Optional[sd.OutputStream] = None
        self.audio_data: Optional[np.ndarray] = None
        self.current_position = 0
        self._lock = threading.Lock()
        
    def load_audio(self, file_path: str) -> None:
        with self._lock:
            try:
                audio_data, sr = sf.read(file_path, dtype='float32')
                if len(audio_data.shape) == 1:
                    self.audio_data = audio_data.reshape(-1, 1)
                else:
                    self.audio_data = audio_data
                self.current_position = min(self.current_position, len(self.audio_data))
            except Exception as e:
                print(f"Error loading audio: {str(e)}")
                self.audio_data = np.zeros((1024, 1), dtype='float32')
                self.current_position = 0
        
    def start_playback(self, position: Optional[int] = None) -> None:
        with self._lock:
            if position is not None:
                self.current_position = min(position, len(self.audio_data))
            if self.stream is not None:
                self.stream.close()
            try:
                self.stream = sd.OutputStream(
                    samplerate=self.sr,
                    channels=self.audio_data.shape[1] if len(self.audio_data.shape) > 1 else 1,
                    callback=self._play_callback,
                    blocksize=2048,
                    dtype=self.audio_data.dtype
                )
                self.stream.start()
                self.is_playing = True
            except Exception as e:
                print(f"Error starting playback: {str(e)}")
                self.is_playing = False

    def pause_playback(self) -> None:
        with self._lock:
            if self.stream is not None:
                try:
                    self.stream.close()
                    self.stream = None
                    self.is_playing = False
                except Exception as e:
                    print(f"Error pausing playback: {str(e)}")
            
    def toggle_playback(self) -> None:
        if self.is_playing:
            self.pause_playback()
        else:
            self.start_playback(self.current_position)

    def _play_callback(self, outdata: np.ndarray, frames: int, 
                      time: Any, status: Optional[sd.CallbackFlags]) -> None:
        if status:
            print(status)
            
        with self._lock:
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

class AudioProcessor:
    def __init__(self, temp_dir: str):
        self.temp_dir = temp_dir
        self.processing_queue: queue.Queue = queue.Queue()
        self.completion_callbacks: Dict[int, Any] = {}
        self.current_operation_id = 0
        self._lock = threading.Lock()
        self._processing_thread = threading.Thread(target=self._processing_loop)
        self._processing_thread.daemon = True
        self._processing_thread.start()

    def process_audio(self, input_file: str, operations: List[Dict[str, Any]], 
                     callback: Any) -> int:
        with self._lock:
            operation_id = self.current_operation_id
            self.current_operation_id += 1
            
            output_file = os.path.join(
                self.temp_dir, 
                f"processed_{operation_id}_{os.path.basename(input_file)}"
            )
            
            self.completion_callbacks[operation_id] = callback
            self.processing_queue.put((operation_id, input_file, output_file, operations))
            
            return operation_id

    def _processing_loop(self) -> None:
        while True:
            try:
                operation_id, input_file, output_file, operations = self.processing_queue.get()
                
                try:
                    y, sr = librosa.load(input_file, sr=None)
                    modified_audio = np.copy(y)

                    for operation in operations:
                        modified_audio = self._apply_effect(modified_audio, sr, operation)

                    sf.write(output_file, modified_audio, sr)

                    callback = self.completion_callbacks.get(operation_id)
                    if callback:
                        callback(output_file)
                        del self.completion_callbacks[operation_id]

                except Exception as e:
                    print(f"Processing error for operation {operation_id}:")
                    print(f"Input file: {input_file}")
                    print(f"Output file: {output_file}")
                    print(f"Operations: {operations}")
                    print(f"Error details: {str(e)}")
                    traceback.print_exc()

            except queue.Empty:
                continue

    def _apply_effect(self, audio, sr, operation):
        effect_type = operation['type']
        values = operation['values']

        try:
            if effect_type == 'rt' and len(values) >= 1:
                return AudioEffects.resample_time(audio, sr, rate=float(values[0]))
            elif effect_type == 'a' and len(values) >= 1:
                return AudioEffects.resample_time(audio, sr, rate=float(values[0]))
            elif effect_type == 't' and len(values) >= 1:
                return AudioEffects.time_stretch(audio, rate=float(values[0]))
            elif effect_type == 'p' and len(values) >= 1:
                return AudioEffects.pitch_shift(audio, sr, n_steps=float(values[0]))
            elif effect_type == 'bpm' and len(values) >= 1:
                target_bpm = float(values[0])
                if target_bpm < 20:  # Set a minimum BPM threshold
                    print(f"Warning: BPM value {target_bpm} is too low. Setting to minimum of 20 BPM.")
                    target_bpm = 20
                source_bpm = AudioEffects.estimate_bpm(audio, sr)
                return AudioEffects.match_bpm(audio, sr, source_bpm, target_bpm)
            elif effect_type == 'stut' and len(values) >= 4:
                return AudioEffects.add_stutter(audio, sr, beats=int(values[0]), count=int(values[1]), length=float(values[2]), repeat=int(values[3]))
            elif effect_type == 'chop' and len(values) >= 4:
                return AudioEffects.chop_and_rearrange(audio, sr, beats=int(values[0]), size=int(values[1]), step=int(values[2]), repeat=int(values[3]))
            elif effect_type == 'echo' and len(values) >= 3:
                return AudioEffects.add_echo(audio, sr, delay=float(values[0]), count=int(values[1]), decay=float(values[2]))
            elif effect_type == 'mash' and len(values) >= 4:
                return AudioEffects.random_mix_beats(audio, sr, beats=int(values[0]), parts=int(values[1]), beats_per_mash=int(values[2]), repeat=int(values[3]))
            elif effect_type == 'loop' and len(values) >= 4:
                return AudioEffects.create_loop(audio, sr, beats=int(values[0]), interval=int(values[1]), length=int(values[2]), repeat=int(values[3]))
            elif effect_type == 'rev' and len(values) >= 4:
                return AudioEffects.reverse_by_beats(audio, sr, beats=int(values[0]), interval=int(values[1]), length=int(values[2]), repeat=int(values[3]))
            else:
                print(f"Warning: Unknown operation '{effect_type}' or insufficient parameters.")
                return audio

        except ValueError as ve:
            print(f"Error in {effect_type} effect: Invalid parameter value.")
            print(f"Details: {str(ve)}")
            print(f"Provided values: {values}")
            print("This might be due to incompatible audio length, beat settings, or incorrect parameter types.")
            return audio

        except TypeError as te:
            print(f"Error in {effect_type} effect: Incorrect parameter type.")
            print(f"Details: {str(te)}")
            print(f"Provided values: {values}")
            print("Please check that all parameters are of the correct type (int, float, etc.).")
            return audio

        except Exception as e:
            print(f"Unexpected error in {effect_type} effect:")
            print(f"Details: {str(e)}")
            print(f"Provided values: {values}")
            print("Stack trace:")
            traceback.print_exc()
            return audio

class AudioManager:
    def __init__(self, input_file: str):
        self.input_file = input_file
        self.y, self.sr = librosa.load(input_file, sr=None)
        self.working_audio = np.copy(self.y)
        self.temp_dir = tempfile.mkdtemp()
        self.history = []
        self.undo_stack = []
        self.redo_stack = []
        
        # Initialize components
        self.player = AudioPlayer(self.sr)
        self.processor = AudioProcessor(self.temp_dir)
        self.history = AudioHistory()
        
        # Set up initial state
        self.working_file = os.path.join(self.temp_dir, 'working.wav')
        sf.write(self.working_file, self.y, self.sr)
        self.player.load_audio(self.working_file)
        self.history.add(self.working_file, [])
        self.change_counter = 0

    def process_instructions(self, instructions: str) -> bool:
        # Handle special commands
        if len(instructions) == 2 and instructions.endswith(';'):
            command = instructions[0]
            return self._handle_special_command(command)

        # Parse and process regular instructions
        operations = self._parse_instructions(instructions)
        if operations:
            self._process_operations(operations)
        return True

    def _handle_special_command(self, command: str) -> bool:
        if command == 'q':
            return False
        elif command == 's':
            self._save_current_state()
        elif command == 'p':
            self.player.toggle_playback()
        elif command == 'u':
            self._undo()
        elif command == 'r':
            self._redo()
        elif command == 'h':
            self._print_help()
        elif command == 'o':
            self._get_operations_history()
        return True

    def _process_operations(self, operations: List[Dict[str, Any]]) -> None:
        def process_complete(output_file: str) -> None:
            self.working_file = output_file
            self.player.load_audio(output_file)
            print("Operation completed successfully.")

        current_input = self.working_file
        for operation in operations:
            operation_id = self.processor.process_audio(
                current_input,
                [operation],
                process_complete
            )
            # Wait for the operation to complete
            while operation_id in self.processor.completion_callbacks:
                time.sleep(0.1)
            current_input = self.working_file

        # After all operations are complete, update history
        self.history.add(self.working_file, operations)
        print("Track updated successfully with the following operations:")
        for op in operations:
            print(op)

    def cleanup(self) -> None:
        try:
            self.player.pause_playback()
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"Error cleaning up: {str(e)}")

    def _parse_instructions(self, instructions: str) -> List[Dict[str, Any]]:
        operations = []
        for instruction in instructions.split(';'):
            if instruction.strip():
                parts = instruction.split(':')
                effect_type = parts[0]
                values = [float(v) for v in parts[1:]]
                operations.append({'type': effect_type, 'values': values})
        return operations

    def _undo(self) -> None:
        previous_state = self.history.undo()
        if previous_state:
            file_path, operations = previous_state
            self.player.load_audio(file_path)
            print("Undo successful.")
        else:
            print("No more undos available.")

    def _redo(self) -> None:
        next_state = self.history.redo()
        if next_state:
            file_path, operations = next_state
            self.player.load_audio(file_path)
            print("Redo successful.")
        else:
            print("No more redos available.")

    def _sanitize_filename(self, filename: str) -> str:
        # Remove or replace any characters that are not suitable for file names
        return re.sub(r'[^\w\s-]', '', filename).strip().replace(' ', '_')

    def _save_current_state(self) -> None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        processed_folder = os.path.join(script_dir, "processed")
        os.makedirs(processed_folder, exist_ok=True)

        base_name = os.path.basename(self.input_file)
        name_without_extension = os.path.splitext(base_name)[0]
        sanitized_name = self._sanitize_filename(name_without_extension)

        # Save WAV file
        wav_file_name = f"processed_{self.change_counter}_{sanitized_name}.wav"
        wav_file_path = os.path.join(processed_folder, wav_file_name)
        shutil.copy2(self.working_file, wav_file_path)
        print(f"Current state saved as WAV: {wav_file_path}")

        # Save MP3 file
        mp3_file_name = f"processed_{self.change_counter}_{sanitized_name}.mp3"
        mp3_file_path = os.path.join(processed_folder, mp3_file_name)
        
        # Convert WAV to MP3
        audio = AudioSegment.from_wav(wav_file_path)
        audio.export(mp3_file_path, format="mp3")
        print(f"Current state saved as MP3: {mp3_file_path}")

        # Increment the change counter after saving
        self.change_counter += 1

    def _get_operations_history(self):
        operations_history = self.history.get_operations_history()
        print("Operations History:")
        for ops in operations_history:
            print(ops)

def print_help():
    print("\nAvailable Commands:")
    print("  p:<n_steps>          - Pitch shift by n_steps semitones")
    print("  rt:<rate>            - Resample time stretch by rate")
    print("  t:<rate>             - Time stretch by rate")
    print("  stut:<count>:<length>:<repeat> - Add stutter effect")
    print("  chop:<size>:<step>:<repeat>    - Chop and rearrange")
    print("  echo:<delay>:<count>:<decay>   - Add echo effect")
    print("  mash:<parts>:<beats_per_mash>:<repeat> - Random mix beats")
    print("  loop:<interval>:<length>:<repeat> - Create loop effect")
    print("  rev:<interval>:<length>:<repeat> - Reverse by beats")
    print("  bpm:<target_bpm>     - Match BPM to target")
    print("  a:<rate>             - Resample time stretch by rate")
    print("  help;                - Show this help message")
    
    print("\nExamples of Usage:")
    print("  python cli.py 'audio.mp3' 'audio.mp3' 'p:2;rt:1.5;chop:4:2:1;'")
    print("  python cli.py 'audio.mp3' 'audio.mp3' 'loop:1:4:2;echo:0.5:3:0.7;'")
    print("  python cli.py 'audio.mp3' 'audio.mp3' 'rev:2:2:2;stut:1:3:1;'")
    print("  python cli.py 'audio.mp3' 'audio.mp3' 'bpm:120;t:0.8;'")
    print("  python cli.py 'audio.mp3' 'audio.mp3' 'help;'")
    print("\nNote: All instructions must end with a semicolon (;)\n")

