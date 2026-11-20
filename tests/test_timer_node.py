import importlib.util
import json
import logging
import os
import sys
import types

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class FakeNode:
    def __init__(self, polyglot, primary, address, name):
        self.poly = polyglot
        self.primary = primary
        self.address = address
        self.name = name
        self.values = {}
        self.sent = []

    def setDriver(self, driver, value, report=True, force=False, uom=None, text=None):
        self.values[driver] = value
        self.sent.append((driver, value, force))


@pytest.fixture
def mod(monkeypatch):
    fake = types.ModuleType('udi_interface')
    fake.Node = FakeNode
    fake.LOGGER = logging.getLogger('timer-test')
    monkeypatch.setitem(sys.modules, 'udi_interface', fake)
    spec = importlib.util.spec_from_file_location(
        'timer_node_under_test', os.path.join(ROOT, 'timer_node.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture
def node(mod):
    return mod.TimerNode(None, 'controller', 'timer_1', 'Timer_1')


def run(node, cmd, value=None):
    command = {'cmd': cmd}
    if value is not None:
        command['value'] = value
    node.commands[cmd](node, command)


def test_starts_at_zero(node, mod):
    assert node.value == 0 and node.paused is False
    assert all(d['value'] == 0 for d in mod.TimerNode.drivers)


def test_zero_does_not_count(node):
    for _ in range(5):
        assert node.tick() is False
    assert node.value == 0


def test_start_sets_one_and_runs(node):
    run(node, 'START')
    assert node.value == 1 and node.values['ST'] == 1
    assert node.paused is False
    node.tick()
    node.tick()
    assert node.value == 3 and node.values['ST'] == 3


def test_start_clears_pause(node):
    run(node, 'SET_VALUE', '50')
    run(node, 'PAUSE')
    assert node.paused is True
    run(node, 'START')
    assert node.value == 1 and node.paused is False
    assert node.values['PAUSED'] == 0
    node.tick()
    assert node.value == 2


def test_start_on_running_timer_restarts_at_one(node):
    run(node, 'SET_VALUE', '40')
    run(node, 'START')
    assert node.value == 1


def test_start_needs_no_value(node):
    node.commands['START'](node, {'cmd': 'START'})
    assert node.value == 1


def test_counts_up_from_set_value(node):
    run(node, 'SET_VALUE', '5')
    assert node.values['ST'] == 5
    node.tick()
    node.tick()
    assert node.value == 7 and node.values['ST'] == 7


def test_pause_and_resume(node):
    run(node, 'SET_VALUE', '10')
    node.tick()
    run(node, 'PAUSE')
    assert node.values['PAUSED'] == 1
    node.tick()
    node.tick()
    assert node.value == 11
    run(node, 'RESUME')
    assert node.values['PAUSED'] == 0
    node.tick()
    assert node.value == 12


def test_pause_ignored_at_zero(node):
    run(node, 'PAUSE')
    assert node.paused is False and node.values.get('PAUSED', 0) == 0


def test_set_value_clears_pause(node):
    run(node, 'SET_VALUE', '3')
    run(node, 'PAUSE')
    run(node, 'SET_VALUE', '20')
    assert node.paused is False
    node.tick()
    assert node.value == 21


def test_set_zero_and_reset_stop_counting(node):
    run(node, 'SET_VALUE', '9')
    run(node, 'PAUSE')
    run(node, 'RESET')
    assert node.value == 0 and node.paused is False
    assert node.values['ST'] == 0 and node.values['PAUSED'] == 0
    assert node.tick() is False
    run(node, 'SET_VALUE', '4')
    run(node, 'SET_VALUE', '0')
    assert node.value == 0 and node.tick() is False


@pytest.mark.parametrize('bad', ['abc', '', '-1', '1.5', '2147483648', 'nan', 'inf', '-inf'])
def test_bad_values_refused(node, bad):
    run(node, 'SET_VALUE', '8')
    run(node, 'SET_VALUE', bad)
    assert node.value == 8


def test_missing_value_refused(node):
    run(node, 'SET_VALUE', '8')
    run(node, 'SET_VALUE')
    assert node.value == 8


def test_whole_float_text_accepted(node):
    run(node, 'SET_VALUE', '7.0')
    assert node.value == 7


def test_value_in_query_is_accepted(node):
    node.commands['SET_VALUE'](node, {'cmd': 'SET_VALUE', 'query': {'': '15'}})
    assert node.value == 15


def test_caps_at_max(node, mod):
    run(node, 'SET_VALUE', str(mod.MAX_VALUE))
    node.tick()
    assert node.value == mod.MAX_VALUE


def test_reset_state_always_reports(node):
    node.reset_state()
    assert ('ST', 0, True) in node.sent and ('PAUSED', 0, True) in node.sent


def test_commands_match_profile(mod):
    with open(os.path.join(ROOT, 'profile.json')) as f:
        profile = json.load(f)
    nodedefs = {n['id']: n for n in profile['nodedefs']}
    assert set(nodedefs) == {'controller', 'timer'}
    accepts = {c['id'] for c in nodedefs['timer']['cmds']['accepts']}
    assert accepts == set(mod.TimerNode.commands)
    assert 'START' in accepts
    assert mod.TimerNode.id == 'timer'
    for fn in mod.TimerNode.commands.values():
        assert callable(fn) and not hasattr(fn, '__self__')
    props = {p['id'] for p in nodedefs['timer']['properties']}
    assert props == {d['driver'] for d in mod.TimerNode.drivers}
    assert 'ST' in props
