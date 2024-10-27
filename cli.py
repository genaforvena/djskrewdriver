from typing import Optional
import sys
import threading
import time
import queue
from djskrewcore.audio import AudioManager

class InputHandler:
    def __init__(self, audio_manager):
        self.audio_manager = audio_manager
        self.command_queue = queue.Queue()
        self.running = True
        self._input_thread = threading.Thread(target=self._input_loop)
        self._command_thread = threading.Thread(target=self._command_loop)
        self._input_thread.daemon = True
        self._command_thread.daemon = True

    def start(self):
        """Start the input handler threads"""
        self._input_thread.start()
        self._command_thread.start()

    def stop(self):
        """Stop the input handler"""
        self.running = False
        self.command_queue.put(None)  # Signal to stop command thread

    def _input_loop(self):
        """Handle user input in a separate thread"""
        try:
            while self.running:
                command = input("> ").strip()
                if command:
                    self.command_queue.put(command)
        except (KeyboardInterrupt, EOFError):
            self.stop()

    def _command_loop(self):
        """Process commands in a separate thread"""
        while self.running:
            try:
                command = self.command_queue.get(timeout=0.5)
                if command is None:
                    break
                try:
                    if not self.audio_manager.process_instructions(command):
                        self.running = False
                except Exception as e:
                    print(f"Error processing command: {str(e)}")
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Command thread error: {str(e)}")
                continue

def print_controls():
    """Print available controls"""
    print("\nControls:")
    print("q; - Quit the program")
    print("s; - Save current state")
    print("p; - Toggle playback")
    print("u; - Undo last operation")
    print("r; - Redo last undone operation")
    print("l; - Load a new audio file")
    print("h; - Print this help message")
    print("\nCommand syntax:")
    print("command:value1:value2:value3;")
    print("Examples:")
    print("- p:-2;              (Lower pitch by 2 semitones)")
    print("- loop:2:8:4;        (2-beat loops, 8 beats long, every 4 beats)")
    print("- rev:1:4:2;         (Reverse every beat, 4 beats long, every 2 beats)")
    print("\nNote: All commands must end with a semicolon (;)")

def main():
    # Parse command line arguments
    file_path = None
    commands = None
    
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg.startswith('https'):
            from djskrewcore.yt_downloader import download_video
            url = arg
            output_path = "."
            file_path = download_video(url, output_path)
        else:
            file_path = arg
        
        if len(sys.argv) > 2:
            commands = sys.argv[2]
    
    # Get file path if not provided
    if not file_path:
        file_path = input("Enter the path to your audio file (or leave blank to download from YouTube): ")
        if not file_path:
            from djskrewcore.yt_downloader import download_video
            url = input("Enter the YouTube video URL: ")
            output_path = "."
            file_path = download_video(url, output_path)

    # Create audio manager
    audio_manager = AudioManager(file_path)
    print(f"\nLoaded audio file: {file_path}")
    
    # Handle command-line commands
    if commands:
        print(f"Processing commands: {commands}")
        audio_manager.process_instructions(commands)
        audio_manager.save_current_state()
        print("\nProcessing complete. File saved.")
        audio_manager.cleanup()
        return
    
    # Enter interactive mode
    print_controls()
    
    # Create and start input handler
    handler = InputHandler(audio_manager)
    try:
        handler.start()
        # Keep main thread alive
        while handler.running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        handler.stop()
        audio_manager.cleanup()

if __name__ == "__main__":
    main()