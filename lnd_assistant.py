from collections import defaultdict
import json
import os
import pickle
import time


def sat_to_btc(satoshi_as_string):
  return int(satoshi_as_string) * 1e-8


class Printer:
  @staticmethod
  def bprint(str):
    print('\033[01m%s\033[00m' % (str))

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
        ' %12s | %10s | %10s | %11s | %6s | %4s | %10s | %18s | %s' % (
        'opened at', 'from/to me', 'capacity', 'local_ratio', 'active',
        'used', 'fwd_events', 'chan_id', 'remote_alias'))
    for ch in channels:
      print(' %12s | %10s | %10s | %11.2f | %6s | %4s | %10d | %18s | %s' % (
            time.strftime('%d %b %H:%M', time.localtime(ch['opened'])),
            'from me' if ch['outgoing'] else 'to me',
            Printer.format_satoshi(ch['capacity']),
            ch['local_ratio'],
            'yes' if ch['active'] else 'no',
            'yes' if ch['used'] else 'no',
            ch['fwd_events'],
            ch['chan_id'],
            ch['remote_alias']))


class LndAssistant:
  def outgoing_channel(self, ch):
    # TODO: can probably be done for closed channels as well through
    #       settled_balance and time_locked_balance.
    return ((float(ch['local_balance']) > 0 and
             float(ch['total_satoshis_received']) == 0) or
            (float(ch['total_satoshis_sent']) >
             float(ch['total_satoshis_received'])))


  def __init__(self, days=7):
    if len(os.popen('lncli walletbalance').read()) == 0:
      raise PermissionError('lncli is locked or does not exist.')

    self.days = days

    ## Node info.
    self.my_node_info = json.loads(os.popen('lncli getinfo').read())
    # my_node_info: { 'alias',
    #                 'best_header_timestamp',
    #                 'block_hash',
    #                 'block_height',
    #                 'chains',
    #                 'identity_pubkey',
    #                 'num_active_channels',
    #                 'num_inactive_channels',
    #                 'num_peers',
    #                 'num_pending_channels',
    #                 'synced_to_chain',
    #                 'testnet',
    #                 'uris',
    #                 'version' }
    self.balance = json.loads(os.popen('lncli walletbalance').read())
    # balance: { 'confirmed_balance',
    #            'total_balance',
    #            'unconfirmed_balance' }

    ## Network graph.
    self.graph = json.loads(os.popen('lncli describegraph').read())
    # graph['nodes']: { 'pub_key',
    #                   'alias',
    #                   'color',
    #                   'addresses': [ {'network',
    #                                   'addr'} ],
    #                   'last_update'}
    self.node_stats = { node['pub_key'] : { 'alias': node['alias'],
                                            'addresses': node['addresses'],
                                            'last_update': node['last_update'],
                                            'capacity': 0.0,
                                            'channels': 0, }
                        for node in self.graph['nodes'] }
    # graph['edges']: { 'chan_point',
    #                   'capacity',
    #                   'channel_id',
    #                   'last_update',
    #                   'node1_pub',
    #                   'node2_pub',
    #                   'node1_policy': { 'min_htlc',
    #                                     'fee_base_msat',
    #                                     'disabled',
    #                                     'fee_rate_milli_msat',
    #                                     'time_lock_delta' },
    #                   'node2_policy': {...} }
    for edge in self.graph['edges']:
      for pubkey in [edge['node1_pub'], edge['node2_pub']]:
        self.node_stats[pubkey]['channels'] += 1
        self.node_stats[pubkey]['capacity'] += sat_to_btc(edge['capacity'])

    ## Forwarding events and routing channels.
    day = 24 * 60 * 60
    cmd = ('lncli fwdinghistory --max_events 50000 ' +
           '--start_time=%d --end_time=%d') % (time.time() - self.days * day,
                                               time.time() + day)
    self.fwd_events = json.loads(os.popen(cmd).read())['forwarding_events']
    # fwd_events: { 'amt_in',
    #               'amt_out',
    #               'chan_id_in',
    #               'chan_id_out',
    #               'fee',
    #               'fee_msat',
    #               'timestamp' }
    self.chan_id_to_routing_channel = {}
    for event in self.fwd_events:
      self.chan_id_to_routing_channel[event['chan_id_in']] = { 'amt_in': [],
          'amt_out': [], 'fee': [] }
      self.chan_id_to_routing_channel[event['chan_id_out']] = { 'amt_in': [],
          'amt_out': [], 'fee': [] }
    for event in self.fwd_events:
      self.chan_id_to_routing_channel[event['chan_id_in']]['amt_in'].append(
          int(event['amt_in']))
      self.chan_id_to_routing_channel[event['chan_id_out']]['amt_out'].append(
          int(event['amt_out']))
      # TODO: maybe use float(event['fee_msat']) / 1000.0
      self.chan_id_to_routing_channel[event['chan_id_out']]['fee'].append(
          int(event['fee']))

    ## Open channels.
    channels_info = json.loads(os.popen('lncli listchannels').read())
    self.channels = channels_info['channels']
    # channels: { 'commit_fee',
    #             'unsettled_balance',
    #             'fee_per_kw',
    #             'capacity',
    #             'remote_pubkey',
    #             'csv_delay',
    #             'num_updates',
    #             'commit_weight',
    #             'private',
    #             'remote_balance',
    #             'total_satoshis_sent',
    #             'pending_htlcs': [{ 'amount',
    #                                 'incoming',
    #                                 'expiration_height',
    #                                 'hash_lock' }],
    #             'chan_id',
    #             'active',
    #             'total_satoshis_received',
    #             'channel_point',
    #             'local_balance' }

    # Channel opening time (pickled, could be slow the first time called).
    try:
      channel_point_to_open_time = pickle.load(open('lnd_assistant.pkl', 'r'))
    except:
      channel_point_to_open_time = {}
    for ch in self.channels:
      if ch['channel_point'] not in channel_point_to_open_time:
        txid = ch['channel_point'][:ch['channel_point'].find(':')]
        bitcoind_cmd = 'bitcoin-cli getrawtransaction %s 1' % (txid)
        txinfo = json.loads(os.popen(bitcoind_cmd).read())
        channel_point_to_open_time[ch['channel_point']] = txinfo['time']
    pickle.dump(channel_point_to_open_time, open('lnd_assistant.pkl', 'w'))

    # Additional channel annotations.
    for ch in self.channels:
      ch['outgoing'] = self.outgoing_channel(ch)
      ch['local_ratio'] = float(ch['local_balance']) / float(ch['capacity'])
      ch['opened'] = channel_point_to_open_time[ch['channel_point']]
      ch['used'] = ( int(ch['total_satoshis_received']) +
                     int(ch['total_satoshis_sent']) > 0 )
      if ch['chan_id'] in self.chan_id_to_routing_channel:
        routing_channel = self.chan_id_to_routing_channel[ch['chan_id']]
        ch['fwd_events'] = ( len(routing_channel['amt_in']) +
                             len(routing_channel['amt_out']) )
      else:
        ch['fwd_events'] = 0
      ch['remote_alias'] = self.node_stats[ch['remote_pubkey']]['alias']

    self.chan_id_to_channel = { ch['chan_id'] : ch for ch in self.channels }
    self.remote_pubkey_to_chan_ids = defaultdict(list)
    for ch in self.channels:
      self.remote_pubkey_to_chan_ids[ch['remote_pubkey']].append(ch['chan_id'])

    ## Closed channels.
    closed_channels_info = json.loads(os.popen('lncli closedchannels').read())
    self.closed_channels = closed_channels_info['channels']
    # closed_channels: { 'capacity',
    #                    'chain_hash',
    #                    'chan_id',
    #                    'channel_point',
    #                    'close_height',
    #                    'close_type',
    #                    'closing_tx_hash',
    #                    'remote_pubkey',
    #                    'settled_balance',
    #                    'time_locked_balance' }
    # close_type: set(['COOPERATIVE_CLOSE',
    #                  'LOCAL_FORCE_CLOSE',
    #                  'REMOTE_FORCE_CLOSE',
    #                  'FUNDING_CANCELED',
    #                  'BREACH_CLOSE'])
    self.closed_chan_id_to_channel = { ch['chan_id'] : ch
                                       for ch in self.closed_channels }
    self.closed_channel_point_to_channel = { ch['channel_point'] : ch
                                              for ch in self.closed_channels }
    self.remote_pubkey_to_closed_channel_point = defaultdict(list)
    for ch in self.closed_channels:
      self.remote_pubkey_to_closed_channel_point[ch['remote_pubkey']].append(
          ch['channel_point'])

  def newly_opened_channels(self, days=-1):
    if days == -1:
      days = self.days
    threshold = time.time() - 24 * 60 * 60 * days
    channels = [ch for ch in self.channels if ch['opened'] > threshold]
    channels = sorted(channels, key=lambda ch: ch['opened'])
    return channels

  def newly_closed_channels(self, days=-1):
    if days == -1:
      days = self.days
    threshold = self.my_node_info['block_height'] - 144 * days
    channels = [ ch for ch in self.closed_channels
                 if ch['close_height'] > threshold ]
    channels = sorted(channels, key=lambda ch: ch['close_height'])
    return channels

