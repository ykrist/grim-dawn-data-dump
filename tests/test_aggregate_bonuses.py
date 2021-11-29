from grim_dawn_data import load_constellation_bonuses
from grim_dawn_data.bonuses import aggregate_bonuses

def test_aggregate_bonuses():
    cons = load_constellation_bonuses()

    blist = []
    for c in cons:
        for s in c['skills'].values():
            blist.extend(s.get('bonuses', []))

    print()
    for b in aggregate_bonuses(blist):
        print(f"{b.kind_id():<60} {b.display()}")


