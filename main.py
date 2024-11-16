import os
import re
import subprocess
from datetime import datetime

def parse_whatsapp_txt(file_path):
    """
    Parse WhatsApp exported .txt file to extract messages and media references.
    """
    messages = []
    chat_participants = []

    # Regex to match WhatsApp message format
    message_pattern = re.compile(r"(?m)^\[\d{1,2}/\d{1,2}/\d{4} BE, \d{2}:\d{2}:\d{2}\] .*?(?=(?:^\[\d{1,2}/\d{1,2}/\d{4} BE, \d{2}:\d{2}:\d{2}\])|$)")

    # Regex to capture individual messages
    message_regex = re.compile(
        r'(\[\d{1,2}\/\d{1,2}\/\d{4} BE, \d{2}:\d{2}:\d{2}\]) (.*?): (.*?)(?=^\[\d{1,2}\/\d{1,2}\/\d{4} BE, \d{2}:\d{2}:\d{2}\]|$)'
    )

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            # Parse the chat export
            matches = message_regex.findall(line)

            # Process and print the captured data
            for match in matches:
                timestamp, sender, message = match
                # Convert Thai date format to US standard datetime format
                date_str, time_str = timestamp.replace('[', '').replace(']', '').split(" BE, ")
                date_obj = datetime.strptime(date_str, "%d/%m/%Y")
                # Convert BE year to Gregorian year
                date_obj = date_obj.replace(year=date_obj.year - 543)
                timestamp = datetime.strptime(f"{date_obj.strftime('%d/%m/%Y')} {time_str}", "%d/%m/%Y %H:%M:%S")
                messages.append({
                    "timestamp": timestamp,
                    "sender": sender,
                    "content": message.strip()
                })

                if sender not in chat_participants:
                    chat_participants.append(sender)

    # with open(file_path, 'r', encoding='utf-8') as f:
    #     for line in f:
    #         match = message_pattern.match(line)
    #         if match:
    #             date_str, time_str, sender, content = match.groups()
    #             # Convert Thai date format to US standard datetime format
    #             date_str = date_str.replace(" BE", "")
    #             date_obj = datetime.strptime(date_str, "%d/%m/%Y")
    #             # Convert BE year to Gregorian year
    #             date_obj = date_obj.replace(year=date_obj.year - 543)
    #             timestamp = datetime.strptime(f"{date_obj.strftime('%d/%m/%Y')} {time_str}", "%d/%m/%Y %H:%M:%S")
    #             messages.append({
    #                 "timestamp": timestamp,
    #                 "sender": sender,
    #                 "content": content.strip()
    #             })

    return messages, chat_participants

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

def convert_to_html(messages, media_folder, participant1, participant2):
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
        body { font-family: Arial, sans-serif; background-color: #e5ddd5; padding: 20px; }
        .message { 
            margin-bottom: 20px;
            max-width: 65%;
            min-width: 12%;
            padding: 10px;
            border-radius: 10px;
            position: relative;
        }
        .message.left { background-color: #ffffff; align-self: flex-start; }
        .message.right { background-color: #dcf8c6; align-self: flex-end; }
        .timestamp.left { color: gray; font-size: 0.8em; position: absolute; bottom: -15px; left: 3px; }
        .timestamp.right { color: gray; font-size: 0.8em; position: absolute; bottom: -15px; right: 3px; }
        .sender { font-weight: bold; margin-bottom: 5px; }
        img { max-width: 300px; height: auto; border: 1px solid #ccc; border-radius: 5px; }
        video { max-width: 300px; height: auto; }
        audio { width: 300px; }
        .chat-container { display: flex; flex-direction: column; }
    </style>
</head>
<body>
<h1>WhatsApp Chat Export</h1>
<div class="chat-container">
'''

    previous_sender = None
    for msg in messages:
        alignment_class = "left" if msg["sender"] == participant1 else "right"
        previous_sender = msg["sender"]
        timestamp_html = f'<span class="timestamp {alignment_class}">{msg["timestamp"].strftime("%d/%m/%Y, %I:%M:%S %p")}</span>'
        sender_html = f'<div class="sender">{msg["sender"]}:</div>'

        # Check if the content is a media reference
        content_html = msg["content"]

        # Process media files (images, videos, audio)
        if "<attached:" in content_html:
            media_file = re.search(r"<attached: (.*?)>", content_html).group(1)
            if re.match(r".*\.(jpg|jpeg|png|gif|webp)$", media_file, re.IGNORECASE):
                content_html = f'<img src="{os.path.join(media_folder, media_file)}" alt="Image">'
            elif re.match(r".*\.(mp4|mov|avi)$", media_file, re.IGNORECASE):
                content_html = f'<video controls><source src="{os.path.join(media_folder, media_file)}" type="video/mp4">Your browser does not support the video tag.</video>'
            elif re.match(r".*\.opus$", media_file, re.IGNORECASE):
                # Convert OPUS to MP3 and embed it in HTML as an audio element
                opus_path = os.path.join(media_folder, media_file)
                mp3_path = convert_opus_to_mp3(opus_path, media_folder)
                content_html = f'<audio controls><source src="{mp3_path}" type="audio/mpeg">Your browser does not support the audio element.</audio>'
            elif re.match(r".*\.(pdf)$", media_file, re.IGNORECASE):
                content_html = f'<a href="{os.path.join(media_folder, media_file)}" target="_blank">{media_file}</a>'

        # Add message to HTML
        html_content += f'<div class="message {alignment_class}">{sender_html} {content_html} {timestamp_html}</div>\n'

    html_content += '''
</div>
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
    messages, participants = parse_whatsapp_txt(txt_file_path)

    # Convert parsed data to HTML
    html_content = convert_to_html(messages, data_folder, participants[0], participants[1])

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