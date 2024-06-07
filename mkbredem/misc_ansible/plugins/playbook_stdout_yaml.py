'''
Parsing Logic:

The script reads the Ansible playbook stdout from a file named ansible_output.txt.
It splits the output into lines and processes each line to extract relevant information.
The pre-play metadata is collected until a line starting with "PLAY [" is encountered.
Each play and its tasks are parsed. Tasks are categorized into "ok", "included", "skipping", "changed", and "failed" lists.
The play recap section is parsed to extract the summary statistics for each host.

Data Structure:

The parsed data is stored in a dictionary with keys: "pre_play", "plays", and "play_recap".
The "pre_play" key holds the pre-play metadata as a single string.
The "plays" key holds a list of plays, each with a list of tasks and their respective statuses.
The "play_recap" key holds a dictionary mapping each host to its recap statistics.

YAML Conversion:

The parsed dictionary is converted to a YAML string using yaml.dump with default_flow_style=False to get a readable format.
The resulting YAML string is written to a file named ansible_output_parsed.yaml.
Usage
Save the script to a file, for example, ansible_output_parser.py.
Place the sample output in a file named ansible_output.txt.
Run the script with python ansible_output_parser.py.
The parsed YAML will be saved in a file named ansible_output_parsed.yaml.
This script is designed to be a starting point and might need adjustments based on variations in actual Ansible playbook outputs.

Phase 1:

Get the file to parse the sample output file as desired.

Phase 2:

Once parsing works as expected, convert project to accept play output as a variable passed as
an argument to the plugin and return a yaml formatted dictionary instead of writing to a file.
'''

import re
import yaml
from collections import defaultdict

def parse_ansible_output(output):
    playbook_header = []
    plays = []
    current_play = None
    current_task = None

    play_started = False
    task_started = False

    for line in output.splitlines():
        if not play_started:
            if line.startswith("PLAY ["):
                play_started = True
                current_play = {
                    "name": line[6:-1].strip(),
                    "tasks": []
                }
            else:
                playbook_header.append(line)
        else:
            if line.startswith("TASK ["):
                task_started = True
                if current_task:
                    current_play["tasks"].append(current_task)
                current_task = {
                    "name": line[7:-5].strip(),
                    "ok": [],
                    "included": {},
                    "skipping": [],
                    "changed": [],
                    "failed": []
                }
            elif line.startswith("PLAY RECAP"):
                if current_task:
                    current_play["tasks"].append(current_task)
                plays.append(current_play)
                current_play = None
                break
            elif task_started:
                if line.startswith("ok:"):
                    host = line.split()[1].strip()
                    if "=>" in line:
                        json_data = yaml.safe_load(line.split("=>", 1)[1].strip())
                        current_task["ok"].append({host: json_data})
                    else:
                        current_task["ok"].append(host)
                elif line.startswith("included:"):
                    match = re.search(r'included: (.+?) for (.+)', line)
                    included_file = match.group(1).strip()
                    hosts = [h.strip() for h in match.group(2).split(',')]
                    current_task["included"] = {"file": included_file, "hosts": hosts}
                elif line.startswith("skipping:"):
                    host = line.split()[1].strip()
                    current_task["skipping"].append(host)
                elif line.startswith("changed:"):
                    host = line.split()[1].strip()
                    if "=>" in line:
                        json_data = yaml.safe_load(line.split("=>", 1)[1].strip())
                        current_task["changed"].append({host: json_data})
                    else:
                        current_task["changed"].append(host)
                elif line.startswith("failed:"):
                    host = line.split()[1].strip()
                    if "=>" in line:
                        json_data = yaml.safe_load(line.split("=>", 1)[1].strip())
                        current_task["failed"].append({host: json_data})
                    else:
                        current_task["failed"].append(host)
    play_recap = {}
    recap_lines = output.split("PLAY RECAP")[1].strip().splitlines()
    for line in recap_lines:
        if ':' in line:
            parts = line.split(':')
            host = parts[0].strip()
            stats = parts[1].strip()
            recap_data = {k.strip(): int(v.strip()) for k, v in (item.split('=') for item in stats.split())}
            play_recap[host] = recap_data

    result = {
        "playbook_header": "\n".join(playbook_header),
        "plays": plays,
        "play_recap": play_recap
    }

    return result

def main():
    with open("ansible_output.txt", "r") as f:
        output = f.read()

    parsed_output = parse_ansible_output(output)
    yaml_output = yaml.dump(parsed_output, default_flow_style=False)

    with open("ansible_output_parsed.yaml", "w") as f:
        f.write(yaml_output)

if __name__ == "__main__":
    main()
