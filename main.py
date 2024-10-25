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


    def spectral_gate(self, y, sr, threshold_db=-50, preserve_freq_ranges=None):
        """
        Apply spectral gating to remove noise while preserving specific frequency ranges.
        
        Parameters:
        y (np.ndarray): Input audio signal
        sr (int): Sample rate
        threshold_db (float): Threshold in dB below which to gate frequencies
        preserve_freq_ranges (list): List of tuples of (min_freq, max_freq) to preserve
        """
        import librosa
        import numpy as np
        
        # Compute STFT
        D = librosa.stft(y)
        mag, phase = librosa.magphase(D)
        
        # Convert to dB scale
        mag_db = librosa.amplitude_to_db(mag)
        
        # Create a mask based on threshold
        mask = mag_db > threshold_db
        
        # If there are frequency ranges to preserve
        if preserve_freq_ranges:
            # Get frequency values for each bin
            freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
            
            # For each range to preserve
            for min_freq, max_freq in preserve_freq_ranges:
                # Find bins in the preserve range
                preserve_mask = (freqs >= min_freq) & (freqs <= max_freq)
                # Add these bins to the mask
                mask[preserve_mask] = True
        
        # Apply the mask
        mag_filtered = mag * mask
        
        # Reconstruct signal
        y_filtered = librosa.istft(mag_filtered * phase)
        
        return y_filtered

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
                command = self.input_buffer.strip()
                if command == 'q;':
                    return False
                elif command == 's;':
                    self.save_current_state()
                    self.input_buffer = ""
                    print("\n> ", end='', flush=True) 
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
    
    def save_current_state(self):
        """Save the current state with operation history in filename"""
        processed_dir = 'processed'
        os.makedirs(processed_dir, exist_ok=True)

        # Get base name without extension
        base_name = os.path.splitext(os.path.basename(self.original_file))[0]
        
        # Get all operations up to current point
        operations_history = []
        for _, ops in list(self.history.history)[:self.history.current_index + 1]:
            operations_history.extend(ops)
        
        # Create operations string for filename
        if operations_history:
            operations_str = "_".join([f"{op['type']}{op['value']}" for op in operations_history])
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



    def print_history_status(self):
        current = self.history.current_index + 1
        total = len(self.history.history)
        ops = self.history.current()[0]  # Operations are now first in tuple
        ops_str = " → ".join([f"{op['type']}:{op['value']}" for op in ops]) if ops else "Original"
        print(f"\nState {current}/{total}: {ops_str}")
        print("> " + self.input_buffer, end='', flush=True)
    
    def apply_operations(self, y, operations):
        """Apply audio operations"""
        y_original = y.copy()
        
        # Detect BPM at the start
        tempo, beats = librosa.beat.beat_track(y=y, sr=self.sr)
        beat_length = 60.0 / tempo  # Length of one beat in seconds
        
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
                elif op['type'] == 'rev':
                    y = reverse_by_beats(y, self.sr, beats, op['value'], op['n'], op['m'])
                elif op['type'] == 'speed':
                    y = librosa.effects.time_stretch(y, rate=float(op['value']))
                elif op['type'] == 'stut':
                    y = add_stutter(y, self.sr, beats, rate=op['value'], n=op['n'], m=op['m'])
                elif op['type'] == 'echo':
                    delay = op['value'] if op['value'] > 0 else beat_length
                    y = add_echo(y, self.sr, delay=delay, beats=beats, n=op['n'], m=op['m'])
                elif op['type'] == 'loop':
                    beats_per_loop = op['value'] if op['value'] > 0 else 4
                    y = create_loop(y, self.sr, beats, beats_per_loop, n=op['n'], m=op['m'])
                elif op['type'] == 'chop':
                    beats_per_chunk = op['value'] if op['value'] > 0 else 2
                    y = chop_and_rearrange(y, self.sr, beats, beats_per_chunk, n=op['n'], m=op['m'])
                elif op['type'] == 'mute':
                    # Mute frequencies below threshold with drum decay
                    y = apply_frequency_muting(y, self.sr, threshold_db=op['value'])
                elif op['type'] == 'trig':
                    # Trigger-based muting with adjustable sensitivity
                    y = apply_trigger_muting(y, self.sr, sensitivity=op['value'], beats=beats)
                elif op['type'] == 'n':
                    threshold = op['value']
                    preserve_ranges = [
                        (80, 1200),    # Voice fundamental frequencies
                        (2000, 4000)   # Voice harmonics and clarity
                    ]
                    y = self.spectral_gate(y, self.sr, threshold_db=threshold, preserve_freq_ranges=preserve_ranges)
                elif op['type'] == 'perc':
                    y = extract_percussive_track(y, self.sr)
                elif op['type'] == 'copy':
                    start_byte = int(op['value'])
                    num_bytes = int(op['value2']) if 'value2' in op else 1
                    y[start_byte:start_byte + num_bytes] = y[start_byte]
        
            except Exception as e:
                print(f"Warning: Operation {op['type']}:{op['value']} failed: {str(e)}")
                continue

        preserve_ranges = [
                        (80, 1200),    # Voice fundamental frequencies
                        (2000, 4000)   # Voice harmonics and clarity
                    ]
        y = self.spectral_gate(y, self.sr, preserve_freq_ranges=preserve_ranges)
        # Match characteristics
        y = match_frequency_profile(y, y_original, self.sr)
        y = match_loudness(y, y_original, self.sr)
        
        return y

def get_beat_frames(beats, sr, hop_length=512):
    """Convert beat positions to frame indices"""
    return librosa.frames_to_samples(beats, hop_length=hop_length)

def reverse_by_beats(y, sr, beats, num_beats=4, n=1, m=1):
    """
    Reverse audio in chunks of specified beats
    num_beats: number of beats per reversed chunk
    """
    # Get beat frames
    beat_frames = get_beat_frames(beats, sr)
    
    # Create output array
    output = np.zeros_like(y)
    
    # Process in chunks of num_beats
    for i in range(0, len(beat_frames) - num_beats, num_beats * m):
        if (i // num_beats) % n == 0:
            start = beat_frames[i]
            end = beat_frames[i + num_beats] if i + num_beats < len(beat_frames) else len(y)
            
            # Reverse this chunk
            chunk = y[start:end]
            output[start:end] = chunk[::-1]
            
            # Apply crossfade
            if i > 0:
                crossfade_length = min(1024, end - start)
                fade_in = np.linspace(0, 1, crossfade_length)
                fade_out = np.linspace(1, 0, crossfade_length)
                output[start:start + crossfade_length] *= fade_in
                output[start - crossfade_length:start] *= fade_out
    
    return output

def add_stutter(y, sr, beats, rate=1.0, n=1, m=1):
    """
    Add stutter effect synchronized with beats
    rate: number of stutters per beat (1.0 = one stutter per beat)
    """
    beat_frames = get_beat_frames(beats, sr)
    output = np.zeros_like(y)
    
    # Copy original signal
    output[:] = y[:]
    
    # Add stutters at beat positions
    for i in range(0, len(beat_frames) - 1, m):
        if (i // m) % n == 0:
        beat_start = beat_frames[i]
        beat_end = beat_frames[i + 1]
        beat_length = beat_end - beat_start
        
        # Number of stutters for this beat
        num_stutters = int(rate)
        if num_stutters > 0:
            stutter_length = beat_length // num_stutters
            
            for j in range(num_stutters):
                # Get segment to repeat
                segment_start = beat_start + (j * stutter_length)
                segment = y[segment_start:segment_start + stutter_length]
                
                # Apply fade envelope
                fade = np.linspace(1.0, 0.0, len(segment)) ** 2
                
                # Add stuttered segment
                if segment_start + len(segment) <= len(output):
                    output[segment_start:segment_start + len(segment)] += segment * fade
    
    # Normalize
    output = output / np.max(np.abs(output))
    return output

def add_echo(y, sr, delay, beats, decay=0.5, n=1, m=1):
    """
    Add echo effect synchronized with beats
    delay: echo delay in seconds (if 0, uses one beat length)
    """
    if delay <= 0:
        if len(beats) >= 2:
            # Use average beat length for delay
            beat_frames = get_beat_frames(beats, sr)
            delays = np.diff(beat_frames)
            delay = np.mean(delays) / sr
        else:
            delay = 0.25  # Default to 250ms if no beats detected
    
    # Convert delay to samples
    delay_samples = int(sr * delay)
    
    # Create output array
    output = np.zeros(len(y) + delay_samples)
    
    # Add original signal
    output[:len(y)] = y
    
    # Add multiple echoes
    for i in range(1, 4):  # Add 3 echoes with decreasing volume
        if (i // m) % n == 0:
        echo_delay = delay_samples * i
        if echo_delay + len(y) <= len(output):
            output[echo_delay:echo_delay + len(y)] += y * (decay ** i)
    
    # Trim to original length
    output = output[:len(y)]
    
    # Normalize
    output = output / np.max(np.abs(output))
    return output

def create_loop(y, sr, beats, beats_per_loop=4, loop_portion=0.5, n=1, m=1):
    """
    Create loops synchronized with beats
    beats_per_loop: number of beats per loop
    loop_portion: portion of the beat to loop (0.0 to 1.0)
    """
    beat_frames = get_beat_frames(beats, sr)
    
    if len(beat_frames) < beats_per_loop + 1:
        return y
    
    # Create output array
    output = np.zeros_like(y)
    
    # Loop through beats and create loops
    for i in range(0, len(beat_frames) - 1, m):
        if (i // m) % n == 0:
        start = beat_frames[i]
        end = beat_frames[i + 1]
        beat_length = end - start
        
        # Determine loop start and end within the beat
        loop_start = start + int(beat_length * (1 - loop_portion))
        loop_end = end
        
        # Extract loop portion
        loop = y[loop_start:loop_end]
        
        # Apply crossfade
        crossfade_length = min(1024, len(loop) // 4)
        fade_in = np.linspace(0, 1, crossfade_length)
        fade_out = np.linspace(1, 0, crossfade_length)
        
        loop[-crossfade_length:] *= fade_out
        loop[:crossfade_length] *= fade_in
        
        # Repeat loop portion
        num_loops = int(np.ceil(beat_length / len(loop)))
        loop_repeated = np.tile(loop, num_loops)[:beat_length]
        
        # Add to output
        output[start:end] += loop_repeated
    
    # Normalize
    output = output / np.max(np.abs(output))
    return output

def chop_and_rearrange(y, sr, beats, beats_per_chunk=2, n=1, m=1):
    """
    Chop audio into beat-sized chunks and rearrange them
    beats_per_chunk: number of beats per chunk
    """
    beat_frames = get_beat_frames(beats, sr)
    
    if len(beat_frames) < beats_per_chunk + 1:
        return y
        
    # Create chunks
    chunks = []
    for i in range(0, len(beat_frames) - beats_per_chunk, beats_per_chunk * m):
        if (i // beats_per_chunk) % n == 0:
        start = beat_frames[i]
        end = beat_frames[i + beats_per_chunk]
        chunks.append(y[start:end])
    
    if not chunks:
        return y
    
    # Rearrange chunks in an interesting pattern
    # Example pattern: 1, 2, 2, 1, 3, 3, 2, 1
    pattern = []
    for i in range(len(chunks)):
        pattern.extend([i, i, (i + 1) % len(chunks)])
    
    # Create output
    output = np.zeros_like(y)
    pos = 0
    crossfade_length = min(1024, len(chunks[0]) // 4)
    
    for idx in pattern:
        if pos + len(chunks[idx]) > len(output):
            break
            
        # Add chunk with crossfade
        if pos > 0:
            # Crossfade with previous chunk
            fade_in = np.linspace(0, 1, crossfade_length)
            fade_out = np.linspace(1, 0, crossfade_length)
            output[pos:pos + crossfade_length] *= fade_out
            chunk_data = chunks[idx].copy()
            chunk_data[:crossfade_length] *= fade_in
            output[pos:pos + len(chunk_data)] += chunk_data
        else:
            output[pos:pos + len(chunks[idx])] = chunks[idx]
            
        pos += len(chunks[idx])
    
    # Trim to original length and normalize
    output = output[:len(y)]
    output = output / np.max(np.abs(output))
    return output

def parse_instructions(instructions):
    """Parse the instruction string into operations"""
    operations = []
    pattern = r"(chop|rev|speed|stut|echo|loop|rt|[ptr]):(-?\d*[.,]?\d+);?"
    matches = re.finditer(pattern, instructions)

    for match in matches:
        cmd_type, value = match.groups()
        value = float(value.replace(',', '.'))
        operations.append({'type': cmd_type, 'value': value})

    return operations

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
    
    def apply_operations(self, y, operations):
        """Apply audio operations"""
        y_original = y.copy()
        
        # Detect BPM at the start
        tempo, beats = librosa.beat.beat_track(y=y, sr=self.sr)
        beat_length = 60.0 / tempo  # Length of one beat in seconds
        
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
                elif op['type'] == 'rev':
                    y = reverse_by_beats(y, self.sr, beats, op['value'])
                elif op['type'] == 'speed':
                    y = librosa.effects.time_stretch(y, rate=float(op['value']))
                elif op['type'] == 'stut':
                    y = add_stutter(y, self.sr, beats, rate=op['value'])
                elif op['type'] == 'echo':
                    delay = op['value'] if op['value'] > 0 else beat_length
                    y = add_echo(y, self.sr, delay=delay, beats=beats)
                elif op['type'] == 'loop':
                    beats_per_loop = op['value'] if op['value'] > 0 else 4
                    y = create_loop(y, self.sr, beats, beats_per_loop)
                elif op['type'] == 'chop':
                    beats_per_chunk = op['value'] if op['value'] > 0 else 2
                    y = chop_and_rearrange(y, self.sr, beats, beats_per_chunk)
                elif op['type'] == 'mute':
                    # Mute frequencies below threshold with drum decay
                    y = apply_frequency_muting(y, self.sr, threshold_db=op['value'])
                elif op['type'] == 'trig':
                    # Trigger-based muting with adjustable sensitivity
                    y = apply_trigger_muting(y, self.sr, sensitivity=op['value'], beats=beats)
                elif op['type'] == 'n':
                    threshold = op['value']
                    preserve_ranges = [
                        (80, 1200),    # Voice fundamental frequencies
                        (2000, 4000)   # Voice harmonics and clarity
                    ]
                    y = self.spectral_gate(y, self.sr, threshold_db=threshold, preserve_freq_ranges=preserve_ranges)
        
            except Exception as e:
                print(f"Warning: Operation {op['type']}:{op['value']} failed: {str(e)}")
                continue

        preserve_ranges = [
                        (80, 1200),    # Voice fundamental frequencies
                        (2000, 4000)   # Voice harmonics and clarity
                    ]
        y = self.spectral_gate(y, self.sr, preserve_freq_ranges=preserve_ranges)
        # Match characteristics
        y = match_frequency_profile(y, y_original, self.sr)
        y = match_loudness(y, y_original, self.sr)
        
        return y


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

def apply_frequency_muting(y, sr, threshold_db=-40, frame_length=2048, hop_length=512):
    """
    Mute frequencies below threshold with drum-like decay
    threshold_db: threshold in dB below which to mute frequencies
    """
    # Compute STFT
    D = librosa.stft(y, n_fft=frame_length, hop_length=hop_length)
    
    # Get magnitude and phase
    mag, phase = librosa.magphase(D)
    
    # Convert to dB scale
    mag_db = librosa.amplitude_to_db(mag)
    
    # Create mask based on threshold
    mask = mag_db > threshold_db
    
    # Create a standard envelope for the frame length
    frame_envelope = create_drum_envelope(frame_length//2 + 1, sr)  # match STFT frequency bins
    
    # For each time frame where we have frequencies above threshold
    for frame in range(mask.shape[1]):
        if np.any(mask[:, frame]):
            # Apply envelope to the entire frequency range
            mag[:, frame] = mag[:, frame] * frame_envelope
            
    # Apply threshold mask
    mag = mag * mask
    
    # Reconstruct signal
    y_filtered = librosa.istft(mag * phase, hop_length=hop_length)
    
    # Ensure output length matches input
    if len(y_filtered) > len(y):
        y_filtered = y_filtered[:len(y)]
    elif len(y_filtered) < len(y):
        y_filtered = np.pad(y_filtered, (0, len(y) - len(y_filtered)))
    
    return y_filtered

def extract_percussive_track(y, sr, frame_length=2048, hop_length=512, threshold_db=-40):
    """
    Extract percussive components from the audio signal.
    """
    y_harmonic, y_percussive = librosa.effects.hpss(y)
    
    # Compute STFT
    D = librosa.stft(y, n_fft=frame_length, hop_length=hop_length)
    
    # Get magnitude and phase
    mag, phase = librosa.magphase(D)
    
    # Convert to dB scale
    mag_db = librosa.amplitude_to_db(mag)
    
    # Create mask based on threshold
    mask = mag_db > threshold_db
    
    # Create a standard envelope for the frame length
    frame_envelope = create_drum_envelope(frame_length//2 + 1, sr)  # match STFT frequency bins
    
    # For each time frame where we have frequencies above threshold
    for frame in range(mask.shape[1]):
        if np.any(mask[:, frame]):
            # Apply envelope to the entire frequency range
            mag[:, frame] = mag[:, frame] * frame_envelope
            
    # Apply threshold mask
    mag = mag * mask
    
    # Reconstruct signal
    y_filtered = librosa.istft(mag * phase, hop_length=hop_length)
    
    # Ensure output length matches input
    if len(y_filtered) > len(y):
        y_filtered = y_filtered[:len(y)]
    elif len(y_filtered) < len(y):
        y_filtered = np.pad(y_filtered, (0, len(y) - len(y_filtered)))
    
    return y_filtered
    """
    Mute frequencies below threshold with drum-like decay
    threshold_db: threshold in dB below which to mute frequencies
    """
    # Compute STFT
    D = librosa.stft(y, n_fft=frame_length, hop_length=hop_length)
    
    # Get magnitude and phase
    mag, phase = librosa.magphase(D)
    
    # Convert to dB scale
    mag_db = librosa.amplitude_to_db(mag)
    
    # Create mask based on threshold
    mask = mag_db > threshold_db
    
    # Create a standard envelope for the frame length
    frame_envelope = create_drum_envelope(frame_length//2 + 1, sr)  # match STFT frequency bins
    
    # For each time frame where we have frequencies above threshold
    for frame in range(mask.shape[1]):
        if np.any(mask[:, frame]):
            # Apply envelope to the entire frequency range
            mag[:, frame] = mag[:, frame] * frame_envelope
            
    # Apply threshold mask
    mag = mag * mask
    
    # Reconstruct signal
    y_filtered = librosa.istft(mag * phase, hop_length=hop_length)
    
    # Ensure output length matches input
    if len(y_filtered) > len(y):
        y_filtered = y_filtered[:len(y)]
    elif len(y_filtered) < len(y):
        y_filtered = np.pad(y_filtered, (0, len(y) - len(y_filtered)))
    
    return y_filtered

def create_drum_envelope(length, sr, decay=0.1):
    """
    Create a drum-like decay envelope
    length: number of samples
    sr: sample rate
    decay: decay time in seconds
    """
    t = np.linspace(0, length/sr, length)
    # Exponential decay with quick attack
    attack = 0.005  # 5ms attack time
    attack_samples = int(attack * sr)
    attack_samples = min(attack_samples, length//4)  # Ensure attack isn't too long
    
    envelope = np.zeros(length)
    # Attack phase
    if attack_samples > 0:
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
    # Decay phase
    decay_samples = length - attack_samples
    if decay_samples > 0:
        envelope[attack_samples:] = np.exp(-np.linspace(0, 3, decay_samples))
    
    # Normalize envelope
    envelope = envelope / np.max(envelope)
    
    return envelope

def apply_trigger_muting(y, sr, sensitivity=0.5, beats=None, frame_length=2048, hop_length=512):
    """
    Apply trigger-based muting with drum-like decay
    sensitivity: threshold for triggering (0.0 to 1.0)
    """
    # Convert sensitivity to absolute threshold
    rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)
    threshold = np.max(rms) * sensitivity
    
    # Get onset strength
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    
    # Detect onsets
    onsets = librosa.onset.onset_detect(
        onset_envelope=onset_env,
        sr=sr,
        units='samples',
        threshold=sensitivity
    )
    
    # Create output signal
    y_out = np.zeros_like(y)
    
    # For each onset
    for i, onset in enumerate(onsets):
        # Determine segment length (until next onset or end)
        if i < len(onsets) - 1:
            segment_length = onsets[i + 1] - onset
        else:
            segment_length = len(y) - onset
            
        # Create drum envelope for this segment
        envelope = create_drum_envelope(segment_length, sr)
        
        # Apply envelope to segment
        if onset + segment_length <= len(y):
            y_out[onset:onset + segment_length] = y[onset:onset + segment_length] * envelope
    
    return y_out

def parse_instructions(instructions):
    """Parse the instruction string into operations"""
    operations = []
    # Added mute and trig to the pattern
    pattern = r"(mute|trig|chop|rev|speed|stut|echo|loop|rt|perc|copy|[ptr]):(-?\d*[.,]?\d+)(?::(-?\d*[.,]?\d+))?(?::(-?\d*[.,]?\d+))?(?::(-?\d*[.,]?\d+))?;?"
    matches = re.finditer(pattern, instructions)

    for match in matches:
        cmd_type, value, value2, n, m = match.groups()
        value = float(value.replace(',', '.'))
        if value2:
            value2 = float(value2.replace(',', '.'))
        else:
            value2 = None
        if n:
            n = int(n.replace(',', '.'))
        else:
            n = 1
        if m:
            m = int(m.replace(',', '.'))
        else:
            m = 1
        operations.append({'type': cmd_type, 'value': value, 'value2': value2, 'n': n, 'm': m})

    return operations

def print_controls():
    """Print available controls"""
    print("\nControls:")
    print("Space: Play/Pause")
    print("Up Arrow: Restart playback")
    print("Left/Right Arrows: Navigate history")
    print("Enter: New line (instructions must end with ;)")
    print("s;: Save current version")
    print("q;: Exit")
    print("\nInstructions syntax:")
    print("p:<semitones>; for pitch shift")
    print("t:<rate>; for time stretch")
    print("r:<rate>; for resampling")
    print("rt:<rate>; for time stretch using resampling")
    print("perc:; for percussive track extraction")
    print("copy:<start_byte>:<num_bytes>; for copying sound from one byte to the next user-provided bytes")
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

