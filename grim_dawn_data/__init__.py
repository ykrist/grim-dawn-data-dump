from pathlib import Path
import subprocess
from functools import lru_cache
from .json_utils import load_json as _load_json

DATA_DIRECTORY = Path(__file__).parent.parent / "data"
TAGS_FILE = DATA_DIRECTORY / "tags.json"
CONSTELLATION_FILE = DATA_DIRECTORY / "constellations.json"
BONUSES_FILE = DATA_DIRECTORY / "constellation-bonuses.json"

STAT_IDS = {'Dexterity': 1, 'Strength': 2, 'Intelligence': 3, 'Life': 4, 'Mana': 5}

WEAPON_TYPES = [
    "Axe",
    "Axe2h",
    "Mace",
    "Mace2h",
    "Magical",
    "Offhand",
    "Ranged1h",
    "Ranged2h",
    "Shield",
    "Spear",
    "Staff",
    "Sword",
    "Sword2h",
]

DAMAGE_TYPES = [
    "Lightning",
    "Life",
    "Cold",
    "Chaos",
    "Fire",
    "Aether",
    "Pierce",
    "Bleeding",
    "Poison",
    "Physical",
    "ManaLeach",
    "LifeLeech",
    "Elemental",
]


cache = lru_cache(maxsize=None)

def auto_extract_archive(path: str):
    p = Path(path)
    if not p.exists():
        subprocess.run(['tar', '-Jxvf', path + '.tar.xz'])
    return p


@cache
def load_tags():
    return _load_json(TAGS_FILE)

@cache
def load_constellation_bonuses():
    return _load_json(BONUSES_FILE)
