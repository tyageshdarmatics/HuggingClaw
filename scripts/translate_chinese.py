import os
import re
import time
import sys
from deep_translator import GoogleTranslator

sys.stdout.reconfigure(encoding='utf-8')

# Inclusive pattern for Chinese characters and typical fullwidth/CJK punctuation marks
ZH_PATTERN = re.compile(r'[\u4e00-\u9fa5\uf900-\ufa2d\u3000-\u303F\uFF00-\uFFEF]+')

def is_text_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext in ['.png', '.jpg', '.jpeg', '.gif', '.mp4', '.sqlite', '.sqlite3', '.db', '.pyc', '.zip', '.tar', '.gz', '.pdf', '.woff', '.woff2', '.ttf']:
        return False
    # Skip virtual environments or cache folders to speed things up
    path_parts = filepath.split(os.sep)
    if '.git' in path_parts or '.cache' in path_parts or '__pycache__' in path_parts or 'node_modules' in path_parts or 'env' in path_parts or 'venv' in path_parts:
        return False
    return True

def translate_match(match, translator):
    text = match.group(0)
    try:
        translated = translator.translate(text)
        print(f"Translated: {text} -> {translated}")
        time.sleep(0.05) 
        return translated if translated else text
    except Exception as e:
        print(f"Translation failed for '{text}': {e}")
        time.sleep(1) # sleep more on error
        return text

def process_file(filepath, translator):
    if not is_text_file(filepath):
        return

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return 

    if not ZH_PATTERN.search(content):
        return

    print(f"==> Processing: {filepath}")
    
    new_lines = []
    lines = content.split('\n')
    for line in lines:
        if ZH_PATTERN.search(line):
            # Using inline lambda so we can pass the translator instance
            new_line = ZH_PATTERN.sub(lambda m: translate_match(m, translator), line)
            new_lines.append(new_line)
        else:
            new_lines.append(line)
            
    try:
        # Preserve original line endings using split and then joining with newline
        # If the file had CRLF, reading in universal newline mode converts it to \n.
        # We will write out with python's default newlines
        pass
    except Exception as e:
        pass
        
    new_content = '\n'.join(new_lines)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
    except Exception as e:
        print(f"Failed to write to {filepath}: {e}")

if __name__ == '__main__':
    rootDir = r"c:\Users\pc\OneDrive\Desktop\openclaw-hf-space\HuggingClaw-main"
    translator = GoogleTranslator(source='zh-CN', target='en')
    for dirName, subdirList, fileList in os.walk(rootDir):
        for fname in fileList:
            filepath = os.path.join(dirName, fname)
            process_file(filepath, translator)
    print("All translations completed!")
