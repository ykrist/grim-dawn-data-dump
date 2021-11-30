from pathlib import Path
import subprocess
from functools import lru_cache
from .json_utils import load_json as _load_json

DATA_DIRECTORY = Path(__file__).parent.parent / "data"
TAGS_FILE = DATA_DIRECTORY / "tags.json"
CONSTELLATION_FILE = DATA_DIRECTORY / "constellations.json"
BONUSES_FILE = DATA_DIRECTORY / "constellation-bonuses.json"

STAT_IDS = {'Dexterity': 1, 'Strength': 2, 'Intelligence': 3, 'Life': 4, 'Mana': 5}


WEAPON_TYPES = {
    "Dagger": "Dagger, melee",
    "Axe": "One-handed, melee, axe",
    "Axe2h": "Two-handed, melee, axe",
    "Mace": "One-handed, Melee, mace",
    "Mace2h": "Two-handed, melee, mace",
    "Offhand": "Caster off-hand",
    "Ranged1h": "One-handed, ranged",
    "Ranged2h": "Two-handed, ranged",
    "Shield": "Shield",
    "Spear": "Two-handed, melee",
    "Staff": "Scepter",
    "Sword": "One-handed, sword, melee",
    "Sword2h": "Two-handed, sword, melee",
}

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



COUNTS_AS = {
    'Damage.Elemental': [
        ('Damage.Fire', 1/3),
        ('Damage.Cold', 1/3),
        ('Damage.Lightning', 1/3),
    ],
    'DamageModifier.Elemental': [
        ('DamageModifier.Fire', 1),
        ('DamageModifier.Cold', 1),
        ('DamageModifier.Lightning', 1),
    ],
    'offensiveTotalDamageModifier': [
        ('DamageModifier.Fire', 1),
        ('DamageModifier.Cold', 1),
        ('DamageModifier.Lightning', 1),
        ('DamageModifier.Aether', 1),
        ('DamageModifier.Chaos', 1),
        ('DamageModifier.Life', 1),
        ('DamageModifier.Physical', 1),
        ('DamageModifier.Pierce', 1),
        ('DamageModifier.Poison', 1),
    ],
    'retaliationTotalDamageModifier': [
        ('Retaliation.Fire', 1),
        ('Retaliation.Cold', 1),
        ('Retaliation.Lightning', 1),
        ('Retaliation.Aether', 1),
        ('Retaliation.Chaos', 1),
        ('Retaliation.Life', 1),
        ('Retaliation.Physical', 1),
        ('Retaliation.Pierce', 1),
        ('Retaliation.Poison', 1),
    ],
    'defensiveAllMaxResist': [
        ("defensiveAetherMaxResist", 1),
        ("defensiveBleedingMaxResist", 1),
        ("defensiveChaosMaxResist", 1),
        ("defensiveColdMaxResist", 1),
        ("defensiveFireMaxResist", 1),
        ("defensiveLifeMaxResist", 1),
        ("defensiveLightningMaxResist", 1),
        ("defensivePierceMaxResist", 1),
        ("defensivePoisonMaxResist", 1),
    ],
    'characterTotalSpeedModifier': [
        ('characterSpellCastSpeedModifier', 1),
        ('characterRunSpeedModifier', 1),
        ('characterAttackSpeedModifier', 1)
    ],
    'defensiveElementalResistance' : [
        ('defensiveFire', 1),
        ('defensiveCold', 1),
        ('defensiveLightning', 1)
    ]
}

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
