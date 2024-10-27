import librosa
import soundfile as sf
import numpy as np
import re
import sys
import sounddevice as sd
from datetime import datetime
from collections import deque
from scipy.signal.windows import hann

class AudioEffects:
    @staticmethod
    def estimate_bpm(y, sr):
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
        return float(tempo)

    @staticmethod
    def match_bpm(y, sr, source_bpm, target_bpm):
        stretch_ratio = target_bpm / source_bpm
        return librosa.effects.time_stretch(y, rate=stretch_ratio)

    @staticmethod
    def pitch_shift(y, sr, n_steps):
        return librosa.effects.pitch_shift(y, sr=sr, n_steps=n_steps)

    @staticmethod
    def time_stretch(y, rate):
        return librosa.effects.time_stretch(y, rate=rate)

    @staticmethod
    def resample_time(y, sr, rate):
        target_sr = int(sr * rate)
        y_resampled = librosa.resample(y, orig_sr=sr, target_sr=target_sr, res_type='kaiser_best')
        return librosa.resample(y_resampled, orig_sr=target_sr, target_sr=sr, res_type='kaiser_best')

    @staticmethod
    def create_loop(y, sr, beats, interval, length, repeat):
        interval = int(interval)
        length = int(length)
        repeat = int(repeat)
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        looped_audio = np.copy(y)
        
        for i in range(0, len(beat_frames) - length, interval):
            if (i // interval) % repeat == 0:
                start = beat_frames[i]
                end = beat_frames[i + length]
                loop_segment = y[start:end]
                
                fade_length = min(1024, len(loop_segment) // 4)
                fade_in = np.linspace(0, 1, fade_length)
                fade_out = np.linspace(1, 0, fade_length)
                
                if len(loop_segment) >= 2 * fade_length:
                    loop_segment[:fade_length] *= fade_in
                    loop_segment[-fade_length:] *= fade_out
                
                looped_audio[start:end] = loop_segment
        
        return looped_audio

    @staticmethod
    def chop_and_rearrange(y, sr, beats, size, step, repeat):
        size = int(size)
        step = int(step)
        repeat = int(repeat)
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        chopped_audio = np.copy(y)
        pattern = [1, 2, 2, 1, 3, 3, 2, 1]
        
        for i in range(0, len(beat_frames) - size, step):
            if (i // step) % repeat == 0:
                start = beat_frames[i]
                end = beat_frames[i + size]
                chunks = [
                    y[beat_frames[j]:beat_frames[j + size]]
                    for j in range(i, i + size)
                ]
                
                rearranged = [chunks[p % len(chunks)] for p in pattern]
                
                for j in range(1, len(rearranged)):
                    fade_length = min(1024, len(rearranged[j]) // 4)
                    fade_in = np.linspace(0, 1, fade_length)
                    fade_out = np.linspace(1, 0, fade_length)
                    if len(rearranged[j]) >= fade_length and len(rearranged[j - 1]) >= fade_length:
                        rearranged[j][:fade_length] *= fade_in
                        rearranged[j - 1][-fade_length:] *= fade_out
                
                concatenated = np.concatenate(rearranged)
                segment_length = end - start
                if len(concatenated) <= segment_length:
                    chopped_audio[start:start + len(concatenated)] = concatenated
                else:
                    chopped_audio[start:end] = concatenated[:segment_length]
        
        return chopped_audio

    @staticmethod
    def add_stutter(y, sr, beats, count, length, repeat):
        count = int(count)
        length = int(length)
        repeat = int(repeat)
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        stuttered_audio = np.copy(y)
        
        for i in range(0, len(beat_frames) - length, 1):
            if (i % repeat) == 0:
                start = beat_frames[i]
                end = beat_frames[i + length]
                stutter_segment = y[start:end]
                
                stuttered = np.tile(stutter_segment, count)
                
                fade_out = np.linspace(1.0, 0.0, len(stutter_segment)) ** 2
                for j in range(count):
                    segment_start = j * len(stutter_segment)
                    segment_end = (j + 1) * len(stutter_segment)
                    if segment_end <= len(stuttered):
                        stuttered[segment_start:segment_end] *= fade_out
                
                stutter_length = len(stuttered)
                original_length = end - start
                if stutter_length <= original_length:
                    stuttered_audio[start:start + stutter_length] = stuttered
                else:
                    stuttered_audio[start:end] = stuttered[:original_length]
        
        return stuttered_audio

    @staticmethod
    def add_echo(y, sr, delay, count, decay):
        count = int(count)
        delay = float(delay)
        decay = float(decay)
        
        echo_samples = int(sr * delay)
        total_length = len(y) + echo_samples * count
        output = np.zeros(total_length)
        output[:len(y)] = y
        
        for i in range(1, count + 1):
            delay_samples = echo_samples * i
            amplitude = decay ** i
            if delay_samples < total_length:
                output[delay_samples:delay_samples + len(y)] += y * amplitude
        
        # Prevent clipping
        max_val = np.max(np.abs(output))
        if max_val > 0:
            output = output / max_val
        
        return output

    @staticmethod
    def reverse_by_beats(y, sr, beats, interval, length, repeat):
        interval = int(interval)
        length = int(length)
        repeat = int(repeat)
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        reversed_audio = np.copy(y)
        
        for i in range(0, len(beat_frames) - length, interval):
            if (i // interval) % repeat == 0:
                start = beat_frames[i]
                end = beat_frames[i + length]
                reversed_segment = y[start:end][::-1]
                
                fade_length = min(1024, len(reversed_segment) // 2)
                fade_in = np.linspace(0, 1, fade_length)
                fade_out = np.linspace(1, 0, fade_length)
                
                if len(reversed_segment) >= 2 * fade_length:
                    reversed_segment[:fade_length] *= fade_in
                    reversed_segment[-fade_length:] *= fade_out
                
                reversed_audio[start:end] = reversed_segment
        
        return reversed_audio

    @staticmethod
    def random_mix_beats(y, sr, beats, parts, beats_per_mash, repeat):
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        mashed_audio = np.copy(y)
        
        for i in range(0, len(beat_frames) - beats_per_mash, repeat):
            if (i // repeat) % repeat == 0:
                start = beat_frames[i]
                end = beat_frames[i + beats_per_mash]
                mash_segment = y[start:end]
                
                part_length = len(mash_segment) // parts
                sections = [
                    mash_segment[j * part_length:(j + 1) * part_length]
                    for j in range(parts)
                ]
                
                np.random.shuffle(sections)
                
                for j in range(1, len(sections)):
                    fade_length = min(1024, len(sections[j]) // 4)
                    fade_in = np.linspace(0, 1, fade_length)
                    fade_out = np.linspace(1, 0, fade_length)
                    if len(sections[j]) >= fade_length and len(sections[j - 1]) >= fade_length:
                        sections[j][:fade_length] *= fade_in
                        sections[j - 1][-fade_length:] *= fade_out
                
                concatenated = np.concatenate(sections)
                segment_length = end - start
                if len(concatenated) <= segment_length:
                    mashed_audio[start:start + len(concatenated)] = concatenated
                else:
                    mashed_audio[start:end] = concatenated[:segment_length]
        
        return mashed_audio

    @staticmethod
    def match_frequency_profile(modified, original, sr):
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
        rms_original = np.sqrt(np.mean(original**2))
        rms_modified = np.sqrt(np.mean(modified**2))
        scaling_factor = rms_original / (rms_modified + 1e-8)
        return modified * scaling_factor

    @staticmethod
    def spectral_gate(y, sr, threshold_db, preserve_freq_ranges=None):
        D = librosa.stft(y)
        mag, phase = librosa.magphase(D)
        mag_db = librosa.amplitude_to_db(mag)
        mask = mag_db > threshold_db

        if preserve_freq_ranges:
            freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
            for min_freq, max_freq in preserve_freq_ranges:
                preserve_mask = (freqs >= min_freq) & (freqs <= max_freq)
                mask[preserve_mask, :] = True

        mag_filtered = mag * mask
        D_filtered = mag_filtered * phase
        return librosa.istft(D_filtered)

def parse_instructions(instructions):
    """Parse the instruction string into operations"""
    print("parsing instructions...", instructions)
    operations = []
    parts = instructions.split(';')
    for part in parts:
        if ':' in part:
            cmd, *args = part.split(':')  # Use unpacking to handle multiple arguments
            values = [float(arg.replace(',', '.')) for arg in args if arg]  # Convert arguments to float
            if cmd == 'p' and len(values) == 1:
                operations.append({'type': cmd, 'values': values})
                print(f"Operation: {{'type': {cmd}, 'values': {values}}}")
            else:
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
    """Truncate the name to a maximum length, preserving start and end."""
    if len(name) > max_length:
        # Calculate how much of the start and end to keep
        part_length = (max_length - 3) // 2  # Subtract 3 for the ellipsis
        start = name[:part_length]
        end = name[-part_length:]
        return f"{start}...{end}"
    return name

def main():
    # Load audio file
    y, sr = librosa.load(sys.argv[1], sr=None)
    
    # Parse instructions
    instructions = sys.argv[2]
    operations = parse_instructions(instructions)
    
    # Check for help command
    if any(op['type'] == 'help' for op in operations):
        print_help()
        return
    
    # Process operations
    for operation in operations:
        cmd_type = operation['type']
        values = operation['values']
        
        try:
            if cmd_type == 'rt':
                y = AudioEffects.resample_time(y, sr, rate=values[0])
            elif cmd_type == 't':
                y = AudioEffects.time_stretch(y, rate=values[0])
            elif cmd_type == 'p':
                y = AudioEffects.pitch_shift(y, sr, n_steps=values[0])
            elif cmd_type == 'stut':
                y = AudioEffects.add_stutter(y, sr, beats=None, count=int(values[0]), length=int(values[1]), repeat=int(values[2]))
            elif cmd_type == 'chop':
                y = AudioEffects.chop_and_rearrange(y, sr, beats=None, size=int(values[0]), step=int(values[1]), repeat=int(values[2]))
            elif cmd_type == 'echo':
                y = AudioEffects.add_echo(y, sr, delay=values[0], count=int(values[1]), decay=values[2])
            elif cmd_type == 'mash':
                y = AudioEffects.random_mix_beats(y, sr, beats=None, parts=int(values[0]), beats_per_mash=int(values[1]), repeat=int(values[2]))
            elif cmd_type == 'loop':
                y = AudioEffects.create_loop(y, sr, beats=None, interval=int(values[0]), length=int(values[1]), repeat=int(values[2]))
            elif cmd_type == 'rev':
                y = AudioEffects.reverse_by_beats(y, sr, beats=None, interval=int(values[0]), length=int(values[1]), repeat=int(values[2]))
            elif cmd_type == 'bpm':
                if len(values) >= 1:
                    target_bpm = values[0]
                    source_bpm = AudioEffects.estimate_bpm(y, sr)
                    y = AudioEffects.match_bpm(y, sr, source_bpm, target_bpm)
                else:
                    print("Warning: 'bpm' operation requires at least one value (target BPM)")
            elif cmd_type == 'a':
                if len(values) >= 1:
                    y = AudioEffects.resample_time(y, sr, rate=values[0])
                else:
                    print("Warning: 'a' operation requires at least one value (rate)")
            else:
                print(f"Warning: Unknown operation {cmd_type}")
        except Exception as e:
            print(f"Warning: Operation {cmd_type}:{values} failed with error: {e}")
    
    # Save processed audio
    sf.write(sys.argv[3], y, sr)

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
    print("  python cli.py 'audio.mp3' 'p:2;rt:1.5;chop:4:2:1;'")
    print("  python cli.py 'audio.mp3' 'loop:1:4:2;echo:0.5:3:0.7;'")
    print("  python cli.py 'audio.mp3' 'rev:2:2:2;stut:1:3:1;'")
    print("  python cli.py 'audio.mp3' 'bpm:120;t:0.8;'")
    print("  python cli.py 'audio.mp3' 'help;'")
    print("\nNote: All instructions must end with a semicolon (;)\n")

if __name__ == "__main__":
    main()
