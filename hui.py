from typing import Optional, List, Dict, Any
import sys
from djskrewcore.audio import AudioManager

class FriendlyAudioCLI:
    def __init__(self):
        self.effects_menu = {
            "1": ("Change pitch", self.pitch_effect),
            "2": ("Change speed", self.speed_effect),
            "3": ("Add echo", self.echo_effect),
            "4": ("Create loops", self.loop_effect),
            "5": ("Reverse parts", self.reverse_effect),
            "6": ("Stutter effect", self.stutter_effect),
            "7": ("Chop and mix", self.chop_effect),
            "8": ("Change BPM", self.bpm_effect),
            "9": ("Random mashup", self.mash_effect),
        }
        
        self.main_menu = {
            "e": "Apply an effect",
            "p": "Play/Pause",
            "u": "Undo last change",
            "r": "Redo last change",
            "s": "Save your track",
            "q": "Quit"
        }

    def get_number_input(self, prompt: str, min_val: float, max_val: float, default: Optional[float] = None) -> float:
        while True:
            default_str = f" (default: {default})" if default is not None else ""
            value = input(f"{prompt}{default_str}: ").strip()
            
            if value == "" and default is not None:
                return default
                
            try:
                num = float(value)
                if min_val <= num <= max_val:
                    return num
                print(f"Please enter a number between {min_val} and {max_val}")
            except ValueError:
                print("Please enter a valid number")

    def pitch_effect(self) -> str:
        print("\n=== Pitch Change ===")
        print("Positive numbers make the sound higher")
        print("Negative numbers make the sound lower")
        print("For example: 2 = two semitones higher, -3 = three semitones lower")
        semitones = self.get_number_input("How many semitones to change?", -12, 12, 0)
        return f"p:{semitones};"

    def speed_effect(self) -> str:
        print("\n=== Speed Change ===")
        print("Numbers above 1 make it faster")
        print("Numbers below 1 make it slower")
        print("For example: 0.5 = half speed, 2 = double speed")
        rate = self.get_number_input("Speed multiplier?", 0.25, 4, 1)
        return f"t:{rate};"

    def echo_effect(self) -> str:
        print("\n=== Echo Effect ===")
        delay = self.get_number_input("Delay time in seconds?", 0.1, 2, 0.5)
        count = int(self.get_number_input("Number of echoes?", 1, 10, 3))
        decay = self.get_number_input("Echo decay (0-1)?", 0, 1, 0.7)
        return f"echo:{delay}:{count}:{decay};"

    def loop_effect(self) -> str:
        print("\n=== Loop Effect ===")
        print("This will create repeating loops in your track")
        beats = int(self.get_number_input("How many beats to loop?", 1, 16, 2))
        length = int(self.get_number_input("Total length in beats?", beats, 32, 8))
        step = int(self.get_number_input("Play every how many beats?", 1, length, 4))
        return f"loop:{beats}:{length}:{step};"

    def reverse_effect(self) -> str:
        print("\n=== Reverse Parts ===")
        print("This will reverse sections of your track")
        beats = int(self.get_number_input("How many beats to reverse?", 1, 16, 1))
        length = int(self.get_number_input("Total length in beats?", beats, 32, 4))
        step = int(self.get_number_input("Reverse every how many beats?", 1, length, 2))
        return f"rev:{beats}:{length}:{step};"

    def stutter_effect(self) -> str:
        print("\n=== Stutter Effect ===")
        beats = int(self.get_number_input("How many beats to stutter?", 1, 8, 1))
        count = int(self.get_number_input("Number of stutters?", 2, 16, 4))
        length = self.get_number_input("Length of each stutter?", 0.25, 4, 1)
        repeat = int(self.get_number_input("Repeat how many times?", 1, 8, 1))
        return f"stut:{beats}:{count}:{length}:{repeat};"

    def chop_effect(self) -> str:
        print("\n=== Chop and Mix ===")
        print("This will chop up and rearrange parts of your track")
        beats = int(self.get_number_input("Chop every how many beats?", 1, 8, 1))
        size = int(self.get_number_input("Length of each chop in beats?", 1, 16, 4))
        step = int(self.get_number_input("Move forward how many beats?", 1, size, 2))
        repeat = int(self.get_number_input("Repeat pattern how many times?", 1, 8, 1))
        return f"chop:{beats}:{size}:{step}:{repeat};"

    def bpm_effect(self) -> str:
        print("\n=== Change BPM ===")
        print("This will adjust the speed to match a specific BPM")
        target_bpm = self.get_number_input("Target BPM?", 60, 200, 120)
        return f"bpm:{target_bpm};"

    def mash_effect(self) -> str:
        print("\n=== Random Mashup ===")
        print("This will create a random mashup of parts of your track")
        beats = int(self.get_number_input("Basic beat size?", 1, 8, 1))
        parts = int(self.get_number_input("Number of parts to mix?", 2, 16, 4))
        beats_per_mash = int(self.get_number_input("Beats per mixed section?", 1, 16, 4))
        repeat = int(self.get_number_input("Repeat pattern how many times?", 1, 8, 1))
        return f"mash:{beats}:{parts}:{beats_per_mash}:{repeat};"

    def print_effects_menu(self):
        print("\n=== Available Effects ===")
        for key, (name, _) in self.effects_menu.items():
            print(f"{key}: {name}")
        print("0: Go back")

    def print_main_menu(self):
        print("\n=== Main Menu ===")
        for key, action in self.main_menu.items():
            print(f"{key}: {action}")

    def get_effect_choice(self) -> Optional[str]:
        while True:
            self.print_effects_menu()
            choice = input("\nChoose an effect (0-9): ").strip()
            
            if choice == "0":
                return None
                
            if choice in self.effects_menu:
                _, effect_func = self.effects_menu[choice]
                return effect_func()
            
            print("Please choose a valid option")

    def run(self, file_path: Optional[str] = None):
        # Get file path if not provided

        if not file_path:
            file_path = input("Enter the path to your audio file or url to download from YouTube: ")
            if "http" in file_path:
                from djskrewcore.yt_downloader import download_video
                url = file_path
                output_path = "."
                file_path = download_video(url, output_path)

        # Create audio manager
        audio_manager = AudioManager(file_path)
        print(f"\nLoaded audio file: {file_path}")
        
        print("\nWelcome to the Audio Processor!")
        print("This tool will help you modify your audio file.")
        
        while True:
            self.print_main_menu()
            choice = input("\nWhat would you like to do? ").strip().lower()
            
            if choice == "q":
                print("Thanks for using the Audio Processor!")
                break
            elif choice == "e":
                effect = self.get_effect_choice()
                if effect:
                    if not audio_manager.process_instructions(effect):
                        break
            elif choice in ["p", "u", "r", "s"]:
                if not audio_manager.process_instructions(f"{choice};"):
                    break
            else:
                print("Please choose a valid option")
        
        audio_manager.cleanup()

def main():
    cli = FriendlyAudioCLI()
    file_path = sys.argv[1] if len(sys.argv) > 1 else None
    cli.run(file_path)

if __name__ == "__main__":
    main()