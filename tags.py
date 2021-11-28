import json
import re
from common import *

TAGS_DIR = auto_extract_archive('tags')

class TagLookup:
    def __init__(self):
        self.tags = TagLookup.load_tags()

    @staticmethod
    @cache
    def load_tags():
        with open(TAGS_FILE, 'r') as fp:
            return json.load(fp)

    def resolve(self, tag: str) -> str:
        s = self.tags[tag]
        s = re.sub(r'\{\^[EH]\}', '', s)
        s = re.sub(r'\{[^{}]+\}', '{}', s)
        s = re.sub(r'\{(?=[^}])', '', s)
        return s

if __name__ == '__main__':
    tags = {}
    tagline = re.compile(r'([a-zA-Z0-9_]+)=(.+)')
    for tagfile in sorted(TAGS_DIR.glob("*/text_en/*.txt")):
        with open(tagfile, 'r') as fp:
            for line in fp:
                m = tagline.fullmatch(line.strip())
                if m:
                    tag = m.group(1)
                    string = m.group(2)
                    if string == '?' or string == "":
                        continue
                    tags[tag] = string


    TAGS_FILE.parent.mkdir(exist_ok=True)

    with open(TAGS_FILE, 'w') as fp:
        json.dump(tags, fp, indent='  ')

