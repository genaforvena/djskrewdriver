import librosa
import soundfile as sf
import numpy as np
import re
import sys
import sounddevice as sd
from datetime import datetime
from collections import deque

def reverse_by_beats(y, sr, beats, value1, value2, value3):
    """
    Reverse audio in chunks of specified beats
    value1: interval between reversals
    value2: number of beats per reversed chunk
    value3: repeat pattern every N beats
    """
    # Get beat frames
    beat_frames = get_beat_frames(beats, sr)
    
    # Create output array
    output = np.zeros_like(y)
    output[:] = y[:]  # Copy original signal
    
    # Process in chunks
    for i in range(0, len(beat_frames) - int(value2), int(value2 * value3)):
        if (i // int(value2)) % int(value1) == 0:
            start = beat_frames[i]
            end = beat_frames[min(i + int(value2), len(beat_frames) - 1)]
            
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

def create_loop(y, sr, beats, value1, value2, value3):
    """
    Create loops synchronized with beats
    value1: number of beats per loop
    value2: loop portion length in beats
    value3: repeat pattern every N beats
    """
    beat_frames = get_beat_frames(beats, sr)
    
    if len(beat_frames) < int(value1) + 1:
        return y
    
    # Create output array
    output = np.zeros_like(y)
    output[:] = y[:]  # Copy original signal
    
    # Loop through beats and create loops
    for i in range(0, len(beat_frames) - int(value2), int(value2 * value3)):
        if (i // int(value2)) % int(value1) == 0:
            start = beat_frames[i]
            end = beat_frames[min(i + int(value2), len(beat_frames) - 1)]
            loop_length = end - start
            
            # Create crossfade
            crossfade_length = min(1024, loop_length // 4)
            fade_in = np.linspace(0, 1, crossfade_length)
            fade_out = np.linspace(1, 0, crossfade_length)
            
            # Apply loop effect
            loop = y[start:end]
            loop[-crossfade_length:] *= fade_out
            loop[:crossfade_length] *= fade_in
            
            # Add to output
            output[start:end] = loop
    
    return output

def chop_and_rearrange(y, sr, beats, value1, value2, value3):
    """
    Chop audio into beat-sized chunks and rearrange them
    value1: number of beats per chunk
    value2: step size in beats
    value3: pattern repeat interval
    """
    beat_frames = get_beat_frames(beats, sr)
    
    if len(beat_frames) < int(value1) + 1:
        return y
        
    # Create output array
    output = np.zeros_like(y)
    output[:] = y[:]  # Copy original signal
    
    # Create chunks
    chunks = []
    for i in range(0, len(beat_frames) - int(value2), int(value2 * value3)):
        if (i // int(value2)) % int(value1) == 0:
            start = beat_frames[i]
            end = beat_frames[min(i + int(value2), len(beat_frames) - 1)]
            chunks.append((start, end))
    
    if not chunks:
        return y
    
    # Rearrange chunks in pattern
    crossfade_length = 1024
    
    for i in range(len(chunks)):
        if i + 1 < len(chunks):
            start, end = chunks[i]
            next_start, next_end = chunks[i + 1]
            
            # Apply crossfade between chunks
            if end > start + crossfade_length and next_end > next_start + crossfade_length:
                fade_out = np.linspace(1, 0, crossfade_length)
                fade_in = np.linspace(0, 1, crossfade_length)
                
                output[end - crossfade_length:end] *= fade_out
                output[next_start:next_start + crossfade_length] *= fade_in
    
    return output

def get_beat_frames(beats, sr, hop_length=512):
    """Convert beat positions to frame indices"""
    return librosa.frames_to_samples(beats, hop_length=hop_length)

def add_stutter(y, sr, beats, value1, value2, value3):
    """
    Add stutter effect synchronized with beats
    rate: number of stutters per beat (1.0 = one stutter per beat)
    """
    beat_frames = get_beat_frames(beats, sr)
    output = np.zeros_like(y)
    
    # Copy original signal
    output[:] = y[:]
    
    # Add stutters at beat positions
    for i in range(0, len(beat_frames) - 1, value3):
        if (i // value3) % value1 == 0:
            beat_start = beat_frames[i]
            beat_end = beat_frames[i + 1]
            beat_length = beat_end - beat_start
            
            # Number of stutters for this beat
            rate = value1  # Define rate as value1
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

def add_echo(y, sr, delay, beats, value1, value2, value3):
    """
    Add echo effect synchronized with beats
    delay: echo delay in seconds (if 0, uses one beat length)
    """
    decay = 0.5  # Define decay as a constant value
    
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
        if (i // value3) % value1 == 0:
            echo_delay = delay_samples * i
            if echo_delay + len(y) <= len(output):
                output[echo_delay:echo_delay + len(y)] += y * (decay ** i)
    
    # Trim to original length
    output = output[:len(y)]
    
    # Normalize
    output = output / np.max(np.abs(output))
    return output

def reverse_by_beats(y, sr, beats, value1, value2, value3):
    """
    Reverse audio in chunks of specified beats
    value1: interval between reversals
    value2: number of beats per reversed chunk
    value3: repeat pattern every N beats
    """
    # Get beat frames
    beat_frames = get_beat_frames(beats, sr)
    
    # Create output array
    output = np.zeros_like(y)
    output[:] = y[:]  # Copy original signal
    
    # Process in chunks
    for i in range(0, len(beat_frames) - int(value2), int(value2 * value3)):
        if (i // int(value2)) % int(value1) == 0:
            start = beat_frames[i]
            end = beat_frames[min(i + int(value2), len(beat_frames) - 1)]
            
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

def create_loop(y, sr, beats, value1, value2, value3):
    """
    Create loops synchronized with beats
    value1: number of beats per loop
    value2: loop portion length in beats
    value3: repeat pattern every N beats
    """
    beat_frames = get_beat_frames(beats, sr)
    
    if len(beat_frames) < int(value1) + 1:
        return y
    
    # Create output array
    output = np.zeros_like(y)
    output[:] = y[:]  # Copy original signal
    
    # Loop through beats and create loops
    for i in range(0, len(beat_frames) - int(value2), int(value2 * value3)):
        if (i // int(value2)) % int(value1) == 0:
            start = beat_frames[i]
            end = beat_frames[min(i + int(value2), len(beat_frames) - 1)]
            loop_length = end - start
            
            # Create crossfade
            crossfade_length = min(1024, loop_length // 4)
            fade_in = np.linspace(0, 1, crossfade_length)
            fade_out = np.linspace(1, 0, crossfade_length)
            
            # Apply loop effect
            loop = y[start:end]
            loop[-crossfade_length:] *= fade_out
            loop[:crossfade_length] *= fade_in
            
            # Add to output
            output[start:end] = loop
    
    return output

def chop_and_rearrange(y, sr, beats, value1, value2, value3):
    """
    Chop audio into beat-sized chunks and rearrange them
    value1: number of beats per chunk
    value2: step size in beats
    value3: pattern repeat interval
    """
    beat_frames = get_beat_frames(beats, sr)
    
    if len(beat_frames) < int(value1) + 1:
        return y
        
    # Create output array
    output = np.zeros_like(y)
    output[:] = y[:]  # Copy original signal
    
    # Create chunks
    chunks = []
    for i in range(0, len(beat_frames) - int(value2), int(value2 * value3)):
        if (i // int(value2)) % int(value1) == 0:
            start = beat_frames[i]
            end = beat_frames[min(i + int(value2), len(beat_frames) - 1)]
            chunks.append((start, end))
    
    if not chunks:
        return y
    
    # Rearrange chunks in pattern
    crossfade_length = 1024
    
    for i in range(len(chunks)):
        if i + 1 < len(chunks):
            start, end = chunks[i]
            next_start, next_end = chunks[i + 1]
            
            # Apply crossfade between chunks
            if end > start + crossfade_length and next_end > next_start + crossfade_length:
                fade_out = np.linspace(1, 0, crossfade_length)
                fade_in = np.linspace(0, 1, crossfade_length)
                
                output[end - crossfade_length:end] *= fade_out
                output[next_start:next_start + crossfade_length] *= fade_in
    
    return output


def parse_instructions(instructions):
    """Parse the instruction string into operations"""
    operations = []
    # Updated pattern to match the new format with any number of arguments
    pattern = r"(mute|trig|chop|rev|speed|stut|echo|loop|rt|perc|copy|[ptr]|mash|revert):((-?\d*[.,]?\d+:)*(-?\d*[.,]?\d+));?"
    matches = re.finditer(pattern, instructions)

    for match in matches:
        if match.groups() and len(match.groups()) >= 2:
            cmd_type, args = match.groups()[:2]  # Ensure we only take the first two groups
            args = args.split(':')[:-1]  # Remove the last empty string
            values = [float(arg.replace(',', '.')) for arg in args]
            operations.append({'type': cmd_type, 'values': values})  # Changed 'value' to 'values'

    return operations

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
    # Updated pattern to match the new format with any number of arguments
    pattern = r"(mute|s|q|trig|chop|rev|speed|stut|echo|loop|rt|perc|copy|[ptr]):((-?\d*[.,]?\d+:)*(-?\d*[.,]?\d+));?"
    matches = re.finditer(pattern, instructions)

    for match in matches:
        if match.groups() and len(match.groups()) >= 2:
            cmd_type, args = match.groups()[:2]  # Ensure we only take the first two groups
            args = args.split(':')[:-1]  # Remove the last empty string
            values = [float(arg.replace(',', '.')) for arg in args]
            operations.append({'type': cmd_type, 'values': values})  # Changed 'value' to 'values'

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

def random_mix_beats(y, sr, beats, num_parts, num_beats, repeat_interval):
    """
    Randomly mix parts of each beat divided by num_parts and do it every repeat_interval beats.
    """
    beat_frames = get_beat_frames(beats, sr)
    output = np.zeros_like(y)
    
    for i in range(0, len(beat_frames) - num_beats, repeat_interval):
        start = beat_frames[i]
        end = beat_frames[i + num_beats]
        segment = y[start:end]
        
        # Divide segment into parts
        part_length = len(segment) // num_parts
        parts = [segment[j*part_length:(j+1)*part_length] for j in range(num_parts)]
        
        # Randomly mix parts
        np.random.shuffle(parts)
        
        # Reassemble segment
        mixed_segment = np.concatenate(parts)
        
        # Apply crossfade
        if i > 0:
            crossfade_length = min(1024, len(mixed_segment))
            fade_in = np.linspace(0, 1, crossfade_length)
            fade_out = np.linspace(1, 0, crossfade_length)
            output[start:start + crossfade_length] *= fade_in
            output[start - crossfade_length:start] *= fade_out
        
        # Add mixed segment to output
        output[start:end] = mixed_segment
    
    return output

