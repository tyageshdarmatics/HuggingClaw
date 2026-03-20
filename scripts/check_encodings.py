import os
import re

ZH = re.compile(r'[\u4e00-\u9fa5\uf900-\ufa2d\u3000-\u303F\uFF00-\uFFEF\u3040-\u30FF]+')

def check_file(filepath):
    # skip binary extensions and some directories
    if filepath.endswith(('.png','.jpg','.jpeg','.gif','.mp4','.sqlite','.sqlite3','.db','.pyc','.zip','.tar','.gz','.pdf','.woff','.woff2','.ttf', '.ico', '.svg')):
        return
    path_parts = filepath.split(os.sep)
    if '.git' in path_parts or 'node_modules' in path_parts or '__pycache__' in path_parts:
        return

    try:
        with open(filepath, 'rb') as f:
            raw = f.read()
            
        encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16', 'utf-16le']
        
        for enc in encodings:
            try:
                text = raw.decode(enc)
                if ZH.search(text):
                    print(f"[{enc}] {filepath}")
                    return # Found it!
            except UnicodeDecodeError:
                pass
    except Exception as e:
        pass

if __name__ == '__main__':
    for rt, dirs, fs in os.walk('.'):
        for f in fs:
            check_file(os.path.join(rt, f))
    print("Search complete.")
