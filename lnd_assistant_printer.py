import time

def bprint(str):
  print('\n\033[01m%s\033[00m' % (str))


def cprint(str):
  print('\033[96m%s\033[00m' % (str))


def format_satoshi(satoshi_as_string):
  if type(satoshi_as_string) == int:
    satoshi_as_string = str(satoshi_as_string)
  temp = []
  for i in range(1, len(satoshi_as_string) + 1):
    temp.append(satoshi_as_string[-i])
    if i % 3 == 0 and i != len(satoshi_as_string):
      temp.append('\'')
  return ''.join(temp[::-1])


def open_channels_table(channels):
  cprint(' %12s | %9s | %10s | %11s | %6s | %4s | %10s | %18s | %s' % (
         'opened at', 'opened_by', 'capacity', 'local_ratio', 'active',
         'used', 'fwd_events', 'chan_id', 'remote_alias'))
  for ch in channels:
    print(' %12s | %9s | %10s | %11.2f | %6s | %4s | %10d | %18s | %s' % (
          time.strftime('%d %b %H:%M', time.localtime(ch['opened_time'])),
          'me' if ch['opened_by_me'] else 'peer',
          format_satoshi(ch['capacity']),
          ch['local_ratio'],
          'yes' if ch['active'] else 'no',
          'yes' if ch['used'] else 'no',
          ch['fwd_events'],
          ch['chan_id'],
          ch['remote_alias']))


def closed_channels_table(channels):
  cprint(' %12s | %12s | %9s | %9s | %10s | %10s | %9s | %10s | %18s | %s' % (
         'closed_at', 'close_type', 'opened_by', 'closed_by', 'capacity',
         'settled', 'days_used', 'fwd_events', 'chan_id', 'remote_alias'))
  for ch in channels:
    channel_age = 'unknown'
    if ch['channel_age'] > 0:
      channel_age = str(int(ch['channel_age']) / (24 * 60 * 60))
    close_type = ch['close_type'].lower()
    if close_type.endswith('_close'):
      close_type = close_type[:-6]
    print(' %12s | %12s | %9s | %9s | %10s | %10s | %9s | %10d | %18s | %s' % (
          time.strftime('%d %b %H:%M', time.localtime(ch['closed_time'])),
          close_type,
          'me' if ch['opened_by_me'] else 'peer',
          'me' if ch['closed_by_me'] else 'peer',
          format_satoshi(ch['capacity']),
          format_satoshi(ch['settled_balance']),
          channel_age,
          ch['fwd_events'],
          ch['chan_id'],
          ch['remote_alias']))


def closed_routing_channels_table(channels):
  cprint((' %12s | %12s | %9s | %9s | %10s | %10s | %9s | %10s | %14s | ' \
          '%18s | %s (%s)') % (
          'closed_at', 'close_type', 'opened_by', 'closed_by', 'capacity',
          'settled', 'days_used', 'fwd_events', 'other_channels', 'chan_id',
          'remote_pubkey', 'remote_alias'))
  for ch in channels:
    channel_age = 'unknown'
    if ch['channel_age'] > 0:
      channel_age = str(int(ch['channel_age']) / (24 * 60 * 60))
    close_type = ch['close_type'].lower()
    if close_type.endswith('_close'):
      close_type = close_type[:-6]
    print((' %12s | %12s | %9s | %9s | %10s | %10s | %9s | %10d | %14s | ' \
           '%18s | %s (%s)') % (
           time.strftime('%d %b %H:%M', time.localtime(ch['closed_time'])),
           close_type,
           'me' if ch['opened_by_me'] else 'peer',
           'me' if ch['closed_by_me'] else 'peer',
           format_satoshi(ch['capacity']),
           format_satoshi(ch['settled_balance']),
           channel_age,
           ch['fwd_events'],
           ch['other_channels'],
           ch['chan_id'],
           ch['remote_pubkey'],
           ch['remote_alias']))


def routing_channels_table(channels):
  cprint(' %10s | %9s | %19s | %5s | %10s | %11s | %9s | %18s | %s' % (
         'fwd_events', 'in/out', 'avg_amt in/out', 'fees', 'capacity',
         'local_ratio', 'opened_by', 'chan_id', 'remote_alias'))
  for ch in channels:
    local_ratio_as_str = ch['local_ratio']
    if type(ch['local_ratio']) == float:
      local_ratio_as_str = '%.2f' % ch['local_ratio']
    fwd_events_in_out = '%4d/%4d' % ( ch['fwd_events_in'],
                                      ch['fwd_events_out'] )
    amt_in_out = '%9s/%9s' % ( format_satoshi(ch['avg_amt_in']),
                               format_satoshi(ch['avg_amt_out']) )
    print(' %10d | %9s | %19s | %5s | %10s | %11s | %9s | %18s | %s' % (
          ch['fwd_events'],
          fwd_events_in_out,
          amt_in_out,
          format_satoshi(ch['fees']),
          format_satoshi(ch['capacity']),
          local_ratio_as_str,
          'me' if ch['opened_by_me'] else 'peer',
          ch['chan_id'],
          ch['remote_alias']))


def peers_with_multiple_channels_table(peers):
  cprint(' %22s | %7s | %9s | %10s | %11s | %6s | %4s | %10s | %s' % (
         'remote_alias', 'number', 'opened_by', 'capacity', 'local_ratio',
         'active', 'used', 'fwd_events', 'funding_tx and output_number'))
  for peer_channels in peers:
    n = len(peer_channels)
    for i in range(n):
      ch = peer_channels[i]
      print(' %22s | %3d/%3d | %9s | %10s | %11.2f | %6s | %4s | %10s | %s' % (
            ch['remote_alias'][:22],
            (i+1), n,
            'me' if ch['opened_by_me'] else 'peer',
            format_satoshi(ch['capacity']),
            ch['local_ratio'],
            'yes' if ch['active'] else 'no',
            'yes' if ch['used'] else 'no',
            ch['fwd_events'],
            ' '.join(ch['channel_point'].split(':'))))


def peers_exhausting_inbound_capacity_table(peers):
  cprint(' %8s | %14s | %11s | %10s | %12s | %10s | %s (%s)' % (
         'channels', 'total_capacity', 'local_ratio', 'sat_sent',
         'sat_received', 'fwd_events', 'remote_pubkey', 'alias'))
  for peer in peers:
    print(' %8d | %14s | %11.2f | %10s | %12s | %10d | %s (%s)' % (
          peer['n_channels'],
          format_satoshi(peer['total_capacity']),
          peer['total_local_ratio'],
          format_satoshi(peer['total_satoshis_sent']),
          format_satoshi(peer['total_satoshis_received']),
          peer['fwd_events'],
          peer['remote_pubkey'],
          peer['alias']))


def old_unused_channels_table(channels):
  cprint(' %12s | %9s | %10s | %6s | %22s | %s' % (
         'opened at', 'opened_by', 'capacity', 'active', 'alias',
         'funding_tx and output_number'))
  for ch in channels:
    print(' %12s | %9s | %10s | %6s | %22s | %s' % (
          time.strftime('%d %b %H:%M', time.localtime(ch['opened_time'])),
          'me' if ch['opened_by_me'] else 'peer',
          format_satoshi(ch['capacity']),
          'yes' if ch['active'] else 'no',
          ch['remote_alias'][:22],
          ' '.join(ch['channel_point'].split(':'))))

def non_direct_peers_with_most_channels_table(peers):
  cprint(' %10s | %10s | %66s | %20s | %s' % (
         'channels', 'capacity', 'pubkey', 'address', 'alias'))
  for peer in peers:
    addr = 'unknown'
    if len(peer['addresses']) and 'addr' in peer['addresses'][0]:
      addr = peer['addresses'][0]['addr']
    print(' %10d | %10.5f | %66s | %20s | %s' % (
          peer['channels'],
          peer['capacity'],
          peer['pubkey'],
          addr,
          peer['alias']))
