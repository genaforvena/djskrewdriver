import librosa
import soundfile as sf
import numpy as np
import re
import sys
import sounddevice as sd
from datetime import datetime
from collections import deque

class AudioEffects:
    @staticmethod
    def estimate_bpm(y, sr):
        # Ensure onset envelope and dynamic programming are used
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
        return tempo

    @staticmethod
    def match_bpm(y, sr, source_bpm, target_bpm):
        # Calculate stretch ratio and apply time-stretch
        stretch_ratio = target_bpm / source_bpm
        return librosa.effects.time_stretch(y, stretch_ratio)

    @staticmethod
    def pitch_shift(y, sr, n_steps):
        # Ensure STFT and phase correction are applied
        return librosa.effects.pitch_shift(y, sr=sr, n_steps=n_steps)

    @staticmethod
    def time_stretch(y, rate):
        # Ensure STFT and phase coherence are maintained
        return librosa.effects.time_stretch(y, rate=rate)

    @staticmethod
    def resample_time(y, sr, rate):
        # Ensure resampling with anti-aliasing filter
        target_sr = int(sr * rate)
        y_resampled = librosa.resample(y, orig_sr=sr, target_sr=target_sr)
        return librosa.resample(y_resampled, orig_sr=target_sr, target_sr=sr)

    @staticmethod
    def create_loop(y, sr, beats, interval, length, repeat):
        # Convert float parameters to integers where necessary
        interval = int(interval)
        length = int(length)
        repeat = int(repeat)
        # Detect beat frames
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        looped_audio = np.copy(y)
        
        for i in range(0, len(beat_frames) - length, interval):
            if i % repeat == 0:
                start = beat_frames[i]
                end = beat_frames[i + length]
                loop_segment = y[start:end]
                
                # Apply fade in/out
                fade_length = min(1024, len(loop_segment) // 4)
                fade_in = np.linspace(0, 1, fade_length)
                fade_out = np.linspace(1, 0, fade_length)
                loop_segment[:fade_length] *= fade_in
                loop_segment[-fade_length:] *= fade_out
                
                looped_audio[start:end] = loop_segment
        
        return looped_audio

    @staticmethod
    def chop_and_rearrange(y, sr, beats, size, step, repeat):
        # Convert float parameters to integers where necessary
        size = int(size)
        step = int(step)
        repeat = int(repeat)
        # Detect beat frames
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        chopped_audio = np.copy(y)
        
        for i in range(0, len(beat_frames) - size, step):
            if i % repeat == 0:
                start = beat_frames[i]  # Define start
                end = beat_frames[i + size]  # Define end
                chunks = [y[beat_frames[j]:beat_frames[j + size]] for j in range(i, i + size)]
                
                # Rearrange chunks
                pattern = [1, 2, 2, 1, 3, 3, 2, 1]
                rearranged = [chunks[p % len(chunks)] for p in pattern]
                
                # Apply crossfades
                for j in range(1, len(rearranged)):
                    fade_length = min(1024, len(rearranged[j]) // 4)
                    fade_in = np.linspace(0, 1, fade_length)
                    fade_out = np.linspace(1, 0, fade_length)
                    rearranged[j][:fade_length] *= fade_in
                    rearranged[j-1][-fade_length:] *= fade_out
                
                # Ensure the concatenated array has the correct shape
                concatenated = np.concatenate(rearranged)
                if len(concatenated) <= end - start:
                    chopped_audio[start:start+len(concatenated)] = concatenated
                else:
                    chopped_audio[start:end] = concatenated[:end-start]
        
        return chopped_audio

    @staticmethod
    def add_stutter(y, sr, beats, count, length, repeat):
        # Convert float parameters to integers where necessary
        count = int(count)
        length = int(length)
        repeat = int(repeat)
        # Detect beat frames
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        stuttered_audio = np.copy(y)
        
        for i in range(0, len(beat_frames) - length, repeat):
            if i % repeat == 0:
                start = beat_frames[i]
                end = beat_frames[i + length]
                stutter_segment = y[start:end]
                
                # Create stutters
                stuttered = np.tile(stutter_segment, count)
                
                # Apply envelope
                fade_out = np.linspace(1.0, 0.0, len(stutter_segment)) ** 2
                for j in range(count):
                    stuttered[j*len(stutter_segment):(j+1)*len(stutter_segment)] *= fade_out
                
                stuttered_audio[start:start+len(stuttered)] = stuttered
        
        return stuttered_audio

    @staticmethod
    def add_echo(y, sr, delay, count, decay):
        # Ensure the function signature matches the expected input
        count = int(count)
        # Create output buffer
        output = np.zeros(len(y) + int(sr * delay * count))
        output[:len(y)] = y
        
        for i in range(1, count + 1):
            delay_samples = int(sr * delay * i)
            amplitude = decay ** i
            output[delay_samples:delay_samples + len(y)] += y * amplitude
        
        # Normalize
        output = output / np.max(np.abs(output))
        
        return output

    @staticmethod
    def reverse_by_beats(y, sr, beats, interval, length, repeat):
        # Detect beat frames
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        reversed_audio = np.copy(y)
        
        for i in range(0, len(beat_frames) - length, interval):
            if i % repeat == 0:
                start = beat_frames[i]
                end = beat_frames[i + length]
                reversed_segment = y[start:end][::-1]
                
                # Apply crossfade
                fade_length = min(1024, len(reversed_segment))
                fade_in = np.linspace(0, 1, fade_length)
                fade_out = np.linspace(1, 0, fade_length)
                reversed_segment[:fade_length] *= fade_in
                reversed_segment[-fade_length:] *= fade_out
                
                reversed_audio[start:end] = reversed_segment
        
        return reversed_audio

    @staticmethod
    def random_mix_beats(y, sr, beats, parts, beats_per_mash, repeat):
        # Convert float parameters to integers where necessary
        parts = int(parts)
        beats_per_mash = int(beats_per_mash)
        repeat = int(repeat)
        # Detect beat frames
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        mashed_audio = np.copy(y)
        
        for i in range(0, len(beat_frames) - beats_per_mash, repeat):
            if i % repeat == 0:
                start = beat_frames[i]
                end = beat_frames[i + beats_per_mash]
                mash_segment = y[start:end]
                
                # Ensure parts are not greater than the length of mash_segment
                part_length = len(mash_segment) // max(1, parts)
                sections = [mash_segment[j*part_length:(j+1)*part_length] for j in range(parts)]
                np.random.shuffle(sections)
                
                # Apply crossfades
                for j in range(1, len(sections)):
                    fade_length = min(1024, len(sections[j]) // 4)
                    fade_in = np.linspace(0, 1, fade_length)
                    fade_out = np.linspace(1, 0, fade_length)
                    sections[j][:fade_length] *= fade_in
                    sections[j-1][-fade_length:] *= fade_out
                
                # Ensure the concatenated array has the correct shape
                concatenated = np.concatenate(sections)
                if len(concatenated) <= end - start:
                    mashed_audio[start:start+len(concatenated)] = concatenated
                else:
                    mashed_audio[start:end] = concatenated[:end-start]
        
        return mashed_audio

    @staticmethod
    def match_frequency_profile(modified, original, sr):
        # Ensure STFT and scaling are applied
        S_original = librosa.stft(original)
        S_modified = librosa.stft(modified)
        mag_original = np.abs(S_original)
        mag_modified = np.abs(S_modified)
        avg_original = np.mean(mag_original, axis=1, keepdims=True)
        avg_modified = np.mean(mag_modified, axis=1, keepdims=True)
        scaling = avg_original / (avg_modified + 1e-8)
        S_matched = S_modified * scaling
        return librosa.istft(S_matched)

    @staticmethod
    def match_loudness(modified, original, sr):
        # Ensure RMS calculation and scaling are applied
        rms_original = np.sqrt(np.mean(original**2))
        rms_modified = np.sqrt(np.mean(modified**2))
        scaling_factor = rms_original / (rms_modified + 1e-8)
        return modified * scaling_factor

    @staticmethod
    def spectral_gate(y, sr, threshold_db, preserve_freq_ranges=None):
        # Ensure all necessary arguments are provided
        D = librosa.stft(y)
        mag, phase = librosa.magphase(D)
        mag_db = librosa.amplitude_to_db(mag)
        mask = mag_db > threshold_db
        if preserve_freq_ranges:
            freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
            for min_freq, max_freq in preserve_freq_ranges:
                preserve_mask = (freqs >= min_freq) & (freqs <= max_freq)
                mask[preserve_mask] = True
        mag_filtered = mag * mask
        return librosa.istft(mag_filtered * phase)

def parse_instructions(instructions):
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
    print("command:number:number:number;")
    print("Example: p:2:1:3; for pitch shift with arguments 2, 1, and 3")
    print("\nNote: All instructions must end with a semicolon (;)")

def too_long_name_truncation(name, max_length=255):
    """Truncate the name to a maximum length."""
    return name[:max_length]  # Truncate to max_length

def main():
    # Load audio file
    y, sr = librosa.load(sys.argv[1])

    # Parse instructions
    instructions = sys.argv[2]
    operations = parse_instructions(instructions)

    # Process operations
    for operation in operations:
        cmd_type = operation['type']
        values = operation['values']

        try:
            if cmd_type == 'rt':
                y = AudioEffects.time_stretch(y, values[0])
            elif cmd_type == 'p':
                y = AudioEffects.pitch_shift(y, sr, values[0])
            elif cmd_type == 'stut':
                y = AudioEffects.add_stutter(y, sr, values[0], values[1], values[2])
            elif cmd_type == 'chop':
                y = AudioEffects.chop_and_rearrange(y, sr, values[0], values[1], values[2], values[3])
            elif cmd_type == 'echo':
                y = AudioEffects.add_echo(y, sr, values[0], int(values[1]), values[2])
            elif cmd_type == 'mash':
                y = AudioEffects.random_mix_beats(y, sr, values[0], values[1], values[2], values[3])
            elif cmd_type == 'loop':
                y = AudioEffects.create_loop(y, sr, values[0], values[1], values[2], values[3])
            elif cmd_type == 'bpm':
                # Implement BPM change if needed
                pass
            elif cmd_type == 'a':
                # Implement any additional processing if needed
                pass
            else:
                print(f"Warning: Unknown operation {cmd_type}")
        except Exception as e:
            print(f"Warning: Operation {cmd_type}:{values} failed with error: {e}")

    # Save processed audio
    sf.write(sys.argv[3], y, sr)

if __name__ == "__main__":
    main()
