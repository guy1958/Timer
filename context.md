## 2026-11-18T19:04:45.826078+00:00

1.0.0: initial version. Controller creates 20 count-up timer nodes (Timer_1..Timer_20, addresses timer_1..timer_20). A 1-second monotonic tick thread started in start() counts up any non-zero, non-paused timer. Commands SET_VALUE/PAUSE/RESUME/RESET. All timers forced to 0 on every start. Value is the ST property (uom 56 raw); PAUSED (uom 2) added for visibility.

Sources consulted: Einstein42/udi-poly-template-python (MIT), UniversalDevicesInc/udi-poly-template-python (MIT)

## 2026-11-20T18:40:13.096896+00:00

1.1.0: added a START command to the timer nodedef. It calls set_value(1): value becomes 1, any pause is cleared, and the tick loop counts it up. On a running timer it restarts the count at 1. Added tests for it and a README row. No other behavior changed.

