from __future__ import print_function
import argparse
from lnd_assistant import LndAssistant, sat_to_btc, Printer


def print_my_node_info(lnda):
  ## Overall node stats.
  Printer.bprint(' == My node: %s (%s)' % (
      lnda.my_node_info['identity_pubkey'], lnda.my_node_info['alias']))
  print('  URI: %s' % (lnda.my_node_info['uris'][0]))
  print('  LND version: %s' % (lnda.my_node_info['version']))

  Printer.bprint(' == Channels')
  # There are multiple closed channels with chan_id = '0', ignore them.
  closed_channels = [ch for ch in lnda.closed_channels if ch['chan_id'] != '0']
  outgoing_channels = [ch for ch in lnda.channels if ch['outgoing']]
  print('  open:     %3d' % (len(lnda.channels)))
  print('  active:   %3d' % (lnda.my_node_info['num_active_channels']))
  print('  outgoing: %3d' % (len(outgoing_channels)))
  print('  pending:  %3d' % (lnda.my_node_info['num_pending_channels']))
  print('  closed:   %3d' % (len(closed_channels)))

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


def print_opened_and_closed_channels(lnda, days, rows):
  opened_channels = lnda.newly_opened_channels(days)
  closed_channels = lnda.newly_closed_channels(days)
  rows_opened = len(opened_channels) if len(opened_channels) < rows else rows
  rows_closed = len(closed_channels) if len(closed_channels) < rows else rows
  Printer.bprint((' == Channels opened in the last %d days ' +
                  '(showing %d out of %d):') % (days, rows_opened,
                                                len(opened_channels)))
  Printer.open_channels_table(opened_channels[-rows:])
  Printer.bprint((' == Channels closed in the last %d days ' +
                  '(showing %d out of %d):') % (days, rows_closed,
                                                len(closed_channels)))
  for ch in closed_channels[-rows:]:
    print('')


if __name__ == '__main__':
  parser = argparse.ArgumentParser(
      description='LndAssistant report.')
  parser.add_argument('--days',
                      type=int,
                      default=7,
                      help='List changes over the last days (default: 7).')
  parser.add_argument('--rows',
                      type=int,
                      default=20,
                      help='List only top rows of tables (default: 20).')
  args = parser.parse_args()

  lnda = LndAssistant(days=args.days)
  print_my_node_info(lnda)
  print_opened_and_closed_channels(lnda, args.days, args.rows)
  ## New channels in the last days.
  ## Channels closed in the last days.
  ## Forwarding stats.
