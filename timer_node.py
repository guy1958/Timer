"""Count-up timer node for the Timer plugin."""
import math
import threading

from udi_interface import Node, LOGGER

MAX_VALUE = 2147483647


def parse_value(command):
    """Return the requested value as an int in 0..MAX_VALUE, or None if unusable."""
    raw = command.get('value')
    if raw is None:
        query = command.get('query') or {}
        if '' in query:
            raw = query['']
        elif len(query) == 1:
            raw = next(iter(query.values()))
    try:
        number = float(raw)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number != int(number):
        return None
    number = int(number)
    if number < 0 or number > MAX_VALUE:
        return None
    return number


class TimerNode(Node):
    id = "timer"
    drivers = [
        {'driver': 'ST', 'value': 0, 'uom': 56, 'name': 'Value'},
        {'driver': 'PAUSED', 'value': 0, 'uom': 2, 'name': 'Paused'},
    ]

    def __init__(self, polyglot, primary, address, name):
        super().__init__(polyglot, primary, address, name)
        self._lock = threading.Lock()
        self.value = 0
        self.paused = False

    def _publish(self, force=False):
        self.setDriver('ST', self.value, True, force)
        self.setDriver('PAUSED', 1 if self.paused else 0, True, force)

    def reset_state(self):
        """Back to 0 and not paused; always reported, even if unchanged."""
        with self._lock:
            self.value = 0
            self.paused = False
            self._publish(force=True)

    def tick(self):
        """One second elapsed. Counts up only if the value is not 0 and not paused."""
        with self._lock:
            if self.value == 0 or self.paused:
                return False
            if self.value < MAX_VALUE:
                self.value += 1
            self.setDriver('ST', self.value)
            return True

    def set_value(self, number):
        with self._lock:
            self.value = number
            self.paused = False
            self._publish()

    def pause(self):
        with self._lock:
            if self.value == 0 or self.paused:
                return
            self.paused = True
            self._publish()

    def resume(self):
        with self._lock:
            if not self.paused:
                return
            self.paused = False
            self._publish()

    def reset(self):
        with self._lock:
            self.value = 0
            self.paused = False
            self._publish()

    def cmd_start(self, command):
        """Start: set the value to 1 (clearing any pause) so the timer runs."""
        self.set_value(1)

    def cmd_set_value(self, command):
        number = parse_value(command)
        if number is None:
            LOGGER.warning('%s: refused Set Value %r (need a whole number from 0 to %d)',
                           self.address, command.get('value'), MAX_VALUE)
            return
        self.set_value(number)

    def cmd_pause(self, command):
        self.pause()

    def cmd_resume(self, command):
        self.resume()

    def cmd_reset(self, command):
        self.reset()

    commands = {
        'START': cmd_start,
        'SET_VALUE': cmd_set_value,
        'PAUSE': cmd_pause,
        'RESUME': cmd_resume,
        'RESET': cmd_reset,
    }
