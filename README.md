# nopeCommands
Some guardrails from AI doing NOPEs
🚫 NopeCommands - Command Safety and Execution Tool
NopeCommands is a secure command execution and classification tool designed to protect against potentially harmful shell commands. The nope.py script filters commands into categories that require restriction, user confirmation, or conditional permission checks before execution. This project includes a CLI interface and a FastAPI-based API for easy and flexible integration.

🎯 Features
Command Categorization: Classifies commands into Strictly Prohibited, Confirmation Required, and Conditionally Allowed categories.
Interactive CLI: Prompts users for confirmation on risky commands, while blocking or conditionally permitting other commands.
API Integration: Exposes a REST API endpoint, allowing applications to validate and execute commands safely.
Secondary Filters: Context-based rules apply further validation, especially for commands such as pip install and ssh.
Extensibility: Easily add or modify command lists and rules to meet specific organizational or individual needs.
🛠 Installation
Clone the Repository

bash
Copy code
git clone https://github.com/matlowai/nopeCommands.git
cd nopeCommands
Install Dependencies

bash
Copy code
pip install fastapi uvicorn
Run with CLI or API (See usage below).

🚀 Usage
1. CLI Mode
The CLI mode allows you to enter and validate commands interactively, providing instant feedback on the categorization and execution status.

Start CLI Mode:

bash
Copy code
python nope.py --cli
Example CLI Interaction
plaintext
Copy code
=== Command Execution Interface ===
Type 'exit' to quit.
Enter command: ls -la
✅ Command executed successfully.
Output:
total 48
drwxr-xr-x 6 user user 4096 Nov  2 12:00 .
...

Enter command: rm -rf /
❌ The command 'rm' is restricted and cannot be executed.
2. API Mode
NopeCommands also provides a FastAPI server for programmatic command validation and execution.

Start the API Server:

bash
Copy code
python nope.py --api --host 0.0.0.0 --port 8000
Example API Request
Use curl or any HTTP client to test commands through the API:

bash
Copy code
curl -X POST "http://localhost:8000/execute" -H "Content-Type: application/json" -d '{"command": "curl http://example.com", "confirm": true}'
Sample API Response
json
Copy code
{
    "status": "success",
    "message": "✅ Command executed successfully.\nOutput:\n<!doctype html>\n<html>...</html>"
}
📂 Command Classification Overview
NopeCommands categorizes commands into three lists for security and control:

1. Strictly Prohibited Commands (nope_commands)
Commands that are too risky to execute under any circumstance are fully restricted. These include:

rm, chmod, shutdown, user, passwd, kill, history
2. Confirmation-Required Commands (confirm_commands)
Useful but risky commands require explicit user confirmation. Examples include:

curl, wget, pip, npm, ssh, docker, scp, mv, top
3. Secondary Filters (secondary_filters)
These commands are allowed with contextual checks. Examples:

pip install only allowed in a virtual environment or from trusted sources.
ssh only allowed to trusted hosts.
git push restricted to specified remote repositories.
🧩 Customization
To extend the command lists or modify behavior:

Add commands to nope_commands to block unconditionally.
Add commands to confirm_commands for those requiring user confirmation.
Modify secondary_filters to apply additional checks for certain commands.
🔒 Security Considerations
NopeCommands maximizes command-line security by restricting, confirming, or filtering commands based on their potential risk. For production use, consider:

Logging: Track command execution and confirmation requests.
Auditing: Review interactions to maintain security oversight.
Monitoring: Use monitoring tools to observe command activity in real-time.
🧪 Testing
For local testing, use the CLI or API mode as described above to validate the behavior of various commands. API tests can be automated using tools like Postman or curl scripts.

⚠️ Disclaimer
While NopeCommands provides comprehensive filtering and security checks, it does not cover every possible dangerous command or situation. Users are encouraged to review, extend, and contribute to this project to improve its robustness. Help us make this tool better by adding more commands, filters, or additional checks for the community.

📄 License
This project is licensed under the Apache 2.0 License.

📬 Feedback and Contributions
Contributions and feedback are welcome! Open an issue or a pull request to suggest features, report issues, or contribute to the project.

Happy secure scripting with NopeCommands! 🎉
