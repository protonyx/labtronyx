import unittest
from nose.tools import * # PEP8 asserts

import labtronyx

@unittest.skip('RPC not working')
def test_init_time_rpc():
    import time
    start = time.clock()
    instr = labtronyx.InstrumentManager(rpc=True)
    delta = time.clock() - start
    assert_less_equal(delta, 2.0, "RPC Init time must be less than 2.0 second(s)")

    instr.rpc_stop()
    del instr

@unittest.skip('RPC not working')
def test_remote_connect():
    # Setup an InstrumentManager with RPC
    instr = labtronyx.InstrumentManager(rpc=True)

    client = labtronyx.RemoteManager(uri='http://localhost:6780/')

    assert_equal(client.getVersion(), instr.getVersion())

    instr.rpc_stop()
    del instr
