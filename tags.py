#!/usr/bin/env python3
import json
import re
from grim_dawn_data import TAGS_FILE, auto_extract_archive
from grim_dawn_data.json_utils import dump_json

TAGS_DIR = auto_extract_archive('tags')

def convert_format_string(s: str) -> str:
    s = re.sub(r'\{\^[EH]\}', '', s)
    s = re.sub(r'\{[^{}]+\}', '{}', s)
    s = re.sub(r'\{(?=[^}])', '', s)
    return s

if __name__ == '__main__':
    tags = {}
    tagline = re.compile(r'([a-zA-Z0-9_]+)=(.+)')
    count_total = 0
    count_ignored = 0

    for tagfile in sorted(TAGS_DIR.glob("*/text_en/*.txt")):
        with open(tagfile, 'r') as fp:
            for line in fp:
                m = tagline.fullmatch(line.strip())
                if m:
                    tag = m.group(1)
                    string = m.group(2)
                    if string == '?' or string == "":
                        count_ignored += 1
                        continue
                    count_total += 1
                    tags[tag] = convert_format_string(string)

    count_unqiue = len(tags)
    TAGS_FILE.parent.mkdir(exist_ok=True)
    dump_json(tags, TAGS_FILE)
    print(f"Extracted tags: {count_unqiue} unique + {count_ignored} ignored + {count_total - count_unqiue - count_ignored} duplicate / {count_total} total")
    print("wrote", TAGS_FILE.resolve())
