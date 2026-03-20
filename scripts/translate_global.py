import os
import re
import time
import sys
from deep_translator import GoogleTranslator

sys.stdout.reconfigure(encoding='utf-8')

ZH_PATTERN = re.compile(r'[\u4e00-\u9fa5\uf900-\ufa2d\u3000-\u303F\uFF00-\uFFEF\u3040-\u309F\u30A0-\u30FF]+')

replacements = {
    '/* Star The status four button (excluding decoration) uses pixel elf skin */': '/* Star State four buttons (excluding decoration) use pixel sprite skin */',
    'Write your style theme (keep strictly the original room structure and only change the visual style)': 'Write your style theme (strictly maintain the original room structure, only change the visual style)',
    'For example: pixel style cyber Tokyo night scene, neon lights, ground reflections on rainy nights, blue and purple main colors': 'For example: pixel style cyber Tokyo night view, neon lights, rainy night ground reflections, blue-purple main color',
    'Default password:1234(You can ask me to change it for you at any time. It is recommended to change it to a strong password)': 'Default password:1234 (You can ask me to change it at any time, it is recommended to change to a strong password)',
    'Visibility: Click the eye button on the right side of the entry to toggle the display of the asset': 'Visibility: Click the eye button on the right side of the item to toggle the visibility of the asset',
    "👁 hide sidebar": "👁 Hide Sidebar",
    "👁 sidebarexpress": "👁 Show Sidebar",
    "Restore default": "Reset to Default",
    "forwardofversionReturn to": "Restore Previous Version",
    "📦 leadWowcrossdeath": "📦 Move",
    "🐚 return to home": "🐚 Return Home",
    "↩️ oneforwardfart": "↩️ One Step Forward",
    "⭐ thisHomeofsave": "⭐ Save This Home",
    "🤝 intermediary": "🤝 Broker",
    "🪚 self-dividedindecoration": "🪚 DIY Decoration",
    "intermediarytoappointlet": "Appoint Broker",
    "🏠 savedidHome": "🏠 Saved Homes",
    "stillsaveThere is no. Firstto "⭐ thisHomeofsave\"ofchargeplease.": "No saves yet. Please save this home first.",
    "nowon the map ofApplicable": "Apply to Current Map",
    "✅ nowmap ofsaveI did": "✅ Current Map Saved",
    "✅ savedidHomeofApplicableI did": "✅ Saved Home Applied",
    "Asset inspectionSO(desk / sofa / star)": "Search Asset (desk / sofa / star)",
    "recognizeAlready loaded": "Loaded",
    "Completeassets": "All Assets",
    "HuggingClaw ofHomeofrecognizeInclusionmiddle...": "Loading HuggingClaw Home...",
    "non-expression": "Hidden",
    "assetsrecognizeInclusion": "Asset Loading",
    "sceneobtain": "Scene Capture",
    "assetsrecognizeInclusionFail. renewdoTry againplease": "Asset Loading Failed. Please Wait and Try Again.",
    "stateDetailIdle: 'standby', stateDetailWriting: 'Document sorting', stateDetailResearching: 'intelligence search', stateDetailExecuting: 'task execution', stateDetailSyncing: 'same periodbackup', stateDetailError: 'Error occurred',": "stateDetailIdle: 'standby', stateDetailWriting: 'Document sorting', stateDetailResearching: 'intelligence search', stateDetailExecuting: 'task execution', stateDetailSyncing: 'same period backup', stateDetailError: 'error occurred',",
    "stateLabelIdle: 'standby', stateLabelWriting: 'Document sorting', stateLabelResearching: 'intelligence search', stateLabelExecuting: 'task execution', stateLabelSyncing: 'same periodbackup', stateLabelError: 'Error occurred',": "stateLabelIdle: 'standby', stateLabelWriting: 'Document sorting', stateLabelResearching: 'intelligence search', stateLabelExecuting: 'task execution', stateLabelSyncing: 'same period backup', stateLabelError: 'error occurred',",
    "Immediately redraw the asset sidebar after language switching to ensure that easy-to-understand names are updated simultaneously.": "Immediately redraw the asset sidebar after language switch to ensure friendly names are synced.",
    "After language switching, the guidance copy of the selected assets will be refreshed synchronously (trilingual linkage of small characters in the upload area)": "Synchronously refresh the instruction text of selected assets after language switch.",
    "Keep on desktop FIT；for mobile phone use RESIZE, and do it by height in the camera fit(Can be landscaped pan)": "Keep on desktop FIT; for mobile phone use RESIZE, and fit by height in camera (horizontal panning supported)",
    "During the same period: todayto the cloudseal.": "Sync: Seal today in cloud.",
    "The backup isceremonyNotPeace of mind.": "Backup is Peace of mind, not ceremony.",
    "BookInclusionmiddle…power supplyoffCaptivity.": "Writing in progress... Do not turn off power.",
    "Changeto timestamp.": "Save changes to timestamp.",
    "cloudEntire column:Click.": "Cloud synchronized.",
    "The same period is overtotouchDon't do it.": "Do not touch until sync completes.",
    "futureofself-dividedofDisasterfromsavecormorant.": "Save future self from disaster.",
    "backuponeTwo, regret oneTworeduceRu.": "One backup reduces one regret.",
    "Alert:firstfallChiWithStay.": "Alert: Stay calm.",
    "Bug's mindmatchoffeelJiru.": "Feel the presence of bugs.",
    "ReappearAfter thatCorrectionfart.": "Reproduce then correct.",
    "Please give me the log, human languageI'll make it.": "Give me logs, I will parse to human language.",
    "The error isenemynothandGakari.": "Errors are clues, not enemies.",
    "firstInfluence rangeoftrappedcormorant.": "Find the blast radius first.",
    "Stop bleedingAfter thatOperation.": "Stop bleeding before operation.",
    "nowImmediatelyroot causeofTracking.": "Tracking root cause now.",
    "A real man,commoncase.": "A common case.",
    "alertmode:problemofVisualizationdo.": "Alert Mode: Visualizing the problem.",
    "The protagonist's standby animation table. please keep 256×256 The frame division is consistent with the grid layout, otherwise the standby action will be framed incorrectly.": "The protagonist's standby animation table. please keep 256x256 framing layout consistent, otherwise standby animation will skip frames.",
    "Sofa shadow layer.It is recommended to stack it with the main body of the sofa at the same coordinates to enhance the feeling of being close to the ground.": "Sofa shadow layer. Suggest stacking at same coordinates as sofa body to enhance grounding.",
    "Notes panel base image.It is recommended to leave a text reading area and reduce high-frequency textures to avoid difficult-to-read information.": "Notes panel base image. Suggest leaving text reading area, lower high-frequency textures to avoid readability issues.",
    "mainHomeworksprite sheet(deskstatus).300×300 segmentationofmaintaindeath, center of gravity positionPlease prepare the.": "Main Homework sprite sheet (desk status). maintain 300x300 segmentation, align center of gravity.",
    "coffee machinefilmlayer. Ontologyandframe・When the anchors are alignedsense of groundingbutoutMasu.": "Coffee machine film layer. Align ontology and frame/anchor to establish sense of grounding.",
    "Visitor is stillfallbackportrait 1.handle guest_anim If you align the design withWhen switchingtonatureis.": "Visitor fallback portrait 1. Align design with guest_anim so it looks natural when switching.",
    "Visitor is stillfallbackportrait 2.handle guest_anim If you align the design withWhen switchingtonatureis.": "Visitor fallback portrait 2. Align design with guest_anim so it looks natural when switching.",
    "Visitor is stillfallbackportrait 3.handle guest_anim If you align the design withWhen switchingtonatureis.": "Visitor fallback portrait 3. Align design with guest_anim so it looks natural when switching.",
    "Visitor is stillfallbackportrait 4.handle guest_anim If you align the design withWhen switchingtonatureis.": "Visitor fallback portrait 4. Align design with guest_anim so it looks natural when switching.",
    "Visitor is stillfallbackportrait 5.handle guest_anim If you align the design withWhen switchingtonatureis.": "Visitor fallback portrait 5. Align design with guest_anim so it looks natural when switching.",
    "Visitor is stillfallbackportrait 6.handle guest_anim If you align the design withWhen switchingtonatureis.": "Visitor fallback portrait 6. Align design with guest_anim so it looks natural when switching.",
    "\"goodIt may become difficult\"newNewBUYAofrecognizeI'm absorbed in……": "Loading new area you might be interested in...",
    "⚠️ Returning to your hometown will overwrite the current customized room background (available from bg-history Restoring historical graphs).\\nAre you sure you want to continue?": "⚠️ Returning home will overwrite current custom background (can be restored from bg-history).\nAre you sure you want to continue?",
    "✅ The initial basemap has been restored (partial refresh failed, the page can be refreshed manually)": "✅ Restored base image (Partial refresh failed, please manually refresh)",
    "⚠️ This will return to the most recently generated room background. Are you sure you want to continue?": "⚠️ Will rollback to latest generated room background, continue?",
    "✅ Returned to the last background (partial refresh failed, the page can be refreshed manually)": "✅ Rolled back to previous background (Partial refresh failed, please manually refresh)",
    "// Use dynamic pixel characters uniformly to avoid relying on deleted demo static image": "// Use dynamic pixel character to avoid depending on deleted demo static image",
    "Error occurred!Go to alert area.": "Error Occurred! Please go to alert area.",
}

def is_binary(filepath):
    if filepath.endswith(('.png','.jpg','.jpeg','.gif','.mp4','.sqlite','.sqlite3','.db','.pyc','.zip','.tar','.gz','.pdf','.woff','.woff2','.ttf', '.ico', '.svg', '.webp')):
        return True
    path_parts = filepath.split(os.sep)
    if '.git' in path_parts or 'node_modules' in path_parts or '__pycache__' in path_parts or 'RestoreTmp' in path_parts:
        return True
    if filepath.endswith(('translate_chinese.py', 'check_encodings.py', 'fix_final.py', 'translate_ja.py', 'translate_all_encodings.py', 'translate_global.py')):
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
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return # Skip non-utf8 files
        
    original = content
        
    for k, v in replacements.items():
        if k in content:
            content = content.replace(k, v)

    if ZH_PATTERN.search(content):
        print(f"Translating regex matches in {filepath}")
        new_lines = []
        for line in content.split('\n'):
            if ZH_PATTERN.search(line):
                new_lines.append(ZH_PATTERN.sub(lambda m: translate_match(m, translator), line))
            else:
                new_lines.append(line)
        content = '\n'.join(new_lines)
    
    if content != original:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                print(f"Saved {filepath}")
        except Exception as e:
            print(f"Failed to write {filepath}: {e}")

if __name__ == '__main__':
    rootDir = r"c:\Users\pc\OneDrive\Desktop\openclaw-hf-space"
    translator = GoogleTranslator(source='auto', target='en')
    for dirName, subdirList, fileList in os.walk(rootDir):
        for fname in fileList:
            filepath = os.path.join(dirName, fname)
            process_file(filepath, translator)
    print("All global translations completed!")
