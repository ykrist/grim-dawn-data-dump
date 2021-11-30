from . import load_tags
from typing import Iterable, List
from .json_utils import JsonSerializable
import copy


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

def _get_tag(t) -> str:
    return load_tags()[t]

class Bonus(JsonSerializable):
    def kind_id(self) -> str:
        raise NotImplementedError

    def display_fmt(self) -> str:
        raise NotImplementedError

    def display_args(self) -> tuple:
        raise NotImplementedError

    def display(self) -> str:
        return self.display_fmt().format(*self.display_args())

    def display_symbolic(self) -> str:
        k = len(self.display_args())
        return self.display_fmt().format(*('XYZ'[i] for i in range(k)))

    def is_aggregatable(self) -> bool:
        return False

@fmt("{amount} {kind}")
class MiscBonus(Bonus):
    def kind_id(self) -> str:
        return self.kind

    def __init__(self, amount: float, kind: str, tagname: str):
        self.amount = amount
        self.kind = kind
        self.tagname = tagname

    def display_fmt(self) -> str:
        return _get_tag(self.tagname)

    def display_args(self) -> tuple:
        return self.amount,


    def is_aggregatable(self) -> bool:
        return True

@fmt("+{amount}% {kind}")
class DamageModifier(Bonus):
    def kind_id(self) -> str:
        return f"{self.__class__.__name__}.{self.kind}"

    def __init__(self, amount: float, kind: str):
        self.amount = amount
        self.kind = kind

    def display_fmt(self) -> str:
        return _get_tag(f"DamageModifier{self.kind}")

    def display_args(self):
        return self.amount,

    def is_aggregatable(self) -> bool:
        return True

@fmt("{bonus}")
class Pets(Bonus):
    def __init__(self, bonus: Bonus):
        self.bonus = bonus

    def kind_id(self) -> str:
        return f"Pets.{self.bonus.kind_id()}"

    def display_fmt(self) -> str:
        return _get_tag('tagPetBonusNameAllPets') + ": " + self.bonus.display_fmt()

    def display_args(self) -> tuple:
        return self.bonus.display_args()

    def is_aggregatable(self) -> bool:
        return self.bonus.is_aggregatable()

class Damage(Bonus):
    def __init__(self, min_val: float, kind: str, max_val=None):
        self.min_val = min_val
        self.max_val = max_val
        self.kind = kind

    def kind_id(self) -> str:
        return f"{self.__class__.__name__}.{self.kind}"

    def is_range(self) -> bool:
        return self.max_val is not None

    def _initial_fmt(self):
        return _get_tag(f"Damage{self.kind}")

    def display_fmt(self):
        f = self._initial_fmt()
        if self.is_range():
            return f.format(_get_tag("DamageRangeFormat"))
        else:
            return f.format(_get_tag("DamageSingleFormat"))

    def display_args(self):
        if self.is_range():
            return (self.min_val, self.max_val)
        else:
            return self.min_val,

    def display_symbolic(self) -> str:
        f = _get_tag(f"Damage{self.kind}")
        return f.format(_get_tag("DamageRangeFormat")).format('X', 'Y')

    def __repr__(self):
        if self.is_range():
            s = f"{self.min_val}-{self.max_val} {self.kind}"
        else:
            s = f"{self.min_val} {self.kind}"

        return f"{self.__class__.__name__}({s})"

    def is_aggregatable(self) -> bool:
        return self.max_val is None

class Retaliation(Damage):
    def kind_id(self) -> str:
        return f"{self.__class__.__name__}.{self.kind}"

    def _initial_fmt(self) -> str:
        return _get_tag(f"Retaliation{self.kind}")



@fmt("-{amount}% * {duration}s {kind}")
class ResistanceReduction(Bonus):
    def __init__(self, amount: float, duration: float, kind: str):
        self.amount = amount
        self.duration = duration
        self.kind = kind

    def kind_id(self) -> str:
        return f"{self.__class__.__name__}.{self.kind}"

    def display_fmt(self):
        return _get_tag("DamageSingleFormat") +  _get_tag(f"Damage{self.kind}ResistanceReductionPercent") + _get_tag('DamageFixedSingleFormatTime')

    def display_args(self) -> tuple:
        return (self.amount, self.duration)

@fmt("{dps} * {duration}s {kind}")
class DamageOverTime(Bonus):
    def __init__(self, dps:  float, duration: float, kind: str):
        self.dps = dps
        self.duration = duration
        self.kind = kind

    def display_fmt(self):
        return _get_tag("DamageSingleFormat") + _get_tag(f"DamageDuration{self.kind}") + _get_tag("DamageSingleFormatTime")


    def display_args(self):
        return (self.dps * self.duration, self.duration)

    def kind_id(self) -> str:
        return f"{self.__class__.__name__}.{self.kind}"


class DamageOverTimeModifier(Bonus):
    def __init__(self, damage_mod: float, duration_mod: float, kind: str):
        self.damage_mod = damage_mod
        self.duration_mod = duration_mod
        self.kind = kind

    def _display_fmt_with_duration(self):
        return self._display_fmt_without_duration() + _get_tag("ImprovedTimeFormat")

    def _display_fmt_without_duration(self):
        return _get_tag(f"DamageDurationModifier{self.kind}")

    def display_fmt(self):
        if self.duration_mod == 0:
            return self._display_fmt_without_duration()
        else:
            return self._display_fmt_with_duration()

    def display_args(self):
        if self.duration_mod == 0:
            return self.damage_mod,
        else:
            return self.damage_mod, self.duration_mod

    def display_symbolic(self) -> str:
        return self._display_fmt_with_duration().format('X', 'Y')

    def kind_id(self) -> str:
        return f"{self.__class__.__name__}.{self.kind}"

    def __repr__(self):
        if self.damage_mod and self.duration_mod > 0:
            s = f"+{self.damage_mod}%, +{self.duration_mod}% dur; {self.kind}"

        elif self.duration_mod > 0:
            s =  f"+{self.duration_mod}% dur; {self.kind}"

        else:
            s = f"+{self.damage_mod}% {self.kind}"

        return f"{self.__class__.__name__}({s})"

    def is_aggregatable(self) -> bool:
        return True

@fmt("{prob}% {bonus}")
class ChanceOf(Bonus):
    def __init__(self, prob: float, bonus: Bonus):
        self.bonus = bonus
        self.prob = prob

    def kind_id(self) -> str:
        return f"{self.__class__.__name__}.{self.bonus.kind_id()}"

    def display_fmt(self):
        return _get_tag("tagChanceOf") + self.bonus.display_fmt()

    def display_args(self) -> tuple:
        return (self.prob, ) + self.bonus.display_args()


def aggregate_bonuses(bonuses: Iterable[Bonus]) -> List[Bonus]:
    aggregated = {}
    pets = []
    blist = []
    for b in bonuses:
        if isinstance(b, Pets):
            pets.append(b.bonus)
            continue

        if b.is_aggregatable():
            key = b.kind_id()
            if key not in aggregated:
                aggregated[key] = copy.copy(b)
            else:
                total = aggregated[key]
                if isinstance(b, (MiscBonus, DamageModifier)):
                    total.amount += b.amount
                elif isinstance(b, (Damage, Retaliation)):
                    total.min_val += b.min_val
                elif isinstance(b, DamageOverTimeModifier):
                    total.damage_mod += b.damage_mod
                    total.duration_mod += b.duration_mod
                else:
                    raise Exception("unreachable code (bug)")

        else:
            blist.append(b)

    if pets:
        blist.extend(map(Pets, aggregate_bonuses(pets)))
    blist.extend(aggregated.values())
    return blist
