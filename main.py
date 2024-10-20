import librosa
import soundfile as sf
import numpy as np
import re

def change_speed(y, sr, speed_factor, preserve_pitch=True):
    if preserve_pitch:
        return librosa.effects.time_stretch(y, rate=speed_factor)
    else:
        return librosa.resample(y, sr, int(sr * speed_factor))

def process_audio(file_path, operations):
    y, sr = librosa.load(file_path)
    
    for op in operations:
        speed_factor = 1 + op['change'] / 100
        y = change_speed(y, sr, speed_factor, op['preserve_pitch'])
    
    output_file = 'processed_' + file_path
    sf.write(output_file, y, sr)
    print(f"Processed audio saved as {output_file}")

def parse_instructions(instructions):
    operations = []
    pattern = r"(SPEED|SLOW):(\d+):(PITCH|NOPITCH);"
    matches = re.finditer(pattern, instructions)
    
    for match in matches:
        action, percentage, pitch_option = match.groups()
        change = int(percentage)
        if action == "SLOW":
            change = -change
        preserve_pitch = (pitch_option == "PITCH")
        operations.append({'change': change, 'preserve_pitch': preserve_pitch})
    
    return operations

if __name__ == "__main__":
    file_path = input("Enter the path to your audio file: ")
    print("Enter your instructions using the following syntax:")
    print("SPEED:<percentage>:PITCH; or SPEED:<percentage>:NOPITCH; to speed up")
    print("SLOW:<percentage>:PITCH; or SLOW:<percentage>:NOPITCH; to slow down")
    print("Example: SLOW:10:PITCH;SPEED:20:NOPITCH;")
    instructions = input("Instructions: ")
    operations = parse_instructions(instructions)
    if operations:
        process_audio(file_path, operations)
    else:
        print("No valid instructions found. Please check your input.")