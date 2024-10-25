import sys
import threading
import keyboard
import time

class InputHandler:
    def __init__(self, processor):
        """Initialize the input handler with an audio processor"""
        self.processor = processor
        self.command_buffer = ""
        self.running = True
        self.keyboard_thread = None
    
    def start(self):
        """Start the input handler threads"""
        # Start keyboard listener thread
        self.keyboard_thread = threading.Thread(target=self._keyboard_listener)
        self.keyboard_thread.daemon = True
        self.keyboard_thread.start()
        
        # Start command processing loop
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
        if self.keyboard_thread:
            self.keyboard_thread.join(timeout=1.0)
    
    def _keyboard_listener(self):
        """Listen for keyboard events in a separate thread"""
        try:
            # Set up hotkeys
            keyboard.on_press_key('space', lambda _: self.processor.playback.toggle_playback())
            keyboard.on_press_key('up', lambda _: self._handle_playback_restart())
            keyboard.on_press_key('left', lambda _: self._handle_history_navigation(-1))
            keyboard.on_press_key('right', lambda _: self._handle_history_navigation(1))
            
            # Keep thread alive
            while self.running:
                time.sleep(0.1)
        except Exception as e:
            print(f"Keyboard listener error: {str(e)}")
        finally:
            keyboard.unhook_all()
    
    def _handle_command(self, command):
        """Process a command string"""
        # Handle special commands
        if command == 'q;':
            self.running = False
            return
        
        # Process the command through the audio processor
        try:
            if not self.processor.process_instructions(command):
                self.running = False
        except Exception as e:
            print(f"Error processing command: {str(e)}")
    
    def _handle_playback_restart(self):
        """Handle playback restart"""
        try:
            self.processor.playback.reset_position()
            self.processor.playback.start_playback()
        except Exception as e:
            print(f"Error restarting playback: {str(e)}")
    
    def _handle_history_navigation(self, direction):
        """Handle history navigation (undo/redo)
        direction: -1 for undo, 1 for redo"""
        try:
            if direction < 0 and self.processor.history.can_undo():
                file_path, ops = self.processor.history.undo()
            elif direction > 0 and self.processor.history.can_redo():
                file_path, ops = self.processor.history.redo()
            else:
                return
            
            # Store playback state
            was_playing = self.processor.playback.is_playing
            position = self.processor.playback.current_position
            
            if was_playing:
                self.processor.playback.pause_playback()
            
            # Update audio
            if file_path:
                self.processor.update_audio_state(file_path)
                if was_playing:
                    self.processor.playback.start_playback(position)
                
            self.processor.print_history_status()
            
        except Exception as e:
            print(f"Error navigating history: {str(e)}")

def print_controls():
    """Print available controls"""
    print("\nControls:")
    print("Space: Play/Pause")
    print("Up Arrow: Restart playback")
    print("Left/Right Arrows: Navigate history")
    print("Enter: Execute command")
    print("s;: Save current version")
    print("q;: Exit")
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
