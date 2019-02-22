import argparse
from lnd_assistant import LndAssistant
import lnd_assistant_printer as Printer


if __name__ == '__main__':
  parser = argparse.ArgumentParser(
      description='Compare and select routes before paying an invoice.')
  parser.add_argument('payreq',
                      type=str,
                      help='Payment request (a.k.a. lightning invoice).')
  parser.add_argument('--amt',
                      type=int,
                      default=1,
                      help='Amount in satoshi (only used if payreq amt==0).')
  parser.add_argument('--max_routes',
                      type=int,
                      default=10,
                      help='How many routes to show (default: 10).')
  args = parser.parse_args()

  lnda = LndAssistant()
  routes_annotated = lnda.possible_routes(args.payreq, amt=args.amt,
                                          max_routes=args.max_routes)
  Printer.routes_annotated_table(routes_annotated)

  TIMES_TO_REPEAT = 5
  for i in range(TIMES_TO_REPEAT):
    options = raw_input('Enter comma-separated routes # (or ctrl+c to exit): ')
    routes = []
    for option in options.split(','):
      routes.append(routes_annotated[int(option)]['route'])
    if LndAssistant.send_to_routes(args.payreq, routes):
      break  # Success.
    elif i < TIMES_TO_REPEAT - 1:
      print('Retrying (%d / %d)...' % (i + 2, TIMES_TO_REPEAT))
