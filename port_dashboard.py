import os
import re

source = r"d:\DATA SCIENCE AND ML\Project\job_trend_predictor\dashboards\components\career_counslor_dashboard.py"
dest = r"d:\DATA SCIENCE AND ML\Project\job_trend_predictor\dashboards\pages\counselor_dashboard.py"

with open(source, "r", encoding="utf-8") as f:
    code = f.read()

# Remove set_page_config completely
code = re.sub(r'st\.set_page_config\([^)]+\)', '', code, flags=re.DOTALL)

# Find the start of the layout code which needs to be wrapped in render()
# Looking for "Minimal custom CSS" header
split_marker = "# Minimal custom CSS"
if split_marker not in code:
    print("Error: Could not find split marker")
    exit(1)

parts = code.split(split_marker)
header = parts[0]
body = split_marker + parts[1]

# Indent the body block by 4 spaces
body_indented = ""
for line in body.split('\n'):
    if line.strip() == "":
        body_indented += "\n"
    else:
        body_indented += "    " + line + "\n"

# Assemble the final page code 
final_code = header + "\n\ndef render(navigate_to=None):\n" + body_indented

with open(dest, "w", encoding="utf-8") as f:
    f.write(final_code)

print("Ported successfully.")
