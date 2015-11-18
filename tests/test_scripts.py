import unittest
from nose.tools import *  # PEP8 asserts

import time

import labtronyx

class ScriptStub(labtronyx.ScriptBase):

    def run(self):
        time.sleep(0.5)


def test_scripts():
    man = labtronyx.InstrumentManager()

    scr = ScriptStub(manager=man)

    assert(scr.isReady())
    scr.start()
    scr.join()

    props = scr.getProperties()

    assert(len(props.get('results', [])) == 1)