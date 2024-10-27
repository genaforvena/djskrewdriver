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
            operations.append({'type': cmd, 'values': values})
            print(f"Operation: {{'type': {cmd}, 'values': {values}}}")
        else:
            if part:  # Ensure the part is not empty
                operations.append({'type': part, 'values': []})
                print(f"Operation: {{'type': {part}, 'values': []}}")
    return operations

def main():
    print("Audio Effects Module")
    print("This module provides various audio processing effects.")
    print("\nAvailable effects:")
    for method in dir(AudioEffects):
        if not method.startswith("__"):
            print(f"- {method}")
    
    print("\nTo use these effects, import this module in your Python script.")
    print("Example:")
    print("from effects import AudioEffects")
    print("effect = AudioEffects.pitch_shift(audio_data, sample_rate, n_steps)")

if __name__ == "__main__":
    main()
