import re
import json
from datetime import datetime

# Path configuration
INPUT_TXT = "WhatsApp Chat with Craftly.txt"
OUTPUT_JSONL = "messages.jsonl"

# Regex for standard WhatsApp line: [8/21/26, 11:04:12 PM] Name: Message
MESSAGE_PATTERN = re.compile(
    r"^\[(?P<date>\d{1,2}/\d{1,2}/\d{2}),\s(?P<time>\d{1,2}:\d{2}:\d{2}\s[AP]M)\]\s(?P<speaker>[^:]+):\s(?P<message>.*)$"
)

def parse_whatsapp(input_path, output_path):
    parsed_messages = []
    current_msg = None
    msg_id_counter = 1

    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            match = MESSAGE_PATTERN.match(line)
            
            if match:
                if current_msg:
                    parsed_messages.append(current_msg)
                
                dt_str = f"{match.group('date')} {match.group('time')}"
                dt_obj = datetime.strptime(dt_str, "%m/%d/%y %I:%M:%S %p")
                
                current_msg = {
                    "message_id": f"msg_{msg_id_counter:06d}",
                    "timestamp": dt_obj.isoformat(),
                    "speaker": match.group("speaker").strip(),
                    "message": match.group("message").strip(),
                    "reply_to": None,
                    "topics": [],
                    "speech_act": None,
                    "evidence": True
                }
                msg_id_counter += 1
            else:
                # Append multi-line strings to previous message body
                if current_msg:
                    current_msg["message"] += f"\n{line}"

        if current_msg:
            parsed_messages.append(current_msg)

    with open(output_path, 'w', encoding='utf-8') as f:
        for msg in parsed_messages:
            f.write(json.dumps(msg, ensure_ascii=False) + '\n')

    print(f"Successfully parsed {len(parsed_messages)} messages into {output_path}")

if __name__ == "__main__":
    parse_whatsapp(INPUT_TXT, OUTPUT_JSONL)