"""
Helper script to escape text for JSON testing in Swagger.
Usage: python escape_json.py
"""

import json

def escape_for_json():
    print("Paste your script text below (press Ctrl+Z then Enter on Windows, or Ctrl+D on Mac/Linux when done):")
    print("-" * 50)

    # Read multiline input
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass

    # Join all lines with newline
    script_text = "\n".join(lines)

    # Create the JSON payload
    payload = {
        "text": script_text,
        "language": "en",
        "correct_grammar": False
    }

    # Convert to JSON string (this handles all escaping)
    json_output = json.dumps(payload, indent=2)

    print("\n" + "=" * 50)
    print("Copy this JSON and paste it into Swagger:")
    print("=" * 50)
    print(json_output)
    print("=" * 50)

if __name__ == "__main__":
    escape_for_json()
