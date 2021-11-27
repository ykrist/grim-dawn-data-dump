import json
import re
import math
from pathlib import Path
from typing import *
import subprocess

CONSTELLATIONS_PATH = Path("ui/skills/devotion/constellations")


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

def load_dbr_file(p: Path) -> dict:
    key_vals = {}
    with open(p, 'r') as fp:
        for line in fp:
            line = line.strip().split(',')
            assert len(line) == 3
            assert line[-1] == ""
            assert line[0] not in key_vals
            key_vals[line[0]] = line[1]
    print("load", p)
    return key_vals


def parse_int_with_float(s: str) -> int:
    v = float(s)
    n = round(v)
    assert math.isclose(v, n, abs_tol=.000001)
    return n

def _get_weapon_reqs(data: dict) -> list:
    return [t for t in WEAPON_TYPES if bool(int(data.get(t, 0)))]

def _get_passive_bonuses(data: dict) -> dict:
    prefixes = [
        "retaliation",
        "offensive",
        "defensive",
        "character",
        "skill",
    ]
    ignore = {
        "characterBaseAttackSpeedTag",
        "skillDisplayName",
        "skillDownBitmapName",
        "skillUpBitmapName",
        'skillBaseDescription',
    }

    bonuses = {}

    for key, val in data.items():
        if key in ignore:
            continue

        if any(key.startswith(p) for p in prefixes):
            v = float(val)
            if v > 0:
                assert key not in val
                bonuses[key] = v

    return bonuses

class BadActiveSkillFile(Exception):
    pass

def parse_active_skill_file(p: Path) -> dict:
    data = load_dbr_file(p)
    if "FileDescription" in data:
        output = { "celestial_power": data['FileDescription']}
    else:
        raise BadActiveSkillFile

    weapon_req = _get_weapon_reqs(data)
    if weapon_req:
        output['weapon_requirement'] = weapon_req
    return output


def parse_petbonus_skill_file(p: Path) -> dict:
    data = load_dbr_file(p)
    return _get_passive_bonuses(data)

def parse_passive_skill_file(p: Path) -> dict:
    data = load_dbr_file(p)
    assert data['Class'] == "Skill_Passive"
    output = {
        "constellation": data['FileDescription'],
        "bonuses": _get_passive_bonuses(data),
    }
    weapon_req = _get_weapon_reqs(data)
    if weapon_req:
        output['weapon_requirement'] = weapon_req
    return output

def parse_constellation_file(p: Path) -> dict:
    affinity_bonus = {}
    affinity_req = {}

    data = load_dbr_file(p)
    for (key_base, dst) in [("affinityRequired", affinity_req), ("affinityGiven", affinity_bonus)]:
        for i in range(1, 9999999):
            valkey = f"{key_base}{i}"
            namekey = f"{key_base}Name{i}"
            if namekey in data:
                a = data[namekey].lower()
                v = parse_int_with_float(data[valkey])
                assert a not in dst
                dst[a] = v
            else:
                break

    pred = {}
    skills = {}
    for key, val in data.items():
        if key.startswith("devotionButton"):
            idx = int(key.replace("devotionButton", "")) - 1
            assert idx not in skills
            skills[idx] = Path(val).stem

        elif key.startswith("devotionLinks"):
            dest = int(key.replace("devotionLinks", "")) - 1
            src = int(val) - 1
            assert dest not in pred
            pred[dest] = src

    output = {
        "pred" : pred,
        "skills": skills,
        "affinity_bonus": affinity_bonus,
        "affinity_required": affinity_req,
    }

    return output

def process_constellation(base_path: Path, p: Path) -> Optional[Dict[str, Any]]:
    c = parse_constellation_file(p)
    c_name = None
    if len(c['skills']) == 0:
        return None
    for s, filename in c['skills'].items():
        skill = process_skill(base_path, filename)
        try:
            n = skill.pop("constellation")
            if c_name is None:
                c_name = n
            else:
                assert c_name == n
        except KeyError:
            pass

        c['skills'][s] = skill

    assert c_name is not None
    c['name'] = c_name

    return c

def process_skill(base_path: Path, skill_id: str) -> Dict[str, Any]:
    get_path = lambda s : base_path / "skills/devotion" / (s + ".dbr")
    p = get_path(skill_id)
    if p.exists():
        data = parse_passive_skill_file(p)
        p = get_path(skill_id + '_petbonus')
        if p.exists():
            data['pet_bonuses'] = parse_petbonus_skill_file(p)
        return data

    try:
        return parse_active_skill_file(get_path(skill_id + "_skill"))
    except BadActiveSkillFile:
        pass

    return parse_active_skill_file(get_path(skill_id + "_skill_buff"))

def parse_constellations_from_db(base_path: Path) -> List[Dict[str, Any]]:
    constellation_files = [
        p for p in (base_path / "ui/skills/devotion/constellations/").glob('*.dbr')
        if "background" not in p.stem
    ]

    constellations = [
        process_constellation(base_path, p) for p in constellation_files
    ]

    constellations = [c for c in constellations if c is not None]
    return constellations

if __name__ == '__main__':
    raw_dir = Path("raw")
    if not raw_dir.exists():
        print("extracting")
        subprocess.run(("tar", "-Jxvf", "raw.tar.xz"))

    constellations = set()
    full_list = []

    for src in Path("raw").glob("*"):
        src = src / "records"
        data = parse_constellations_from_db(src)
        for c in data:
            n = c['name']
            assert n not in constellations or n == 'Crossroads'
            constellations.add(n)
        full_list.extend(data)

    with open('constellations-extracted.json', 'w') as fp:
        json.dump(full_list, fp, indent='  ')
