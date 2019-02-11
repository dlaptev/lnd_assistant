from pprint import pprint
import time


class Printer:
  @staticmethod
  def bprint(str):
    print('\n\033[01m%s\033[00m' % (str))

  @staticmethod
  def cprint(str):
    print('\033[96m%s\033[00m' % (str))

  @staticmethod
  def format_satoshi(satoshi_as_string):
    if type(satoshi_as_string) == int:
      satoshi_as_string = str(satoshi_as_string)
    temp = []
    for i in range(1, len(satoshi_as_string) + 1):
      temp.append(satoshi_as_string[-i])
      if i % 3 == 0 and i != len(satoshi_as_string):
        temp.append('\'')
    return ''.join(temp[::-1])

  @staticmethod
  def open_channels_table(channels):
    Printer.cprint(
        ' %12s | %9s | %10s | %11s | %6s | %4s | %10s | %18s | %s' % (
            'opened at', 'opened_by', 'capacity', 'local_ratio', 'active',
            'used', 'fwd_events', 'chan_id', 'remote_alias'))
    for ch in channels:
      print(' %12s | %9s | %10s | %11.2f | %6s | %4s | %10d | %18s | %s' % (
            time.strftime('%d %b %H:%M', time.localtime(ch['opened_time'])),
            'me' if ch['opened_by_me'] else 'peer',
            Printer.format_satoshi(ch['capacity']),
            ch['local_ratio'],
            'yes' if ch['active'] else 'no',
            'yes' if ch['used'] else 'no',
            ch['fwd_events'],
            ch['chan_id'],
            ch['remote_alias']))

  @staticmethod
  def closed_channels_table(channels):
    Printer.cprint(
        ' %12s | %12s | %9s | %9s | %10s | %10s | %9s | %10s | %18s | %s' % (
            'closed_at', 'close_type', 'opened_by', 'closed_by', 'capacity',
            'settled', 'days_used', 'fwd_events', 'chan_id', 'remote_alias'))
    for ch in channels:
      channel_age = 'unknown'
      if ch['channel_age'] > 0:
        channel_age = int(ch['channel_age']) / (24 * 60 * 60)
      close_type = ch['close_type'].lower()
      if close_type.endswith('_close'):
        close_type = close_type[:-6]
      print(
          ' %12s | %12s | %9s | %9s | %10s | %10s | %9d | %10d | %18s | %s' % (
              time.strftime('%d %b %H:%M', time.localtime(ch['closed_time'])),
              close_type,
              'me' if ch['opened_by_me'] else 'peer',
              'me' if ch['closed_by_me'] else 'peer',
              Printer.format_satoshi(ch['capacity']),
              Printer.format_satoshi(ch['settled_balance']),
              channel_age,
              ch['fwd_events'],
              ch['chan_id'],
              ch['remote_alias']))

  @staticmethod
  def routing_channels_table(channels):
    Printer.cprint(
        ' %10s | %9s | %19s | %5s | %10s | %11s | %9s | %18s | %s' % (
            'fwd_events', 'in/out', 'avg_amt in/out', 'fees', 'capacity',
            'local_ratio', 'opened_by', 'chan_id', 'remote_alias'))
    for ch in channels:
      local_ratio_as_str = ch['local_ratio']
      if type(ch['local_ratio']) == float:
        local_ratio_as_str = '%.2f' % ch['local_ratio']
      fwd_events_in_out = '%4d/%4d' % ( ch['fwd_events_in'],
                                        ch['fwd_events_out'] )
      amt_in_out = '%9s/%9s' % ( Printer.format_satoshi(ch['avg_amt_in']),
                                 Printer.format_satoshi(ch['avg_amt_out']) )
      print(' %10d | %9s | %19s | %5s | %10s | %11s | %9s | %18s | %s' % (
          ch['fwd_events'],
          fwd_events_in_out,
          amt_in_out,
          Printer.format_satoshi(ch['fees']),
          Printer.format_satoshi(ch['capacity']),
          local_ratio_as_str,
          'me' if ch['opened_by_me'] else 'peer',
          ch['chan_id'],
          ch['remote_alias']))
