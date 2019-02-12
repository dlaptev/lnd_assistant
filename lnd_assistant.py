from collections import defaultdict
from pprint import pprint
import json
import os
import pickle
import time

def sat_to_btc(satoshi_as_string):
  return int(satoshi_as_string) * 1e-8


class LndAssistant:
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
    self.chan_id_to_chan_fwd_events = {}
    for event in self.fwd_events:
      self.chan_id_to_chan_fwd_events[event['chan_id_in']] = { 'amt_in': [],
          'amt_out': [], 'fee': [] }
      self.chan_id_to_chan_fwd_events[event['chan_id_out']] = { 'amt_in': [],
          'amt_out': [], 'fee': [] }
    for event in self.fwd_events:
      self.chan_id_to_chan_fwd_events[event['chan_id_in']]['amt_in'].append(
          int(event['amt_in']))
      self.chan_id_to_chan_fwd_events[event['chan_id_out']]['amt_out'].append(
          int(event['amt_out']))
      # TODO: maybe use float(event['fee_msat']) / 1000.0
      self.chan_id_to_chan_fwd_events[event['chan_id_out']]['fee'].append(
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

    ## Channel opening time (pickled, could be slow the first time called).
    def update_txid_to_time(txid, txid_to_time):
      if txid not in txid_to_time:
        bitcoind_cmd = 'bitcoin-cli getrawtransaction %s 1' % (txid)
        txinfo = json.loads(os.popen(bitcoind_cmd).read())
        txid_to_time[txid] = txinfo['time']

    try:
      txid_to_time = pickle.load(open('lnd_assistant_txid_to_time.pkl', 'r'))
    except:
      txid_to_time = {}
    for ch in self.channels:
      txid = ch['channel_point'][:ch['channel_point'].find(':')]
      update_txid_to_time(txid, txid_to_time)
    for ch in self.closed_channels:
      if ch['close_type'] == 'FUNDING_CANCELED':
        continue  # These transactions are not recorded.
      txid = ch['channel_point'][:ch['channel_point'].find(':')]
      update_txid_to_time(txid, txid_to_time)
      txid = ch['closing_tx_hash']
      update_txid_to_time(txid, txid_to_time)
    pickle.dump(txid_to_time, open('lnd_assistant_txid_to_time.pkl', 'w'))

    ## Transactions.
    transactions_info = json.loads(os.popen('lncli listchaintxns').read())
    self.transactions = transactions_info['transactions']
    self.tx_hash_to_transaction = { t['tx_hash'] : t
                                    for t in self.transactions }

    ## Additional annotations for open channels.
    def txid_by_me(txid, tx_hash_to_transaction):
      return (txid in tx_hash_to_transaction and
              tx_hash_to_transaction[txid]['amount'] != '0')

    for ch in self.channels:
      txid = ch['channel_point'][:ch['channel_point'].find(':')]
      ch['opened_time'] = txid_to_time[txid]
      ch['opened_by_me'] = txid_by_me(txid, self.tx_hash_to_transaction)
      ch['local_ratio'] = float(ch['local_balance']) / float(ch['capacity'])
      ch['used'] = ( int(ch['total_satoshis_received']) +
                     int(ch['total_satoshis_sent']) > 0 )
      if ch['chan_id'] in self.chan_id_to_chan_fwd_events:
        chan_fwd_events = self.chan_id_to_chan_fwd_events[ch['chan_id']]
        ch['fwd_events'] = ( len(chan_fwd_events['amt_in']) +
                             len(chan_fwd_events['amt_out']) )
      else:
        ch['fwd_events'] = 0
      ch['remote_alias'] = self.node_stats[ch['remote_pubkey']]['alias']

    ## Additional annotations for closed channels.
    for ch in self.closed_channels:
      if ch['close_type'] != 'FUNDING_CANCELED':
        txid = ch['channel_point'][:ch['channel_point'].find(':')]
        ch['opened_time'] = txid_to_time[txid]
        ch['closed_time'] = txid_to_time[ch['closing_tx_hash']]
        ch['channel_age'] = ch['closed_time'] - ch['opened_time']
        ch['opened_by_me'] = txid_by_me(txid, self.tx_hash_to_transaction)
        ch['closed_by_me'] = txid_by_me(ch['closing_tx_hash'],
                                        self.tx_hash_to_transaction)
      else:
        ch['opened_time'] = 0
        ch['closed_time'] = 0
        ch['channel_age'] = 0
      if ch['chan_id'] in self.chan_id_to_chan_fwd_events:
        chan_fwd_events = self.chan_id_to_chan_fwd_events[ch['chan_id']]
        ch['fwd_events'] = ( len(chan_fwd_events['amt_in']) +
                             len(chan_fwd_events['amt_out']) )
      else:
        ch['fwd_events'] = 0
      if ch['remote_pubkey'] in self.node_stats:
        ch['remote_alias'] = self.node_stats[ch['remote_pubkey']]['alias']
      else:
        ch['remote_alias'] = ch['remote_pubkey'][:30] + '...'

    ## Additional data structures for easier lookups.
    self.chan_id_to_channel = { ch['chan_id'] : ch for ch in self.channels }
    self.remote_pubkey_to_chan_ids = defaultdict(list)
    for ch in self.channels:
      self.remote_pubkey_to_chan_ids[ch['remote_pubkey']].append(ch['chan_id'])

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
    channels = [ch for ch in self.channels if ch['opened_time'] > threshold]
    channels = sorted(channels, key=lambda ch: ch['opened_time'], reverse=True)
    return channels

  def newly_closed_channels(self, days=-1):
    if days == -1:
      days = self.days
    threshold = time.time() - 24 * 60 * 60 * days
    channels = [ ch for ch in self.closed_channels
                 if ch['closed_time'] > threshold ]
    channels = sorted(channels, key=lambda ch: ch['closed_time'], reverse=True)
    return channels

  def routing_channels(self, days=-1):
    if days == -1:
      days = self.days
    channels = []
    for chan_id in self.chan_id_to_chan_fwd_events.keys():
      if chan_id in self.chan_id_to_channel:
        ch = self.chan_id_to_channel[chan_id]
      elif chan_id in self.closed_chan_id_to_channel:
        ch = self.closed_chan_id_to_channel[chan_id]
        ch['local_ratio'] = '? (closed)'
      else:
        ch = { 'chan_id': chan_id, 'remote_alias': '?', 'opened_by_me': '?',
               'capacity': '?', 'local_ratio': '?' }
      chan_fwd_events = self.chan_id_to_chan_fwd_events[chan_id]
      ch['fwd_events_in'] = len(chan_fwd_events['amt_in'])
      ch['fwd_events_out'] = len(chan_fwd_events['amt_out'])
      ch['fwd_events'] = ch['fwd_events_in'] + ch['fwd_events_out']
      if ch['fwd_events_in'] > 0:
        ch['avg_amt_in'] = int( sum(chan_fwd_events['amt_in']) /
                                len(chan_fwd_events['amt_in']) )
      else:
        ch['avg_amt_in'] = 0
      if ch['fwd_events_out'] > 0:
        ch['avg_amt_out'] = int( sum(chan_fwd_events['amt_out']) /
                                 len(chan_fwd_events['amt_out']) )
      else:
        ch['avg_amt_out'] = 0
      ch['fees'] = sum(chan_fwd_events['fee'])
      channels.append(ch)
    channels = sorted(channels, key=lambda ch: ch['fwd_events'], reverse=True)
    return channels

  def peers_with_multiple_channels(self):
    peers = []
    for pubkey in self.remote_pubkey_to_chan_ids.keys():
      if len(self.remote_pubkey_to_chan_ids[pubkey]) > 1:
        channels = []
        for chan_id in self.remote_pubkey_to_chan_ids[pubkey]:
          channels.append(self.chan_id_to_channel[chan_id])
        channels = sorted(channels, key=lambda ch: float(ch['capacity']),
                          reverse=True)
        peers.append(channels)
    peers = sorted(peers, key=lambda x: len(x), reverse=True)
    return peers

  def peers_exhausting_inbound_capacity(self):
    peers = []
    for pubkey in self.remote_pubkey_to_chan_ids.keys():
      total_capacity = 0
      total_local_balance = 0
      total_satoshis_sent = 0
      total_satoshis_received = 0
      fwd_events = 0
      for chan_id in self.remote_pubkey_to_chan_ids[pubkey]:
        ch = self.chan_id_to_channel[chan_id]
        total_capacity += int(ch['capacity'])
        total_local_balance += int(ch['local_balance'])
        total_satoshis_sent += int(ch['total_satoshis_sent'])
        total_satoshis_received += int(ch['total_satoshis_received'])
        fwd_events += int(ch['fwd_events'])
      if total_satoshis_sent > 0 and total_local_balance < total_capacity / 3:
        peers.append({
            'remote_pubkey': pubkey,
            'alias': self.node_stats[pubkey]['alias'],
            'n_channels': len(self.remote_pubkey_to_chan_ids[pubkey]),
            'total_capacity': total_capacity,
            'total_local_ratio': float(total_local_balance) / total_capacity,
            'total_satoshis_sent': total_satoshis_sent,
            'total_satoshis_received': total_satoshis_received,
            'fwd_events': fwd_events,
            })
    peers = sorted(peers, key=lambda p: p['total_local_ratio'])
    return peers
