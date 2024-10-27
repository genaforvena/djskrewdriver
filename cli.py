import sys
import threading
import time

class InputHandler:
    def __init__(self, processor):
        """Initialize the input handler with an audio processor"""
        self.processor = processor
        self.command_buffer = ""
        self.running = True
    
    def start(self):
        """Start the input handler"""
        try:
            while self.running:
                command = input("> ").strip()
                if command:
                    self._handle_command(command)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the input handler"""
        self.running = False
    
    def _handle_command(self, command):
        """Process a command string"""
        # Process the command through the audio processor
        try:
            if not self.processor.process_instructions(command):
                self.running = False
        except Exception as e:
            print(f"Error processing command: {str(e)}")

def print_controls():
    """Print available controls"""
    print("\nControls:")
    print("q; - Quit the program")
    print("s; - Save current state")
    print("a; - Apply changes")
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
        arg = sys.argv[1].strip("'\"")  # Remove quotes from the file path
        file_path = arg.strip('"')  # Ensure no quotes are present
        if arg.startswith('https'):
            from djskrewcore.yt_downloader import download_video
            url = arg
            output_path = "."
            file_path = download_video(url, output_path)
        else:
            file_path = arg  # Ensure no quotes are present
        
        if len(sys.argv) > 2:
            commands = sys.argv[2]
    
    # Get file path if not provided
    if not file_path:
        file_path = input("Enter the path to your audio file (or leave blank to download from YouTube): ")  # Ensure no quotes are present
        if not file_path:
            from djskrewcore.yt_downloader import download_video
            url = input("Enter the YouTube video URL: ")
            output_path = "."
            file_path = download_video(url, output_path)
            if not file_path:
                raise FileNotFoundError("Failed to download the video.")

    # Create audio processor
    from djskrewcore.main import AudioProcessor
    processor = AudioProcessor(file_path)
    print(f"\nLoaded audio file: {file_path}")
    
    # Handle command-line commands
    if commands:
        print(f"Processing commands: {commands}")
        processor.process_instructions(commands)
        processor.save_current_state()
        print("\nProcessing complete. File saved.")
        processor.cleanup()
        return
    
    # Enter interactive mode
    print_controls()
    
    # Create and start input handler
    handler = InputHandler(processor)
    try:
        handler.start()
    except Exception as e:
        print(f"Error in input handler: {str(e)}")
    finally:
        handler.stop()
        processor.cleanup()
        print("\nExiting...")

if __name__ == "__main__":
    main()
