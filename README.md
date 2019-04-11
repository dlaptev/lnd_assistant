# LND assistant - useful scripts for `lnd`

1. [`report.py`](#reportpy) - in-depth reporting:
   1. overall node stats;
   2. detailed routing stats per channel;
   3. recently opened/closed channels;
   4. suggestions to open channels (to re-balance routing channels);
   5. suggestions to close channels (redundant or unused).
2. [`select_payment_route.py`](#select_payment_routepy) - a tool to pay smarter:
   1. know exactly how much fees will you pay in advance;
   2. or pay along the route that balances your channels.
3. [`set_range_fees.py`](#set_range_feespy) - a tool to passively balance channels via adaptive fees:
   1. set fees inversely proportional to the local balance of each channel;
   2. this will encourage channels to be used in the direction that balances them.

## Usage
1. Download the repository: `git clone https://github.com/dlaptev/lnd_assistant`
2. Make sure that `lncli` is unlocked: `lncli unlock`
3. Run one of the scripts: `python ./lnd_assistant/report.py`

No installation, no dependencies. If you have python - you are good to go.

## `report.py`
You can pass two optional arguments:
  * `python report.py --days=14` - this will compute forwarding stats over the last 14 days (instead of 7 by default);
  * `python report.py --rows=10` - this will show maximum 10 rows in each table (instead of 20 by default).

### Overall node stats
 * Number of open/closed/active/pending channels, number of channels opened by your node;
 * Local/remote/on-chain balance, fees reserved for on-chain transactions;
 * Routing events, amount forwarded, fees collected.

![Overall node stats](https://github.com/dlaptev/dlaptev.github.io/blob/master/img/github/lnd_assistant_report_1.png?raw=true "Overall node stats example")

### Detailed routing stats per channel
 * Number of forwarding events and amount forwarded in each direction;
 * Fees collected from each channel;
 * Capacity of each channel and how balanced the channel is (local_ratio).

![Detailed routing stats](https://github.com/dlaptev/dlaptev.github.io/blob/master/img/github/lnd_assistant_report_2.png?raw=true "Detailed routing stats example")

### Recently opened/closed channels
 * When and why (by whom) the channel was opened/closed;
 * Capacity, local_ratio and settled balance;
 * Whether the channel is active/used.

![Recently opened/closed channels](https://github.com/dlaptev/dlaptev.github.io/blob/master/img/github/lnd_assistant_report_3.png?raw=true "Recently opened/closed channels example")

### Suggestions to open channels
 * A list of peers that received payments through your node and almost exhausted the inbound capacity of open channels. If you think these peers will further receive payments through your node - you can open additional channels to them.
 * A list of closed channels used for routing. If you think these channels were closed by accident - you can try to reopen channels to these peers.
 * A list of nodes with the largest number of channels with which your node has no channels. It is not always a good idea to open channels to these nodes, but it could help to increase your ability to send payments.

![Suggestions to open channels](https://github.com/dlaptev/dlaptev.github.io/blob/master/img/github/lnd_assistant_report_4.png?raw=true "Suggestions to open channels example")

### Suggestions to close channels
 * A list of peers with multiple channels. You can close some of these redundant channels that are rarely used. To free up on-chain balance - close the channels with high local_ratio.
 * A list of oldest channels that were never used. You can close some of these.

![Suggestions to close channels](https://github.com/dlaptev/dlaptev.github.io/blob/master/img/github/lnd_assistant_report_5.png?raw=true "Suggestions to close channels example")

## `select_payment_route.py`
The first argument is the payment request (invoice) and is mandatory, the other two are optional:
 * `python select_payment_route.py lnbc1...` - this will decode the provided payment request and suggest multiple routes;
 * `python select_payment_route.py lnbc1... --amt=10` - you need to provide an amount if the amount is not specified in the payment request (equals to zero);
 * `python select_payment_route.py lnbc1... --max_routes=20` - this will show you 20 different routes (instead of 10 by default).

Notes.
 * Selecting a route guarantees you a fixed fee, but there is no guarantee that a route would work (this is because `lnd` does not know in advance how the balance is distributed along the route). Try selecting multiple acceptable routes.
 * To better balance your channels - select a route with large local_ratio. Paying the invoice will decrease local_ratio making the channel more balanced.

![Select payment route](https://github.com/dlaptev/dlaptev.github.io/blob/master/img/github/lnd_assistant_select_payment_route.png?raw=true "Select payment route example")

## `set_range_fees.py`
