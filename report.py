from __future__ import print_function
import argparse
from lnd_assistant import LndAssistant, sat_to_btc
import lnd_assistant_printer as Printer


def print_my_node_info(lnda):
  Printer.bprint(' == My node: %s (%s)' % (
      lnda.my_node_info['identity_pubkey'], lnda.my_node_info['alias']))
  print('  URI: %s' % (lnda.my_node_info['uris'][0]))
  print('  LND version: %s' % (lnda.my_node_info['version']))

  Printer.bprint(' == Channels')
  # There are multiple closed channels with chan_id = '0', ignore them.
  closed_channels = [ch for ch in lnda.closed_channels if ch['chan_id'] != '0']
  channels_opened_by_me = [ch for ch in lnda.channels if ch['opened_by_me']]
  print('  open:    %3d' % (len(lnda.channels)))
  print('  active:  %3d' % (lnda.my_node_info['num_active_channels']))
  print('  from me: %3d' % (len(channels_opened_by_me)))
  print('  pending: %3d' % (lnda.my_node_info['num_pending_channels']))
  print('  closed:  %3d' % (len(closed_channels)))

  Printer.bprint(' == Balance')
  local_balance = sum([ sat_to_btc(ch['local_balance'])
                        for ch in lnda.channels ])
  remote_balance = sum([ sat_to_btc(ch['remote_balance'])
                         for ch in lnda.channels ])
  capacity = local_balance + remote_balance
  commit_fees = sum([sat_to_btc(ch['commit_fee']) for ch in lnda.channels])
  print('  local:       %.5f' % (local_balance))
  print('  remote:      %.5f' % (remote_balance))
  print('  capacity:    %.5f (local + remote)' % (capacity))
  print('  commit fees: %.5f' % (commit_fees))
  print('  on-chain:    %.5f' % (sat_to_btc(lnda.balance['total_balance'])))


def print_routing_info(lnda, days, rows):
  Printer.bprint(' == Routing stats for the last %d days' % (days))
  print('  routing events: %d' % (len(lnda.fwd_events)))
  amt_forwarded = sum([int(e['amt_in']) for e in lnda.fwd_events])
  print('   amt forwarded: %s satoshis (%.5f BTC)' % (
        Printer.format_satoshi(amt_forwarded), sat_to_btc(amt_forwarded)))
  fees = sum([int(e['fee']) for e in lnda.fwd_events])
  print('  fees collected: %s satoshis' % (Printer.format_satoshi(fees)))
  routing_channels = lnda.routing_channels()
  show_rows = len(routing_channels) if len(routing_channels) < rows else rows
  Printer.bprint(' == Routing channels (showing %d out of %d):' % (
                 show_rows, len(routing_channels)))
  Printer.routing_channels_table(routing_channels[:rows])


def print_opened_and_closed_channels(lnda, rows):
  opened_channels = sorted(lnda.channels,
                           key=lambda ch: ch['opened_time'],
                           reverse=True)
  show_rows = len(opened_channels) if len(opened_channels) < rows else rows
  Printer.bprint(' == Recently opened channels (showing %d out of %d):' % (
                 show_rows, len(opened_channels)))
  Printer.open_channels_table(opened_channels[:rows])
  closed_channels = sorted(lnda.closed_channels,
                           key=lambda ch: ch['closed_time'],
                           reverse=True)
  show_rows = len(closed_channels) if len(closed_channels) < rows else rows
  Printer.bprint(' == Recently closed channels (showing %d out of %d):' % (
                 show_rows, len(closed_channels)))
  Printer.closed_channels_table(closed_channels[:rows])


def print_tips_on_channels_to_open(lnda, rows):
  peers = lnda.peers_exhausting_inbound_capacity()
  show_rows = len(peers) if len(peers) < rows else rows
  Printer.bprint(' == Candidate peers to rebalance (showing %d out of %d):' % (
                 show_rows, len(peers)))
  print('// These are the peers that received payments through your node and ' \
        'almost exhausted the inbound capacity of open channels. If you ' \
        'think these peers will further receive payments through your node - ' \
        'you can open additional channels to them.')
  Printer.peers_exhausting_inbound_capacity_table(peers[:rows])
  channels = lnda.closed_routing_channels()
  show_rows = len(channels) if len(channels) < rows else rows
  Printer.bprint(' == Closed routing channels (showing %d out of %d):' % (
                 show_rows, len(channels)))
  print('// If you think these channels were closed by accident - you can ' \
        'try to reopen channels to these peers (you may already have other ' \
        'channels to these peers).')
  Printer.closed_routing_channels_table(channels[:rows])
  # TODO: the list of peers with high number of channels.


def print_tips_on_channels_to_close(lnda, rows):
  peers = lnda.peers_with_multiple_channels()
  show_rows = len(peers) if len(peers) < rows / 2 else rows / 2
  Printer.bprint(' == Peers with multiple channels (showing %d out of %d):' % (
                 show_rows, len(peers)))
  print('// You can close some of these redundant channels that are rarely ' \
        'used. To free up on-chain balance - close the channels with high ' \
        'local_ratio.')
  Printer.peers_with_multiple_channels_table(peers[:rows / 2])
  channels = lnda.old_unused_channels()
  show_rows = len(channels) if len(channels) < rows else rows
  Printer.bprint(' == Oldest unused channels (showing %d out of %d):' % (
                 show_rows, len(channels)))
  print('// You can close some of these unused channels.')
  Printer.old_unused_channels_table(channels[:rows])


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='LndAssistant deep dive report.')
  parser.add_argument('--days', type = int, default = 7,
      help = 'Compute forwarding stats over the last days (default: 7).')
  parser.add_argument('--rows',
                      type = int,
                      default = 20,
                      help = 'List only top rows of tables (default: 20).')
  args = parser.parse_args()

  print('Generating the report, this could take some time...')
  lnda = LndAssistant(days=args.days)

  print_my_node_info(lnda)
  print_routing_info(lnda, args.days, args.rows)
  print_opened_and_closed_channels(lnda, args.rows)
  print_tips_on_channels_to_open(lnda, args.rows)
  print_tips_on_channels_to_close(lnda, args.rows)
  print('')
