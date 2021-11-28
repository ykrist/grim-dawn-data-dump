import json
from tags import TagLookup
import re
from typing import *
from common import *


def fmt(fstring, str=True, repr=True):
    def format_self(self):
        return self.__class__.__name__ + "(" + fstring.format_map(self.__dict__) + ")"


    def wrapper(cls):
        if str:
            cls.__str__ = format_self
        if repr:
            cls.__repr__ = format_self
        return cls
    return wrapper


def split_bonus_name(name: str):
    m = re.fullmatch('([a-z]+)([A-Z][a-z]+)+', name)
    assert m is not None
    first = m.group(1)
    split = (first, ) + tuple(re.findall("[A-Z][a-z]+", name))

    return split



class Bonus:
    JSON_TAGS = {}

    def __init_subclass__(cls, json, **kwargs):
        Bonus.JSON_TAGS[json] = cls
        cls.JSON_TAG = json

    def value(self) -> float:
        raise NotImplementedError

    def tag(self) -> str:
        raise NotImplementedError

    def display(self) -> str:
        tags = TagLookup()
        fstr = tags.resolve(self.tag())
        return fstr.format(self.value())


@fmt("{amount} {kind}")
class MiscBonus(Bonus, json="misc"):
    def __init__(self, amount: float, kind: str, tagname: str):
        self.amount = amount
        self.kind = kind
        self.tagname = tagname

    def value(self):
        return self.amount

    def tag(self) -> str:
        return self.tagname

@fmt("+{amount}% {kind}")
class DamageModifier(Bonus, json="dmg_mod"):
    def __init__(self, amount: float, kind: str):
        self.amount = amount
        self.kind = kind

    def value(self):
        return self.amount

    def tag(self) -> str:
        return f"DamageModifier{self.kind}"

class Damage(Bonus, json="dmg"):
    def __init__(self, min_val: float, kind: str, max_val=None):
        self.min_val = min_val
        self.max_val = max_val
        self.kind = kind

    def is_range(self) -> bool:
        return self.max_val is not None

    def value(self):
        if self.is_range():
            return 0.5 * (self.min_val + self.max_val)
        else:
            return self.min_val

    def display(self) -> str:
        tags = TagLookup()
        fstr = tags.resolve(self.tag())
        if self.is_range():
            v = f"{self.min_val}-{self.max_val}"
        else:
            v = f"{self.min_val}"
        return fstr.format(v)

    def tag(self):
        return f"Damage{self.kind}"

    def __repr__(self):
        if self.is_range():
            s = f"{self.min_val}-{self.max_val} {self.kind}"
        else:
            s = f"{self.min_val} {self.kind}"

        return f"{self.__class__.__name__}({s})"

class Retaliation(Damage, json="retaliation"):
    def tag(self):
        return f"Retaliation{self.kind}"

@fmt("-{amount}% * {duration}s {kind}")
class ResistanceReduction(Bonus, json="resistance_reduce"):
    def __init__(self, amount: float, duration: float, kind: str):
        self.amount = amount
        self.duration = duration
        self.kind = kind

    def value(self) -> float:
        return self.amount * self.duration

    def tag(self):
        return f"Damage{self.kind}ResistanceReductionPercent"

@fmt("{dps} * {duration}s {kind}")
class DamageOverTime(Bonus, json="dot"):
    def __init__(self, dps:  float, duration: float, kind: str):
        self.dps = dps
        self.duration = duration
        self.kind = kind

    def value(self) -> float:
        return self.dps * self.duration

    def tag(self) -> str:
        return f"DamageDuration{self.kind}"

class DamageOverTimeModifier(Bonus, json="dot_mod"):
    def __init__(self, damage: float, duration: float, kind: str):
        self.damage = damage
        self.duration = duration
        self.kind = kind

    def __repr__(self):
        if self.damage and self.duration > 0:
            s = f"+{self.damage}%, +{self.duration}% dur; {self.kind}"

        elif self.duration > 0:
            s =  f"+{self.duration}% dur; {self.kind}"

        else:
            s = f"+{self.damage}% {self.kind}"

        return f"{self.__class__.__name__}({s})"

    def value(self) -> float:
        return self.damage + self.duration

    def tag(self) -> str:
        return f"DamageDurationModifier{self.kind}"

@fmt("{prob}% {bonus}")
class ChanceOf(Bonus, json="chance"):
    def __init__(self, prob: float, bonus: Bonus):
        self.bonus = bonus
        self.prob = prob

    def value(self) -> float:
        return self.bonus.value() * self.prob / 100

    def tag(self):
        return "tagChanceOf"


@cache
def manual_tags() -> Dict:
    with open("manual_bonuses.txt", 'r') as fp:
        manual = {
            split_bonus_name(l[0]): l[1]
            for l in (l.strip().split('=') for l in fp)
        }
    return manual

STAT_IDS = {'Dexterity': 1, 'Strength': 2, 'Intelligence': 3, 'Life': 4, 'Mana': 5}

def get_tag_name(bonus: Tuple[str]) -> str:
    manual = manual_tags()
    tags = TagLookup.load_tags()

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
            blist.append(Damage(v_min, ty, max_val=v_max))

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

def interpret_bonuses(bonuses) -> List[Bonus]:
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

def load_all():
    def deserialize_json(obj):
        if "_type" in obj:
            try:
                cls = Bonus.JSON_TAGS[obj["_type"]]
            except KeyError:
                pass
            else:
                return cls(**obj['data'])

        return obj

    with open(BONUSES_FILE, 'r') as fp:
        return json.load(fp, object_hook=deserialize_json)

def serialize_json(obj):
    if isinstance(obj, Bonus):
        return {
            "_type": obj.JSON_TAG,
            "data": obj.__dict__
        }

    raise NotImplementedError

if __name__ == '__main__':
    with open(CONSTELLATION_FILE, 'r') as fp:
        data = json.load(fp)
    tags = TagLookup.load_tags()
    bonuses = set()
    not_handled = set()
    for c in data:
        for s in c['skills'].values():
            if "bonuses" in s:
                b = s['bonuses'].copy()
                blist, rem = interpret_bonuses(b)
                s['bonuses'] = blist

                for b in blist:
                    print(b.display())

                not_handled.update(rem)

    if not_handled:
        print("error, the following bonus attributes were not handled")
        contents = "\n".join("".join(s) for s in sorted(not_handled))
        with open("not_handled.txt", 'w') as fp:
            fp.write(contents)
        print(contents)

    with open(BONUSES_FILE, 'w') as fp:
        json.dump(data, fp, indent='  ', default=serialize_json)


