#!/usr/bin/env python3

import subprocess
import shlex
import sys
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# ============================
# Command Categorization Lists
# ============================

# 1. Strictly Prohibited Commands (nopeCommands)
nope_commands = [
    # System and File Manipulation
    'rm', 'chmod', 'chown', 'chgrp', 'mkfs', 'mount', 'umount', 'dd',

    # System Control and Shutdown
    'shutdown', 'reboot', 'poweroff', 'init', 'systemctl', 'journalctl',

    # User and Access Control
    'user', 'passwd', 'sudo', 'su',

    # Process and Kernel Manipulation
    'kill', 'dmesg', 'lsmod', 'modprobe', 'insmod', 'rmmod',

    # Network and Firewall Commands
    'iptables', 'firewalld', 'ufw', 'nc',

    # System Scheduling and Kernel Settings
    'crontab', 'at', 'swapon', 'swapoff',

    # Hardware Inspection Commands
    'lsusb', 'lspci', 'lsblk',

    # System History
    'history'
]

# 2. Confirmation-Required Commands (confirmCommands)
confirm_commands = [
    # Remote File Fetching
    'curl', 'wget',

    # Package Management and Installation
    'pip', 'pip3', 'npm', 'yarn', 'apt-get', 'apt', 'yum', 'dnf', 'pacman', 'brew',

    # System-Level Configuration and Modifications
    'sysctl', 'ulimit', 'update-alternatives', 'locale-gen',

    # Version Management and Environment Setup
    'nvm', 'rbenv', 'pyenv', 'sdk', 'snap',

    # Network and Tunneling
    'ssh', 'scp', 'ftp', 'sftp', 'rsync',

    # Virtual Environment and Container Management
    'docker', 'docker-compose', 'podman', 'kubectl', 'minikube',

    # System-Wide Services and Daemons
    'service', 'launchctl',

    # Disk and Filesystem Management Tools
    'fdisk', 'mkfs.ext4', 'mkfs.ntfs', 'resize2fs', 'e2fsck', 'fsck',

    # Virtual Machines and Kernel Modifications
    'qemu', 'kvm',

    # User Session Management
    'loginctl', 'useradd', 'usermod', 'groupadd', 'groupmod',

    # System Logs and Network Connections
    'netstat', 'ss', 'tcpdump', 'nmap',

    # File Operations with Potential Overwrites
    'mv', 'cp', 'ln -s',

    # Environment Variable and Shell Configuration
    'export', 'source',

    # Process Monitoring and File Listings
    'top', 'ps', 'df', 'du',

    # Miscellaneous Risky Commands
    'alias', 'reset', 'stty'
]

# 3. Secondary Filters (secondaryFilters)
# Each filter includes the command, optional subcommand, condition function, and message.
secondary_filters = [
    {
        "command": "pip",
        "subcommand": "install",
        "condition": lambda args: any(arg.startswith('--trusted-host') for arg in args) or is_within_virtualenv(),
        "message": "Ensure that pip installations are from trusted sources or within a virtual environment."
    },
    {
        "command": "npm",
        "subcommand": "install",
        "condition": lambda args: '-g' not in args and is_within_project_directory(),
        "message": "NPM installations are allowed only within the project directory and without global flags."
    },
    {
        "command": "docker",
        "subcommand": None,
        "condition": lambda args: 'run' in args or 'build' in args,
        "message": "Docker operations are restricted to running or building images without modifying the host system."
    },
    {
        "command": "ssh",
        "subcommand": None,
        "condition": lambda args: is_trusted_host(args[-1]) if args else False,
        "message": "SSH connections are allowed only to predefined trusted hosts."
    },
    {
        "command": "git",
        "subcommand": "push",
        "condition": lambda args: is_allowed_remote(args[-1]) if args else False,
        "message": "Git push operations are restricted to allowed remote repositories."
    }
]

# ============================
# Helper Functions
# ============================

def is_within_virtualenv() -> bool:
    """Check if the current environment is a Python virtual environment."""
    return (hasattr(sys, 'real_prefix') or 
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))

def is_within_project_directory() -> bool:
    """Check if the current working directory is a project directory."""
    # Placeholder: Implement logic to determine if within a project directory
    # For example, check for presence of certain files like requirements.txt, package.json, etc.
    required_files = ['requirements.txt', 'package.json', 'Pipfile', 'pyproject.toml']
    cwd_files = subprocess.check_output(['ls']).decode().split()
    return any(file in cwd_files for file in required_files)

def is_trusted_host(host: str) -> bool:
    """Check if the SSH host is in the list of trusted hosts."""
    trusted_hosts = ['github.com', 'gitlab.com', 'bitbucket.org']
    return host in trusted_hosts

def is_allowed_remote(remote: str) -> bool:
    """Check if the Git remote is in the list of allowed remotes."""
    allowed_remotes = ['origin', 'upstream']
    return remote in allowed_remotes

def confirm(prompt: str) -> bool:
    """Prompt the user for confirmation in CLI."""
    while True:
        response = input(f"{prompt} (y/n): ").lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please respond with 'y' or 'n'.")

# ============================
# Command Execution Function
# ============================

def execute_command(command: str, user_confirm: Optional[bool] = None) -> str:
    """
    Classify and execute a command based on predefined categories.

    Args:
        command (str): The full command string to execute.
        user_confirm (Optional[bool]): Confirmation from API client. If None, prompt user in CLI.

    Returns:
        str: Result message indicating the action taken.
    """
    parts = shlex.split(command)
    if not parts:
        return "❌ No command provided."

    base_command = parts[0]
    args = parts[1:]

    # Check for strictly prohibited commands
    if base_command in nope_commands:
        return f"❌ The command '{base_command}' is restricted and cannot be executed."

    # Check for confirmation-required commands
    if base_command in confirm_commands:
        if user_confirm is None:
            # CLI prompt
            prompt_msg = f"⚠️ The command '{command}' may pose risks. Do you want to proceed?"
            user_confirm = confirm(prompt_msg)
        elif not user_confirm:
            return "⏸️ Command execution cancelled by the user."

        if not user_confirm:
            return "⏸️ Command execution cancelled by the user."

    # Check for secondary filters
    for filter in secondary_filters:
        if filter["command"] == base_command:
            subcmd = filter.get("subcommand")
            if subcmd and len(args) > 0 and args[0] != subcmd:
                continue  # Subcommand does not match
            if filter["condition"](args):
                if user_confirm is None:
                    # CLI prompt
                    prompt_msg = f"⚠️ {filter['message']} Do you want to proceed with the command '{command}'?"
                    user_confirm = confirm(prompt_msg)
                elif not user_confirm:
                    return "⏸️ Command execution cancelled by the user."

                if not user_confirm:
                    return "⏸️ Command execution cancelled by the user."

    # Proceed with command execution
    try:
        # Execute the command safely without using shell=True
        result = subprocess.run(parts, capture_output=True, text=True, check=True)
        return f"✅ Command executed successfully.\nOutput:\n{result.stdout}"
    except subprocess.CalledProcessError as e:
        return f"❌ Command execution failed.\nError:\n{e.stderr}"
    except FileNotFoundError:
        return f"❌ Command '{base_command}' not found."
    except Exception as e:
        return f"❌ An unexpected error occurred: {str(e)}"

# ============================
# FastAPI Setup
# ============================

app = FastAPI(title="Command Classification API", version="1.0")

class CommandRequest(BaseModel):
    command: str
    confirm: Optional[bool] = None  # For API clients to provide confirmation

class CommandResponse(BaseModel):
    status: str
    message: str

@app.post("/execute", response_model=CommandResponse)
def api_execute_command(request: CommandRequest):
    """
    API endpoint to classify and execute a command.

    Args:
        request (CommandRequest): The command and optional confirmation.

    Returns:
        CommandResponse: The result of the command execution.
    """
    command = request.command
    user_confirm = request.confirm

    if any(cmd == command.split()[0] for cmd in nope_commands):
        return CommandResponse(status="blocked", message=f"❌ The command '{command.split()[0]}' is restricted and cannot be executed.")

    # Determine if confirmation is required
    if any(cmd == command.split()[0] for cmd in confirm_commands):
        if user_confirm is None:
            raise HTTPException(status_code=400, detail="Confirmation required for this command. Please set 'confirm' to true or false.")
        elif not user_confirm:
            return CommandResponse(status="cancelled", message="⏸️ Command execution cancelled by the user.")

    # Check for secondary filters
    applicable_filters = [f for f in secondary_filters if f["command"] == command.split()[0]]
    for filter in applicable_filters:
        if filter["condition"](command.split()[1:]):
            if user_confirm is None:
                raise HTTPException(status_code=400, detail=f"Confirmation required: {filter['message']}")
            elif not user_confirm:
                return CommandResponse(status="cancelled", message="⏸️ Command execution cancelled by the user.")

    # Execute the command
    result_message = execute_command(command, user_confirm)
    if result_message.startswith("✅"):
        return CommandResponse(status="success", message=result_message)
    elif result_message.startswith("⏸️"):
        return CommandResponse(status="cancelled", message=result_message)
    else:
        return CommandResponse(status="error", message=result_message)

# ============================
# CLI Interface
# ============================

def cli_interface():
    """
    Command-Line Interface to interactively input and execute commands.
    """
    print("=== Command Execution Interface ===")
    print("Type 'exit' to quit.")
    while True:
        try:
            user_input = input("Enter command: ").strip()
            if user_input.lower() in ['exit', 'quit']:
                print("Exiting CLI.")
                break
            if not user_input:
                continue
            result = execute_command(user_input)
            print(result)
        except KeyboardInterrupt:
            print("\nExiting CLI.")
            break
        except Exception as e:
            print(f"❌ An unexpected error occurred: {str(e)}")

# ============================
# Main Execution
# ============================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Command Classification and Execution Tool")
    parser.add_argument('--api', action='store_true', help="Run as FastAPI server")
    parser.add_argument('--cli', action='store_true', help="Run as CLI tool")
    parser.add_argument('--host', type=str, default="127.0.0.1", help="API server host")
    parser.add_argument('--port', type=int, default=8000, help="API server port")

    args = parser.parse_args()

    if args.api:
        print(f"Starting FastAPI server at http://{args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)
    elif args.cli:
        cli_interface()
    else:
        parser.print_help()
