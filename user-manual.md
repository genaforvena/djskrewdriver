# DJ Screwdriver User Manual 🎚️

## Quick Start

### Basic Usage
```bash
# Interactive mode
python main.py

# Direct file processing
python main.py input.mp3 "p:-2;rt:0.8;"

# YouTube processing
python main.py https://youtube.com/watch?v=... "bpm:128;stut:2:1:2;"
```

### Playback Controls
- **Space**: Play/Pause
- **Up Arrow**: Restart playback
- **Left Arrow**: Undo last operation
- **Right Arrow**: Redo operation
- **Enter**: Execute command
- **s;**: Save current version
- **q;**: Exit program

## Command Reference

### Core Commands
Each command follows the syntax: `command:value1:value2:value3;`

#### Basic Operations
```
p:X;              # Pitch shift (semitones)
t:X;              # Time stretch (rate)
rt:X;             # Resample time stretch (rate)
r:X;              # Resample (rate)
bpm:X;            # Match to target BPM
```

#### Beat-Synchronized Effects
```
loop:X:Y:Z;       # Create beat loops
chop:X:Y:Z;       # Chop and rearrange
stut:X:Y:Z;       # Add stutter effect
echo:X:Y:Z;       # Add echo
rev:X:Y:Z;        # Reverse beats
mash:X:Y:Z;       # Random beat mixing
```

### Parameter Explanation

#### For all effects:
- Rate values:
  - 1.0 = original speed
  - 2.0 = double speed
  - 0.5 = half speed

#### Pitch (p)
```
p:2;              # Pitch up 2 semitones
p:-2;             # Pitch down 2 semitones
p:12;             # Pitch up one octave
p:-12;            # Pitch down one octave
```

#### Time/Rate (t, rt, r)
```
t:2.0;            # Double speed
t:0.5;            # Half speed
rt:1.5;           # 1.5x speed using resampling
r:0.8;            # 80% speed with pitch change
```

#### BPM Matching
```
bpm:128;          # Match to 128 BPM
bpm:160;          # Match to 160 BPM
bpm:90;           # Match to 90 BPM
```

#### Loop Effect (loop:interval:length:repeat;)
```
loop:1:8:4;       # Create loops every beat, 8 beats long, repeat every 4 beats
loop:2:16:8;      # Create loops every 2 beats, 16 beats long, repeat every 8 beats
loop:4:8:2;       # Create loops every 4 beats, 8 beats long, repeat every 2 beats
```

#### Chop Effect (chop:size:step:repeat;)
```
chop:1:4:2;       # 1-beat chunks, 4-beat steps, repeat every 2 beats
chop:2:8:4;       # 2-beat chunks, 8-beat steps, repeat every 4 beats
chop:4:16:8;      # 4-beat chunks, 16-beat steps, repeat every 8 beats
```

#### Stutter Effect (stut:count:length:repeat;)
```
stut:2:1:2;       # 2 stutters per beat, 1 beat long, repeat every 2 beats
stut:4:1:4;       # 4 stutters per beat, 1 beat long, repeat every 4 beats
stut:8:1:2;       # 8 stutters per beat, 1 beat long, repeat every 2 beats
```

#### Echo Effect (echo:delay:count:decay;)
```
echo:0.2:3:0.7;   # 200ms delay, 3 echoes, 0.7 decay rate
echo:0.1:4:0.8;   # 100ms delay, 4 echoes, 0.8 decay rate
echo:0.3:2:0.6;   # 300ms delay, 2 echoes, 0.6 decay rate
```

#### Reverse Effect (rev:interval:length:repeat;)
```
rev:1:4:2;        # Reverse every beat, 4 beats long, repeat every 2 beats
rev:2:8:4;        # Reverse every 2 beats, 8 beats long, repeat every 4 beats
rev:4:16:8;       # Reverse every 4 beats, 16 beats long, repeat every 8 beats
```

#### Mash Effect (mash:parts:beats:repeat;)
```
mash:4:2:4;       # Mix 4 parts every 2 beats, repeat every 4 beats
mash:8:1:2;       # Mix 8 parts every beat, repeat every 2 beats
mash:16:1:1;      # Mix 16 parts every beat, repeat every beat
```

## Test Cases

### Basic Transformations
```bash
# Pitch changes
p:2;
p:-2;
p:12;
p:-12;

# Speed changes
rt:1.5;
rt:0.8;
t:2.0;
t:0.5;

# BPM matching
bpm:128;
bpm:160;
bpm:90;
```

### Effect Combinations
```bash
# Vaporwave effect
p:-5;rt:0.8;echo:0.3:3:0.7;

# Glitch effect
stut:4:1:2;echo:0.1:4:0.8;loop:1:4:2;

# Rhythmic transformation
chop:1:4:2;rev:1:2:1;echo:0.2:3:0.6;

# Complex pattern
loop:2:8:4;stut:2:1:2;echo:0.25:3:0.7;rev:1:4:2;
```

### Extreme Transformations
```bash
# Super slow haunting
rt:0.25;p:-24;echo:0.4:8:0.9;stut:4:1:2;

# Hyper speed glitch
rt:2.5;p:12;stut:8:1:1;echo:0.05:6:0.9;

# Maximum chaos
mash:16:1:1;stut:6:1:1;echo:0.02:8:0.95;loop:1:1:1;
```

### Genre-Specific Transformations
```bash
# To House Music
bpm:128;loop:4:16:4;echo:0.2:3:0.7;

# To DnB
bpm:174;chop:1:2:2;loop:2:8:4;

# To Hip-Hop
bpm:90;p:-2;echo:0.3:2:0.8;loop:2:8:4;
```

## Common Issues and Solutions

1. **Audio Quality**
   - Keep rate changes between 0.5x and 2.0x for best quality
   - Use multiple small changes instead of one large change
   - Save intermediate results with 's;'

2. **CPU Usage**
   - Complex effect chains may be CPU intensive
   - Apply effects gradually
   - Monitor system performance

3. **File Handling**
   - Large files may take longer to process
   - Save frequently with 's;'
   - Use undo (left arrow) for quick corrections

4. **Effect Timing**
   - Effects are processed in order
   - BPM changes should usually come first
   - Chain effects from broad to detailed

## Best Practices

1. **Effect Order**
```bash
# Recommended order:
bpm:128;          # Global tempo first
p:-2;             # Then pitch
rt:0.9;           # Then time stretching
loop:2:8:4;       # Then beat effects
echo:0.2:3:0.7;   # Then details
```

2. **Saving Strategy**
```bash
# Save after major changes
bpm:128;p:-2;s;
rt:0.9;loop:2:8:4;s;
echo:0.2:3:0.7;s;
```

3. **Testing Strategy**
```bash
# Test gradually
effect:value;     # Test single effect
s;               # Save if good
effect:value;     # Add another effect
s;               # Save if good
```

This manual should serve as both a reference and a testing guide. Would you like me to:
1. Add more test cases?
2. Include troubleshooting scenarios?
3. Add more genre-specific transformations?
4. Create a quick-reference card format?