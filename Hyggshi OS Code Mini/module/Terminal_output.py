import subprocess
import os
import sys
import threading
from collections import deque

class TerminalOutput:
    """Terminal output handler for executing commands"""
    
    def __init__(self, max_history=100):
        self.command_history = deque(maxlen=max_history)
        self.current_directory = os.getcwd()
        self.environment = os.environ.copy()
        
    def run_command(self, command, cwd=None, timeout=30):
        """
        Execute a command and return output, error, and return code
        
        Args:
            command (str): Command to execute
            cwd (str): Working directory
            timeout (int): Command timeout in seconds
            
        Returns:
            tuple: (stdout, stderr, returncode)
        """
        if cwd is None:
            cwd = self.current_directory
            
        try:
            # Add command to history
            self.command_history.append(command)
            
            # Handle special commands that modify shell state
            if command.strip().startswith('cd '):
                return self._handle_cd_command(command, cwd)
            
            # Execute command
            if sys.platform.startswith('win'):
                # Windows
                process = subprocess.run(
                    command,
                    shell=True,
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    env=self.environment
                )
            else:
                # Unix/Linux/macOS
                process = subprocess.run(
                    command,
                    shell=True,
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    env=self.environment
                )
            
            return process.stdout, process.stderr, process.returncode
            
        except subprocess.TimeoutExpired:
            return "", f"Command timed out after {timeout} seconds", -1
        except subprocess.SubprocessError as e:
            return "", f"Subprocess error: {str(e)}", -1
        except Exception as e:
            return "", f"Error executing command: {str(e)}", -1
    
    def _handle_cd_command(self, command, current_cwd):
        """Handle cd command to change directory"""
        try:
            parts = command.strip().split(maxsplit=1)
            if len(parts) == 1:
                # cd without arguments - go to home
                new_dir = os.path.expanduser("~")
            else:
                new_dir = parts[1]
                
            # Resolve relative paths
            if not os.path.isabs(new_dir):
                new_dir = os.path.join(current_cwd, new_dir)
                
            new_dir = os.path.abspath(new_dir)
            
            if os.path.exists(new_dir) and os.path.isdir(new_dir):
                self.current_directory = new_dir
                os.chdir(new_dir)
                return f"Changed directory to: {new_dir}", "", 0
            else:
                return "", f"Directory not found: {new_dir}", 1
                
        except Exception as e:
            return "", f"Error changing directory: {str(e)}", 1
    
    def run_command_async(self, command, callback=None, cwd=None):
        """
        Run command asynchronously
        
        Args:
            command (str): Command to execute
            callback (callable): Callback function to handle results
            cwd (str): Working directory
        """
        def execute():
            result = self.run_command(command, cwd)
            if callback:
                callback(result)
                
        thread = threading.Thread(target=execute)
        thread.daemon = True
        thread.start()
        return thread
    
    def get_command_history(self):
        """Get command history"""
        return list(self.command_history)
    
    def clear_history(self):
        """Clear command history"""
        self.command_history.clear()
    
    def set_environment_variable(self, key, value):
        """Set environment variable"""
        self.environment[key] = value
        os.environ[key] = value
    
    def get_environment_variable(self, key, default=None):
        """Get environment variable"""
        return self.environment.get(key, default)
    
    def get_current_directory(self):
        """Get current working directory"""
        return self.current_directory
    
    def set_current_directory(self, directory):
        """Set current working directory"""
        if os.path.exists(directory) and os.path.isdir(directory):
            self.current_directory = os.path.abspath(directory)
            os.chdir(self.current_directory)
            return True
        return False

# Test the module
if __name__ == "__main__":
    terminal = TerminalOutput()
    
    # Test basic command
    print("Testing basic command:")
    stdout, stderr, returncode = terminal.run_command("echo Hello World")
    print(f"stdout: {stdout}")
    print(f"stderr: {stderr}")
    print(f"returncode: {returncode}")
    
    # Test directory listing
    print("\nTesting directory listing:")
    stdout, stderr, returncode = terminal.run_command("dir" if sys.platform.startswith('win') else "ls")
    print(f"stdout: {stdout[:200]}...")  # First 200 chars
    
    # Test cd command
    print("\nTesting cd command:")
    stdout, stderr, returncode = terminal.run_command("cd ..")
    print(f"stdout: {stdout}")
    print(f"Current directory: {terminal.get_current_directory()}")