"""python3 hub/test_server.py  -> prints ok"""
import json
from pathlib import Path
from server import Game

adv = json.loads((Path(__file__).parent / "adventures" / "fairy-forest.json").read_text())
g = Game(adv)
assert g.state()["clue"].startswith("Where the Old Oak")
assert g.hit(3) == "wrong" and g.healed == []
assert g.hit(1) == "heal" and g.healed == [1]
assert g.state()["clue"].startswith("The Oak is healed")
for s in (2, 3, 4):
    assert g.hit(s) == "heal"
assert g.hit(5) == "done" and g.state()["done"]
assert g.hit(1) == "done"  # ignored after finish
g.reset()
assert g.healed == [] and not g.state()["done"]
print("ok")
