#!/usr/bin/env python3
from grim_dawn_data import cache, DAMAGE_TYPES, BONUSES_FILE, CONSTELLATION_FILE, STAT_IDS, load_tags
from grim_dawn_data.bonuses import *
from grim_dawn_data.json_utils import dump_json, load_json
from typing import *
import re

def split_bonus_name(name: str):
    m = re.fullmatch('([a-z]+)([A-Z][a-z]+)+', name)
    assert m is not None
    first = m.group(1)
    split = (first, ) + tuple(re.findall("[A-Z][a-z]+", name))

    return split

@cache
def manual_bonuses() -> Dict:
    with open("manual_bonuses.txt", 'r') as fp:
        manual = {
            split_bonus_name(l[0]): l[1]
            for l in (l.strip().split('=') for l in fp)
        }
    return manual


def get_tag_name(bonus: Tuple[str]) -> str:
    manual = manual_bonuses()
    tags = load_tags()

    if bonus in manual:
        tag = manual[bonus]
        assert tag in tags
        return tag

    if bonus[0] == 'character':
        if bonus[1] in STAT_IDS and (len(bonus) < 3 or bonus[2] != "Regen"):
            tag = f"tagCharAttribute0{STAT_IDS[bonus[1]]}" + "".join(bonus[2:])
        else:
            tag = 'tagChar' + "".join(bonus[1:])

    elif bonus[0] == "defensive":
        if bonus[1] == "Slow" and bonus[3] == "Leach":
            tag = "Defense" + "".join(bonus[2:])
        else:

            tag = "Defense" + "".join(bonus[1:])

    else:
        tag = "".join((bonus[0].capitalize(),) + bonus[1:] )

    if tag in tags:
        return tag

    tag = tag + "s"
    if tag in tags:
        return tag

    return None


def get_flat_damage(bonuses: dict) -> List[Bonus]:
    blist = []
    for ty in DAMAGE_TYPES:
        k_amount = split_bonus_name("offensive" + ty + "Modifier")
        k_chance = split_bonus_name("offensive" + ty + "ModifierChance")

        if k_amount in bonuses:
            amount = bonuses.pop(k_amount)
            b = DamageModifier(amount, ty)
            if k_chance in bonuses:
                p = bonuses.pop(k_chance)
                b = ChanceOf(p, b)
            blist.append(b)

        k_max = split_bonus_name("offensive" + ty + "Max")
        k_min = split_bonus_name("offensive" + ty + "Min")

        if k_max in bonuses:
            v_max = bonuses.pop(k_max)
            v_min = bonuses.pop(k_min)
        elif k_min in bonuses:
            v_max = None
            v_min = bonuses.pop(k_min)
        else:
            v_min = None
            v_max = None

        if v_min is not None:
            blist.append(Damage(v_min, ty, max_val=v_max))

    return blist

def get_retaliation_damage(bonuses: dict) -> List[Bonus]:
    blist = []
    for ty in DAMAGE_TYPES:
        k_max = split_bonus_name("retaliation" + ty + "Max")
        k_min = split_bonus_name("retaliation" + ty + "Min")

        if k_max in bonuses:
            v_max = bonuses.pop(k_max)
            v_min = bonuses.pop(k_min)
        elif k_min in bonuses:
            v_max = None
            v_min = bonuses.pop(k_min)
        else:
            v_min = None
            v_max = None

        if v_min is not None:
            blist.append(Retaliation(v_min, ty, max_val=v_max))

    return blist

def get_resistance_reduction(bonuses: dict) -> List[Bonus]:
    blist = []
    for ty in DAMAGE_TYPES:
        k_duration = split_bonus_name("offensive" + ty + "ResistanceReductionPercentDurationMin")
        k_amt = split_bonus_name("offensive" + ty + "ResistanceReductionPercentMin")

        if k_amt in bonuses or k_duration in bonuses:
            a = bonuses.pop(k_amt)
            d = bonuses.pop(k_duration)

            blist.append(ResistanceReduction(a, d, ty))

    return blist


def get_damage_over_time(bonuses: dict) -> List[Bonus]:
    blist = []
    for ty in DAMAGE_TYPES:
        k_amount = split_bonus_name("offensiveSlow" + ty + "Min")
        k_duration = split_bonus_name("offensiveSlow" + ty + "DurationMin")
        k_chance = split_bonus_name("offensiveSlow" + ty + "Chance")

        if k_amount in bonuses:
            amount = bonuses.pop(k_amount)
            duration = bonuses.pop(k_duration)
            b = DamageOverTime(amount, duration, ty)
            if k_chance in bonuses:
                p = bonuses.pop(k_chance)
                b = ChanceOf(p, b)
            blist.append(b)

        k_amt_mod = split_bonus_name("offensiveSlow" +  ty + "Modifier")
        k_dur_mod = split_bonus_name("offensiveSlow" +  ty + "DurationModifier")

        if k_amt_mod in bonuses or k_dur_mod in bonuses:
            try:
                amt = bonuses.pop(k_amt_mod)
            except KeyError:
                amt = 0.

            try:
                dur = bonuses.pop(k_dur_mod)
            except KeyError:
                dur = 0.

            blist.append(DamageOverTimeModifier(amt, dur, ty))


    return blist

def interpret_bonuses(bonuses) -> Tuple[List[Bonus], Dict]:
    bonuses = {split_bonus_name(b): v for b, v in bonuses.items()}

    blist = []

    blist.extend(get_damage_over_time(bonuses))
    blist.extend(get_flat_damage(bonuses))
    blist.extend(get_retaliation_damage(bonuses))
    blist.extend(get_resistance_reduction(bonuses))

    for b in list(bonuses):
        tag = get_tag_name(b)
        if tag is not None:
            val = bonuses.pop(b)
            blist.append(MiscBonus(val, "".join(b), tag))

    return blist, bonuses


if __name__ == '__main__':
    data = load_json(CONSTELLATION_FILE)
    tags = load_tags()
    bonuses = set()
    not_handled = set()
    for c in data:
        for i, s in enumerate(c['skills'].values()):
            if 'bonuses' in s:
                blist, rem = interpret_bonuses(s['bonuses'])
                not_handled.update(rem)
            else:
                blist = []

            if 'pet_bonuses' in s:
                pet_blist, rem = interpret_bonuses(s.pop('pet_bonuses'))
                blist.extend(map(Pets, pet_blist))
                not_handled.update(rem)

            if blist:
                print(f"{c['name']} ({i})")
                for b in blist:
                    print(f"    {b.display():<60}  [{b.kind_id()}]")
                s['bonuses'] = blist

    if not_handled:
        print("error, the following bonus attributes were not handled")
        contents = "\n".join("".join(s) for s in sorted(not_handled))
        with open("not_handled.txt", 'w') as fp:
            fp.write(contents)
        print(contents)

    dump_json(data, BONUSES_FILE)
