import os
import subprocess
import threading
import queue
import time
import re

class MinecraftServer:
    def __init__(self, batch_file="run.bat", server_dir="./server"):
        self.server_path = os.path.abspath(os.path.join(server_dir, batch_file))
        self.server_process = None  # Holds the server subprocess
        self.output_queue = queue.Queue(maxsize=128)  # For capturing stdout
        self.stop_event = threading.Event()  # Used to signal stopping
        self.server_thread = None  # Thread for reading stdout
        self.lock = threading.Lock()  # Ensures thread-safe operations
        self.server_ready = threading.Event()  # Indicates when the server is ready
        self.console_title = "MinecraftServerConsole"  # Unique console title for management

    def start_server(self) -> bool:
        if self.server_process is not None:
            print("Server is already running.")
            return

        try:
            # Launch the server in a new command prompt
            command = f'start "{self.console_title}" /B cmd /c "{self.server_path}"'
            self.server_process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                shell=True
            )
            print("[INFO]: Server started in a separate command prompt window.")
        except Exception as e:
            print(f"Error starting server: {e}")
            return False
        else:
            # Start a thread to monitor server output
            self.stop_event.clear()
            self.server_ready.clear()
            self.server_thread = threading.Thread(target=self._read_stdout, daemon=True)
            self.server_thread.start()
            return True

    def _read_stdout(self):
        ready_pattern = re.compile(r"\[.*?\] \[Server thread/INFO\]: Done \(.*?\)! For help, type \"help\"")
        try:
            while not self.stop_event.is_set():
                if self.server_process.stdout is None:
                    continue
                
                line = self.server_process.stdout.readline()
                if not line:
                    break
                
                stripped_line = line.strip()
                
                with self.lock:
                    # Always add the line to the queue if it's not empty
                    if stripped_line and not self.output_queue.full():
                        self.output_queue.put(stripped_line)
                
                # Check for server ready message
                if ready_pattern.search(line):
                    print("\n[DEBUG]: Server is now ready!")
                    self.server_ready.set()
        except Exception as e:
            print(f"Error reading stdout: {e}")

    def send_command(self, command):
        if not self.server_ready.is_set():
            print("Server is not ready to receive commands. Please wait.")
            return None

        try:
            # Send the command to the server stdin
            if self.server_process.stdin:
                self.server_process.stdin.write(f"{command}\n")
                self.server_process.stdin.flush()
                print(f"[INFO]: Command sent -> {command}")
                
                # Wait a short time for the server to process the command
                time.sleep(0.5)
                
                # Collect output
                output = []
                start_time = time.time()
                while time.time() - start_time < 5:  # 5-second timeout
                    with self.lock:
                        while not self.output_queue.empty():
                            line = self.output_queue.get()
                            if line and line not in output:
                                output.append(line)
                    
                    if output:
                        return output
                    
                    time.sleep(0.1)
                
                print("[WARNING]: No output received from server command.")
                return None
            else:
                print("[ERROR]: Cannot send command; stdin is not available.")
                return None
        except Exception as e:
            print(f"Error sending command: {e}")
            return None
        
    def get_output(self):
        output = []
        with self.lock:
            while not self.output_queue.empty():
                output.append(self.output_queue.get())
        return output

    def stop_server(self) -> bool:
        if self.server_process is None:
            print("Server is not running.")
            return True

        # Send the stop command
        self.send_command("stop")
        time.sleep(5)  # Give the server time to stop
        
        # Close the command prompt window
        try:
            os.system(f'taskkill /FI "WINDOWTITLE eq {self.console_title}" /T /F')
            print("[INFO]: Server has been stopped.")
        except Exception as e:
            print(f"Error stopping server: {e}")
            return False
        else:
            self.stop_event.set()
            self.server_thread.join()
            self.server_process = None

    def is_running(self):
        return self.server_process is not None
    
# Example usage
if __name__ == "__main__":
    server = MinecraftServer()

    # Start the server
    server.start_server()

    # Wait for the server to be ready
    server.server_ready.wait()
    print(server.is_running())
    try:
        while True:
            # Example of sending a command
            command = input("Enter command: ")
            if command.strip().lower() == "exit":
                break
            print(server.send_command(command)[-1])
            # Get server output
            output = server.get_output()
            for line in output:
                print(f"[Server]: {line}")
    finally:
        server.stop_server()
        print(server.is_running())
