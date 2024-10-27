# 🎧 DJ SCREWDRIVER COOKBOOK

A guide to making your tracks hit harder, mix smoother, and sound unique. No computer science degree required!

No coding knowledge needed! Just three easy steps to get mixing:

## 🚀 Setup (One Time Only)

1. **Get DJ Screwdriver**
   - Download the .zip file u can download clicking on https://github.com/genaforvena/djskrewdriver/archive/refs/heads/master.zip
   - Unzip it anywhere on your computer
   - Remember where you put it!

2. **Install the Tools**
   ### Windows:
   - Press `Win + R` on your keyboard
   - Type `cmd` and press Enter
   - Copy this WHOLE line and paste it (right-click to paste):
     ```
     pip install librosa soundfile numpy sounddevice keyboard pydub
     ```
   - Press Enter and wait until it's done

   ### Mac:
   - Press `Cmd + Space`
   - Type "Terminal" and press Enter
   - Copy and paste this line:
     ```
     pip install librosa soundfile numpy sounddevice keyboard pydub
     ```
   - Press Enter and wait until it's done

## 💫 Running DJ Screwdriver

### Windows
1. Open the folder where you unzipped DJ Screwdriver
2. Hold `Shift` and `Right-Click` in the empty space
3. Click "Open PowerShell window here" or "Open command window here"
4. Type this and press Enter:
   ```
   python hui.py
   ```
5. When asked, drag & drop your audio file into the window

### Mac
1. Open Terminal (Cmd + Space, type "Terminal")
2. Type `cd ` (with a space after cd)
3. Drag the DJ Screwdriver folder into Terminal
4. Press Enter
5. Type:
   ```
   python hui.py
   ```
6. When asked, drag & drop your audio file into Terminal

## 🎮 Start Creating!

Once running, you'll see this simple menu:
```
=== Main Menu ===
e: Add an effect
p: Play/Pause
u: Undo
r: Redo
s: Save your edit
q: Quit
```

Just press 'e' and follow the prompts to start transforming your tracks!

## ⚡ Quick Tips
- Works with MP3s and WAVs
- Can also use YouTube links
- Press 'u' to undo any effect you don't like
- Press 's' to save your edit
- Press 'q' to quit

## 🆘 Common Issues & Fixes

If you get any errors about Python or pip:
- Let me know and I'll help you install Python!

### "Permission denied"
- Run PowerShell/Terminal as Administrator (right-click, Run as Administrator)

### "Module not found"
- Run the pip install command again

### Anything else?
- Hit me up, I'll help you get it running!

Now you're ready to check out the Cookbook and start creating! 🎉

## 🎵 How Sound Gets Transformed

Think of your track like clay - each effect molds it in a different way:
- **Pitch** works like vinyl speed - higher or lower
- **Time** stretches or squeezes your sound
- **Stutter** is like quickly scratching back and forth
- **Echo** adds space and depth
- **Loop** grabs a piece and repeats it
- **Chop** cuts up and rearranges your beats
- **Mash** shuffles parts around randomly

## 🎚️ Making Tracks Bang

### Adding Weight to Your Sound
```
=== Main Menu === 
e: Add an effect

Pick effect: 2 (Speed Change)
Speed multiplier? 0.8
[Track gets deeper and heavier]

Pick effect: 6 (Stutter)
How many beats? 2
Number of stutters? 4
Length? 1
Repeat? 1
[Adds punch and intensity]
```
What's happening: Slowing it down brings out the bass frequencies, then the stutter adds impact by hitting those low frequencies repeatedly.

### Making Tracks Brighter and Louder
```
Pick effect: 1 (Pitch)
Semitones? 2
[Brightens the sound]

Pick effect: 3 (Echo)
Delay time? 0.1
Number of echoes? 4
Decay? 0.9
[Creates density and perceived loudness]
```
Why it works: Raising the pitch brings out high frequencies, short echoes stack up and make it feel louder without distorting.

## 🎹 Genre Flip Recipes

### Turn Any Track into House (128 BPM)
```
1. Pick effect: 8 (BPM)
   Target BPM? 128
   [Locks to house tempo]

2. Pick effect: 4 (Loop)
   How many beats? 1
   Total length? 4
   Play every? 2
   [Creates that house groove]

3. Pick effect: 3 (Echo)
   Delay time? 0.2 
   Number of echoes? 3
   Decay? 0.7
   [Adds classic house space]
```

### Make It DnB (174 BPM)
```
1. Pick effect: 8 (BPM)
   Target BPM? 174
   [Speeds to DnB tempo]

2. Pick effect: 7 (Chop)
   Chop every? 1
   Length? 2
   Move forward? 2
   Repeat? 1
   [Creates that broken beat feel]

3. Pick effect: 6 (Stutter)
   How many beats? 2
   Number of stutters? 4
   Length? 1
   Repeat? 1
   [Adds that dnb aggression]
```

### Hip-Hop Remix (90 BPM)
```
1. Pick effect: 8 (BPM)
   Target BPM? 90
   [Sets hip-hop tempo]

2. Pick effect: 1 (Pitch)
   Semitones? -2
   [Deepens the vibe]

3. Pick effect: 4 (Loop)
   How many beats? 2
   Total length? 8
   Play every? 4
   [Creates that head-nod loop]
```

## 🎪 Effect Stacking Magic

### Build Energy
```
1. Start Simple:
   Pick effect: 4 (Loop)
   How many beats? 1
   Total length? 4
   Play every? 2
   [Creates base pattern]

2. Add Intensity:
   Pick effect: 6 (Stutter)
   How many beats? 2
   Number of stutters? 4
   Length? 1
   Repeat? 1
   [Adds excitement]

3. Create Space:
   Pick effect: 3 (Echo)
   Delay time? 0.2
   Number of echoes? 4
   Decay? 0.8
   [Makes it huge]
```
Why it works: Each effect builds on the last - loop sets the foundation, stutter adds energy, echo makes it larger than life.

### Dark and Deep Transform
```
1. Go Down:
   Pick effect: 1 (Pitch)
   Semitones? -5
   [Darkens everything]

2. Add Weight:
   Pick effect: 2 (Speed)
   Speed multiplier? 0.8
   [Makes it heavier]

3. Create Atmosphere:
   Pick effect: 3 (Echo)
   Delay time? 0.3
   Number of echoes? 6
   Decay? 0.9
   [Adds dark space]
```
The process: Lower pitch creates darkness, slower speed adds weight, long echoes create the haunting vibe.

## 🎯 Quick Problem Solvers

### Track Too Weak?
```
1. Pick effect: 6 (Stutter)
   How many beats? 2
   Number of stutters? 4
   Length? 1
   Repeat? 1
   [Adds punch]

2. Pick effect: 3 (Echo)
   Delay time? 0.1
   Number of echoes? 4
   Decay? 0.9
   [Builds density]
```

### Need More Bass?
```
1. Pick effect: 1 (Pitch)
   Semitones? -2
   [Deepens bass]

2. Pick effect: 2 (Speed)
   Speed multiplier? 0.9
   [Enhances low end]
```

### Want More Energy?
```
1. Pick effect: 7 (Chop)
   Chop every? 1
   Length? 2
   Move forward? 1
   Repeat? 2
   [Creates movement]

2. Pick effect: 4 (Loop)
   How many beats? 1
   Total length? 4
   Play every? 2
   [Builds tension]
```

## 🎼 Effect Combinations That Always Work

### Safe Combinations
```
1. Pitch → Speed → Echo
   (Changes the sound, then adds space)

2. BPM → Loop → Echo
   (Sets tempo, makes pattern, adds depth)

3. Chop → Stutter → Echo
   (Rearranges, adds impact, creates space)
```

### Risky Combinations (Avoid)
```
❌ Echo → Echo → Echo
   (Too much delay buildup)

❌ Stutter → Stutter → Stutter
   (Gets too choppy)

❌ Loop → Loop → Loop
   (Creates weird patterns)
```

## 🎹 DJ Tips

1. **Save Your Work**
   - Press 'S' after each good change
   - You can always undo with 'U' if needed

2. **Build Gradually**
   - Start with tempo/pitch
   - Add rhythmic effects
   - Finish with space/echo

3. **Monitor Your Levels**
   - Effects can stack up and get loud
   - Use your mixer's gains to control

4. **Create Versions**
   - Make different versions for your set
   - Save intro edits, outros, drops

5. **Test Your Edits**
   - Try effects at home first
   - Know how they'll react in the mix

## 🎧 Remember

- Every track reacts differently to effects
- Trust your ears - if it sounds good, it is good
- You can always undo (U) if you don't like something
- Save (S) when you've got something good
- Have fun experimenting!

Made with 💜 for DJs who love to create something unique

