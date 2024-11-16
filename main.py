import os
import re
import subprocess
from datetime import datetime


def parse_whatsapp_txt(file_path):
    """
    Parse WhatsApp exported .txt file to extract messages and media references.
    """
    messages = []

    # message_pattern = re.compile(r"^\[(\d{2}/\d{2}/\d{4}), (\d{2}:\d{2})\] (.*?): (.*)$")
    # Regex to match WhatsApp message format
    message_pattern = re.compile(r"^\[(\d{2}/\d{2}/\d{4} BE), (\d{2}:\d{2}:\d{2})\] (.*?): (.*)$")

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            match = message_pattern.match(line)
            if match:
                date_str, time_str, sender, content = match.groups()
                # timestamp = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M")
                timestamp = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y BE %H:%M:%S")
                messages.append({
                    "timestamp": timestamp,
                    "sender": sender,
                    "content": content.strip()
                })

    return messages


def convert_opus_to_mp3(opus_file, output_folder):
    """
    Convert an OPUS file to MP3 using FFmpeg.
    """
    mp3_file = os.path.join(output_folder, os.path.splitext(opus_file)[0] + '.mp3')

    # Check if the MP3 file already exists; if not, convert it
    if not os.path.exists(mp3_file):
        try:
            subprocess.run(['ffmpeg', '-i', opus_file, mp3_file], check=True)
            print(f"Converted {opus_file} to {mp3_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error converting {opus_file}: {e}")

    return mp3_file


def convert_to_html(messages, media_folder):
    """
    Convert parsed messages to HTML format.
    """
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WhatsApp Chat Export</title>
    <style>
        body { font-family: Arial, sans-serif; }
        .message { margin-bottom: 10px; }
        .timestamp { color: gray; font-size: 0.9em; }
        .sender { font-weight: bold; }
        img { max-width: 300px; height: auto; }
        video { max-width: 300px; height: auto; }
        audio { width: 300px; }
    </style>
</head>
<body>
<h1>WhatsApp Chat Export</h1>
'''

    for msg in messages:
        timestamp_html = f'<span class="timestamp">[{msg["timestamp"].strftime("%d/%m/%Y, %H:%M")}]</span>'
        sender_html = f'<span class="sender">{msg["sender"]}:</span>'

        # Check if the content is a media reference
        content_html = msg["content"]

        # Process media files (images, videos, audio)
        if re.match(r".*\.(jpg|jpeg|png|gif)$", msg["content"], re.IGNORECASE):
            content_html = f'<img src="{os.path.join(media_folder, msg["content"])}" alt="Image">'
        elif re.match(r".*\.(mp4|mov|avi)$", msg["content"], re.IGNORECASE):
            content_html = f'<video controls><source src="{os.path.join(media_folder, msg["content"])}" type="video/mp4">Your browser does not support the video tag.</video>'
        elif re.match(r".*\.opus$", msg["content"], re.IGNORECASE):
            # Convert OPUS to MP3 and embed it in HTML as an audio element
            opus_path = os.path.join(media_folder, msg["content"])
            mp3_path = convert_opus_to_mp3(opus_path, media_folder)
            content_html = f'<audio controls><source src="{mp3_path}" type="audio/mpeg">Your browser does not support the audio element.</audio>'

        # Add message to HTML
        html_content += f'<div class="message">{timestamp_html} {sender_html} {content_html}</div>\n'

    html_content += '''
</body>
</html>
'''

    return html_content


def save_html(output_path, html_content):
    """
    Save generated HTML content to a file.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)


def main(data_folder):
    txt_file_path = os.path.join(data_folder, '_chat.txt')

    # Parse the WhatsApp .txt file
    messages = parse_whatsapp_txt(txt_file_path)

    # Convert parsed data to HTML
    html_content = convert_to_html(messages, data_folder)

    # Save the output HTML file
    output_file_path = txt_file_path.replace('.txt', '.html')
    save_html(output_file_path, html_content)

    print(f"HTML file saved at {output_file_path}")


if __name__ == "__main__":
    # Example usage
    # Path to the exported WhatsApp .txt file
    input_folder = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'input',
        'chat_history'
    )

    output_folder = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'output',
        str(int(datetime.now().timestamp()))
    )

    # os.makedirs(output_folder, exist_ok=True)

    # copy everything from input/chat_history path to the newly created output directory, using python
    import shutil
    shutil.copytree(input_folder, output_folder)

    main(output_folder)
