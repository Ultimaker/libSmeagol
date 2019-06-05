import random
import re
import unittest
from typing import Dict, Any, NamedTuple, Optional, List

import math

import libSmeagol

class Node:
    def __init__(self, dataval=None):
        self.dataval = dataval
        self.nextval = None

    def flatten(self, start=None) -> List[str]:
        return ["Souron's " + self.dataval] + self.nextval.flatten(start if start is not None else self) if start is not self else []


class TheOneRing:
    def __init__(self, contents: Node) -> None:
        self.contents = contents  # type: Node

    def __str__(self) -> str:
        return re.sub(r",([^,]+$)", r" and\1", "<TheOneRing {} \>".format(", ".join(self.contents.flatten())))


class Sauron:
    finger = None
    @staticmethod
    def forgeRing() -> TheOneRing:
        ring = Node("Cruelty")
        ring.nextval = Node("Malice")
        ring.nextval.nextval = Node("Will to Dominate all life")
        ring.nextval.nextval.nextval = ring
        for _ in range(random.randint(0,255)):
            ring = ring.nextval
        return TheOneRing(ring)


Isildur = NamedTuple("Isildur", [("ring", TheOneRing)])


class Deagol:
    ring = None # type: Optional[TheOneRing]
    def fish(self, where: Dict[str, Any]) -> Any:
        return where.get("ring")


class Smeagol:
    def __init__(self):
        self.pocket = libSmeagol.Pocket()

    def kill(self, brother: Deagol) -> None:
        self.pocket.set("My Precious!", str(brother.ring))


class TheOneTestToRuleThemAll(unittest.TestCase):
    def test(self):
        Sauron.finger = Sauron.forgeRing()
        isildur = Isildur(Sauron.finger)
        Sauron.finger = None

        river = {"ring": isildur.ring }
        isildur = None

        deagol = Deagol()
        smeagol = Smeagol()

        deagol.ring = deagol.fish(river)
        smeagol.kill(deagol)
        deagol = None

        gollum = smeagol

        assert gollum.pocket.get("My Precious!") is not None
