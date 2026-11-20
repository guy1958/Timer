# Timer

# Timer

Twenty count-up timers for eisy programs: `Timer_1` through `Timer_20`.

## Behavior

- Every timer starts at **0** and stays there until you set it.
- A timer whose value is anything other than 0 counts up by 1 every second.
- **Value** is a plain number. In a program you can test it with greater than, less than, equal to and so on.
- **Restart:** whenever the plugin or the system restarts, every timer goes back to 0.

## Commands (on each timer)

| Command | What it does |
|---|---|
| Start | Sets the value to 1, clears any pause, and the timer counts up from there. On a timer that is already running it restarts the count at 1. |
| Set Value | Sets the timer to the number you enter (a whole number, 0 to 2147483647) and starts it counting if it isn't 0. Also clears a pause. Setting 0 stops it. |
| Pause | Stops counting and keeps the current value. Ignored if the timer is at 0. |
| Resume | Continues counting from the paused value. |
| Reset to 0 | Sets the value to 0, stops counting and clears any pause. |

A value that isn't a whole number in range is refused: nothing changes and a warning is logged.

## Properties

- **Value** (`ST`): the current count, as a raw number.
- **Paused**: Yes while a timer is paused, otherwise No.

## Notes

- A timer counts about once per second, kept in step with a monotonic clock, so it does not drift with the work done on each tick.
- Nothing is configurable: no keys, accounts or settings are needed.
- The plugin has no access to eisy beyond its own nodes.
