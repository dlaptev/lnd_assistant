from __future__ import print_function
import argparse
import os
from lnd_assistant import LndAssistant

def local_ratio_to_fees(local_ratio, args):
  if local_ratio <= args.left_cap_local_ratio:
    return (args.max_base_fee_msat, args.max_fee_rate)
  if local_ratio >= args.right_cap_local_ratio:
    return (args.min_base_fee_msat, args.min_fee_rate)
  capped_ratio = ((local_ratio - args.left_cap_local_ratio) /
                  (args.right_cap_local_ratio - args.left_cap_local_ratio))
  base_fee = round(args.max_base_fee_msat -
      (args.max_base_fee_msat - args.min_base_fee_msat) * capped_ratio)
  fee_rate = round(args.max_fee_rate -
      (args.max_fee_rate - args.min_fee_rate) * capped_ratio, 6)
  return (base_fee, fee_rate)


if __name__ == '__main__':
  parser = argparse.ArgumentParser(
      description='Set fees inverse proportional to local channel balance.')
  parser.add_argument('--min_base_fee_msat', type = int, default = 0,
      help = 'Minimal base fee (absolute fee) in milli-satoshis (default: 0).')
  parser.add_argument('--max_base_fee_msat', type = int, default = 500,
      help = 'Maximum base fee in milli-satoshis (default: 500).')
  parser.add_argument('--min_fee_rate', type = float, default = 0.000001,
      help = 'Minimal fee rate (relative fee) (default: 0.000001).')
  parser.add_argument('--max_fee_rate', type = float, default = 0.000005,
      help = 'Maximum fee rate (default: 0.000010).')
  parser.add_argument('--left_cap_local_ratio', type = float, default = 0.0,
      help = 'Keep max fees below this local balance ratio (default: 0.0).')
  parser.add_argument('--right_cap_local_ratio', type = float, default = 0.6,
      help = 'Keep min fees above this local balance ratio (default: 0.6).')
  args = parser.parse_args()

  print('    chan_id / local_ratio: base_fee_msat, fee_rate')
  for ch in LndAssistant.get_open_channels():
    base_fee, fee_rate = local_ratio_to_fees(ch['local_ratio'], args)
    print('%18s / %.2f: %13d, %.6f' % (ch['chan_id'], ch['local_ratio'],
                                      base_fee, fee_rate))
    cmd = ('lncli updatechanpolicy --base_fee_msat=%d --fee_rate=%.6f ' +
           '--time_lock_delta=144 --chan_point=%s') % (base_fee, fee_rate,
                                                       ch['channel_point'])
    _ = os.popen(cmd).read()
