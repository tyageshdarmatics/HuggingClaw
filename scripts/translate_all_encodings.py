import os
import re
import time
import sys
from deep_translator import GoogleTranslator

sys.stdout.reconfigure(encoding='utf-8')

ZH_PATTERN = re.compile(r'[\u4e00-\u9fa5\uf900-\ufa2d\u3000-\u303F\uFF00-\uFFEF\u3040-\u309F\u30A0-\u30FF]+')

def is_binary(filepath):
    if filepath.endswith(('.png','.jpg','.jpeg','.gif','.mp4','.sqlite','.sqlite3','.db','.pyc','.zip','.tar','.gz','.pdf','.woff','.woff2','.ttf', '.ico', '.svg', '.webp')):
        return True
    path_parts = filepath.split(os.sep)
    if '.git' in path_parts or 'node_modules' in path_parts or '__pycache__' in path_parts:
        return True
    if filepath.endswith(('translate_chinese.py', 'check_encodings.py', 'fix_final.py', 'translate_ja.py', 'translate_all_encodings.py')):
        return True
    return False

def translate_match(match, translator):
    text = match.group(0)
    try:
        translated = translator.translate(text)
        print(f"Translated: {text} -> {translated}")
        time.sleep(0.05)
        return translated if translated else text
    except Exception as e:
        print(f"Failed to translate {text}: {e}")
        time.sleep(1)
        return text

def process_file(filepath, translator):
    if is_binary(filepath):
        return

    try:
        with open(filepath, 'rb') as f:
            raw = f.read()
    except Exception:
        return

    target_enc = None
    target_text = None

    try:
        text = raw.decode('utf-8')
        target_enc = 'utf-8'
        target_text = text
    except UnicodeDecodeError:
        for enc in ['gbk', 'utf-16', 'utf-16le']:
            try:
                text = raw.decode(enc)
                target_enc = enc
                target_text = text
                break
            except UnicodeDecodeError:
                pass

    if target_enc and target_text and ZH_PATTERN.search(target_text):
        print(f"Processing [{target_enc}] {filepath}")
        new_lines = []
        for line in target_text.split('\n'):
            if ZH_PATTERN.search(line):
                new_line = ZH_PATTERN.sub(lambda m: translate_match(m, translator), line)
                new_lines.append(new_line)
            else:
                new_lines.append(line)
        
        new_content = '\n'.join(new_lines)
        try:
            with open(filepath, 'w', encoding=target_enc) as f:
                f.write(new_content)
        except Exception as e:
            print(f"Failed to write {filepath}: {e}")

if __name__ == '__main__':
    rootDir = r"c:\Users\pc\OneDrive\Desktop\openclaw-hf-space\HuggingClaw-main"
    translator = GoogleTranslator(source='auto', target='en')
    for dirName, subdirList, fileList in os.walk(rootDir):
        for fname in fileList:
            filepath = os.path.join(dirName, fname)
            process_file(filepath, translator)
    print("All additional encodings translated!")
