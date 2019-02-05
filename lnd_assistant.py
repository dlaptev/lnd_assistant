from __future__ import print_function
from collections import defaultdict
import json
import os
import time


def outgoing_channel(ch):
  # TODO: can probably be done for closed channels as well through
  #       settled_balance and time_locked_balance.
  return ((float(ch['local_balance']) > 0 and
           float(ch['total_satoshis_received']) == 0) or
          (float(ch['total_satoshis_sent']) >
           float(ch['total_satoshis_received'])))


def BTC(satoshi_as_string):
  return int(satoshi_as_string) * 1e-8


def format_satoshi(satoshi_as_string):
  if type(satoshi_as_string) == int:
    satoshi_as_string = str(satoshi_as_string)
  temp = []
  for i in range(1, len(satoshi_as_string) + 1):
    temp.append(satoshi_as_string[-i])
    if i % 3 == 0 and i != len(satoshi_as_string):
      temp.append('\'')
  return ''.join(temp[::-1])


class LndToolkit:

  def __init__(self):
    if len(os.popen('lncli walletbalance').read()) == 0:
      raise PermissionError('lncli is locked or does not exist.')

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
        self.node_stats[pubkey]['capacity'] += BTC(edge['capacity'])

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
    for ch in self.channels:
      ch['outgoing'] = outgoing_channel(ch)
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
    self.closed_channel_points_to_channel = { ch['channel_points'] : ch
                                              for ch in self.closed_channels }
    self.remote_pubkey_to_closed_channel_points = defaultdict(list)
    for ch in self.closed_channels:
      self.remote_pubkey_to_closed_channel_points[ch['remote_pubkey']].append(
          ch['channel_point'])

