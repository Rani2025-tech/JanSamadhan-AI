import os
import json
import sys

# Ensure repository root is in sys.path
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, repo_root)
sys.path.insert(0, os.path.join(repo_root, "frontend"))

import ui_text
from backend.core import messages

def migrate():
    locales_dir = os.path.join(repo_root, "locales")
    os.makedirs(locales_dir, exist_ok=True)

    dept_file = os.path.join(repo_root, "data", "departments.json")
    with open(dept_file, "r", encoding="utf-8") as f:
        dept_data = json.load(f)

    categories_list = [d["category"] for d in dept_data]
    departments_list = [d["department"] for d in dept_data]
    statuses_list = ["Submitted", "Assigned", "In Progress", "Resolved", "Reopened"]
    priorities_list = ["Low", "Medium", "High", "Critical"]

    orig_ui = ui_text.UI_TEXT
    orig_bot = messages.MESSAGES

    # Report original counts
    print(f"Original UI_TEXT key count: {len(orig_ui)}")
    print(f"Original MESSAGES key count: {len(orig_bot)}")

    for lang in ["en", "hi", "or"]:
        ui_count = sum(1 for k in orig_ui if lang in orig_ui[k])
        bot_count = sum(1 for k in orig_bot if lang in orig_bot[k])
        print(f"Original keys for {lang} -> UI: {ui_count}, Bot: {bot_count}")

    # Build en.json labels
    en_labels = {
        "categories": {cat: cat for cat in categories_list},
        "departments": {dept: dept for dept in departments_list},
        "statuses": {stat: stat for stat in statuses_list},
        "priorities": {pri: pri for pri in priorities_list}
    }

    # Status/priority mapping helper from old keys
    status_key_map = {
        "Submitted": "status_submitted",
        "Assigned": "status_assigned",
        "In Progress": "status_in_progress",
        "Resolved": "status_resolved",
        "Reopened": "status_reopened"
    }
    priority_key_map = {
        "Low": "priority_low",
        "Medium": "priority_medium",
        "High": "priority_high",
        "Critical": "priority_critical"
    }

    def extract_labels(lang_code):
        if lang_code == "en":
            return en_labels
        
        # hi and or labels
        stat_dict = {}
        for s_name, s_key in status_key_map.items():
            if s_key in orig_ui and lang_code in orig_ui[s_key]:
                stat_dict[s_name] = orig_ui[s_key][lang_code]
            elif s_key in orig_bot and lang_code in orig_bot[s_key]:
                stat_dict[s_name] = orig_bot[s_key][lang_code]

        pri_dict = {}
        for p_name, p_key in priority_key_map.items():
            if p_key in orig_ui and lang_code in orig_ui[p_key]:
                pri_dict[p_name] = orig_ui[p_key][lang_code]
            elif p_key in orig_bot and lang_code in orig_bot[p_key]:
                pri_dict[p_name] = orig_bot[p_key][lang_code]

        return {
            "categories": {},
            "departments": {},
            "statuses": stat_dict,
            "priorities": pri_dict
        }

    english_note_map = {
        "en": "(English)",
        "hi": "(अंग्रेज़ी)",
        "or": "(ଇଂରାଜୀ)"
    }

    # 1. Create en.json, hi.json, or.json
    migrated_counts = {}
    for lang in ["en", "hi", "or"]:
        ui_dict = {k: orig_ui[k][lang] for k in orig_ui if lang in orig_ui[k]}
        # Ensure english_note is present
        if "english_note" not in ui_dict:
            ui_dict["english_note"] = english_note_map[lang]
        
        bot_dict = {k: orig_bot[k][lang] for k in orig_bot if lang in orig_bot[k]}
        labels_dict = extract_labels(lang)

        doc = {
            "_note": "needs review by a fluent speaker",
            "ui": ui_dict,
            "bot": bot_dict,
            "labels": labels_dict
        }

        out_path = os.path.join(locales_dir, f"{lang}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)

        migrated_counts[lang] = {
            "ui": len(ui_dict),
            "bot": len(bot_dict)
        }
        print(f"Migrated {lang}.json -> UI: {len(ui_dict)}, Bot: {len(bot_dict)}")

    # 2. Create mr.json, ta.json, bn.json with empty sections
    for lang in ["mr", "ta", "bn"]:
        doc = {
            "_note": "needs review by a fluent speaker",
            "ui": {},
            "bot": {},
            "labels": {
                "categories": {},
                "departments": {},
                "statuses": {},
                "priorities": {}
            }
        }
        out_path = os.path.join(locales_dir, f"{lang}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
        print(f"Created empty stub {lang}.json")

    return migrated_counts

if __name__ == "__main__":
    migrate()

