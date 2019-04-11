# LND assistant - useful scripts for `lnd`

1. [`report.py`](#reportpy) - in-depth reporting:
   1. overall node stats;
   2. detailed routing stats per channel;
   3. recently opened/closed channels;
   4. suggestions to open channels (to re-balance routing channels);
   5. suggestions to close channels (redundant or oldest unused).
2. [`select_payment_route.py`](#select-payment-routepy) - a tool to pay smarter:
   1. know exactly how much fees will you pay in advance;
   2. or pay along the route that balances your channels.
3. [`set_range_fees.py`](#set-range-feespy) - a tool to passively balance channels via adaptive fees:
   1. set fees inversely proportional to the local balance of each channel;
   2. this will encourage channels to be used in the direction that balances them.

## Usage
1. Download the repository: `git clone https://github.com/dlaptev/lnd_assistant`
2. Make sure that `lncli` is unlocked: ```lncli unlock```
3. Run one of the scripts: `python ./lnd_assistant/report.py`

No installation, no dependencies. If you have python - you are good to go.

## `report.py`

## `select_payment_route.py`

## `set_range_fees.py`
