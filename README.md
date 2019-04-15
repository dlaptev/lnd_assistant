# LND assistant - useful scripts for `lnd`

1. [`report.py`](#1-reportpy) - in-depth reporting:
   1. overall node stats;
   2. detailed routing stats per channel;
   3. recently opened/closed channels;
   4. suggestions to open channels (to re-balance routing channels);
   5. suggestions to close channels (redundant or unused).
2. [`select_payment_route.py`](#2-select_payment_routepy) - a tool to pay smarter:
   1. know in advance how much fees you will pay;
   2. or pay along the route that balances your channels.
3. [`set_range_fees.py`](#3-set_range_feespy) - a tool to passively balance channels via adaptive fees:
   1. set fees inversely proportional to the local balance of each channel;
   2. this will encourage channels to be used in the direction that balances them.

## 0. Usage
If you have `python`, `lncli` and `bitcoin-cli` all on one machine - you are good to go.

1. Download the repository: `git clone https://github.com/dlaptev/lnd_assistant`
2. Make sure that `lncli` is unlocked: `lncli unlock`
3. Run one of the scripts: `python ./lnd_assistant/report.py`

The scripts are designed to be as simple to use as possible: no installation, no dependencies, no configuration. But it only works for the most popular setup: `lnd` + `bitcoind` on one machine. If you have remote `bitcoind` - you will need to install local `bictoin-cli` and point it to the remote backend. If you have differend backend (such as `btcd`) - you will need to modify the code (it is very simple though).

## 1. `report.py`
You can pass two optional arguments:
  * `python report.py --days=14` - this will compute forwarding stats over the last 14 days (instead of 7 by default);
  * `python report.py --rows=10` - this will show maximum 10 rows in each table (instead of 20 by default).

#### i. Overall node stats
 * Number of open/closed/active/pending channels, number of channels opened by your node;
 * Local/remote/on-chain balance, fees reserved for on-chain transactions;
 * Routing events, amount forwarded, fees collected.

![Overall node stats](https://github.com/dlaptev/dlaptev.github.io/blob/master/img/github/lnd_assistant_report_1.png?raw=true "Overall node stats example")

#### ii. Detailed routing stats per channel
 * Number of forwarding events and amount forwarded in each direction;
 * Fees collected from each channel;
 * Capacity of each channel and how balanced the channel is (local_ratio).

![Detailed routing stats](https://github.com/dlaptev/dlaptev.github.io/blob/master/img/github/lnd_assistant_report_2.png?raw=true "Detailed routing stats example")

#### iii. Recently opened/closed channels
 * When and why (by whom) the channel was opened/closed;
 * Capacity, local_ratio and settled balance;
 * Whether the channel is active/used.

![Recently opened/closed channels](https://github.com/dlaptev/dlaptev.github.io/blob/master/img/github/lnd_assistant_report_3.png?raw=true "Recently opened/closed channels example")

#### iv. Suggestions to open channels
 * A list of peers that received payments through your node and almost exhausted the inbound capacity of open channels. If you think these peers will further receive payments through your node - you can open additional channels to them.
 * A list of closed channels used for routing. If you think these channels were closed by accident - you can try to reopen channels to these peers.
 * A list of nodes with the largest number of channels with which your node has no channels. It is not always a good idea to open channels to these nodes, but it could help to increase your ability to send payments.

![Suggestions to open channels](https://github.com/dlaptev/dlaptev.github.io/blob/master/img/github/lnd_assistant_report_4.png?raw=true "Suggestions to open channels example")

#### v. Suggestions to close channels
 * A list of peers with multiple channels. You can close some of these redundant channels that are rarely used. To free up on-chain balance - close the channels with high local_ratio.
 * A list of oldest channels that were never used. You can close some of these.

![Suggestions to close channels](https://github.com/dlaptev/dlaptev.github.io/blob/master/img/github/lnd_assistant_report_5.png?raw=true "Suggestions to close channels example")

## 2. `select_payment_route.py`
The first argument is the payment request (invoice) and is mandatory, the other two are optional:
 * `python select_payment_route.py lnbc1...` - this will decode the provided payment request and suggest multiple routes;
 * `python select_payment_route.py lnbc1... --amt=10` - you need to provide an amount if the amount is not specified in the payment request (equals to zero);
 * `python select_payment_route.py lnbc1... --max_routes=20` - this will show you 20 different routes (instead of 10 by default).

Notes.
 * Selecting a route guarantees you a fixed fee, but there is no guarantee that a route would work (this is because `lnd` does not know in advance how the balance is distributed along the route). Try selecting multiple acceptable routes.
 * To better balance your channels - select a route with large local_ratio. Paying the invoice will decrease local_ratio making the channel more balanced.

![Select payment route](https://github.com/dlaptev/dlaptev.github.io/blob/master/img/github/lnd_assistant_select_payment_route.png?raw=true "Select payment route example")

## 3. `set_range_fees.py`

The idea behind this script is to passively balance channels by adjusting fees according to how balanced each channel is. It works like this:
1. set lower fees for channels where most of the balance is local,
2. this will result in more payments being routed through this channel,
3. this is turn will result in a more balanced channel;
4. for channels that already have low local balance - increase the fees proportionally to the ratio of the local balance;
5. this will decrease the number of payments that make the channel les balanced.

There are six arguments:
 * `--min_base_fee_msat`  - minimal base fee (absolute fee) in milli-satoshis (default: 1);
 * `--max_base_fee_msat` - maximum base fee (absolute fee) in milli-satoshis (default: 1000);
 * `--min_fee_rate` - minimal fee rate (relative fee) (default: 0.000001);
 * `--max_fee_rate` - maximum fee rate (relative fee) (default: 0.001000);
 * `--left_cap_local_ratio` - the channels with local balance ratio below this value will have maximum fees (default: 0.0);
 * `--right_cap_local_ratio` - the channels with local balance ratio above this value will have minimum fees (default: 0.7).

This will result in the following fees being set per channel:
 * Channels with local balance ratio below `left_cap_local_ratio` (mostly remote balance) will have `max_base_fee_msat` and `max_fee_rate` fees.
 * Channels with local balance ratio above `right_cap_local_ratio` (mostly local balance) will have `min_base_fee_msat` and `min_fee_rate` fees.
 * Channels with local balance ratio between `left_cap_local_ratio` and `right_cap_local_ratio` will have both base fees and fee rate linearly interpolated between the maximum and minimum rates.


## Do you have questions or ideas or want to help?

Please feel free to create an issue, submit a pull request, fork and change whatever you want, write to me directly (contact@lightningto.me), or tip via https://tippin.me/@LightningTo_Me.
