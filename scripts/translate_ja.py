import os
import re
import time
import sys
from deep_translator import GoogleTranslator

sys.stdout.reconfigure(encoding='utf-8')

# Include Japanese characters
ZH_PATTERN = re.compile(r'[\u4e00-\u9fa5\uf900-\ufa2d\u3000-\u303F\uFF00-\uFFEF\u3040-\u309F\u30A0-\u30FF]+')

def translate_match(match, translator):
    text = match.group(0)
    try:
        translated = translator.translate(text)
        time.sleep(0.1)
        return translated if translated else text
    except Exception:
        return text

filepath = r"c:\Users\pc\OneDrive\Desktop\openclaw-hf-space\HuggingClaw-main\frontend\electron-standalone.html"
translator = GoogleTranslator(source='auto', target='en')

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

new_lines = []
lines = content.split('\n')
for line in lines:
    if ZH_PATTERN.search(line):
        new_lines.append(ZH_PATTERN.sub(lambda m: translate_match(m, translator), line))
    else:
        new_lines.append(line)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))
print("Finished translating electron-standalone.html")
