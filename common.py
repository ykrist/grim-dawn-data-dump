from pathlib import Path
import subprocess
from functools import lru_cache

TAGS_FILE = Path("data/tags.json")
CONSTELLATION_FILE = Path("data/constellations.json")
BONUSES_FILE = Path("data/constellation-bonuses.json")

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
