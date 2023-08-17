from flask import Flask, request
from binance.um_futures import UMFutures
from binance.lib.utils import config_logging
import logging
from binance.error import ClientError

live_api_key = 'yR7thAjvm3ew1dSp4eaUTlVD3CyArKKPjp95kAXW6NQmIYlSuO3SwVOU9OA5Ca4i'
live_api_secret = '5thfP47BW2udjxQcrEFop2RjSBzKGc71qdz43UrxOSW5Nilu8zVnpSTRPyxMT1ca'

test_api_key = 'fa04b7d881a6d9926f7afcc7c9890791b4a171e9016825f2525df7ebd54f54c9'
test_api_secret = '0fffbecdc98fb483d485c13bfbf8531e34b5bf3e5d8f86b45f14921affe44c08'

live_client = UMFutures(live_api_key, live_api_secret)
test_client = UMFutures(test_api_key, test_api_secret, base_url='https://testnet.binancefuture.com')

app = Flask(__name__)
start_time = datetime.now()  # Mark the time when the app starts

@app.route('/uptime9164', methods=['GET'])
def uptime9164():
    uptime = (datetime.now() - start_time) / 60
    return {
        "code": "success",
        "message": f"Server has been running for {uptime} minutes"
    }, 200

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    logging.info(f'Received alert: {data}')

    action = data.get('action')
    symbol = data.get('ticker')
    trade_amount = float(data.get('trade_amount', '0.001'))
    account_type = data.get('account_type', 'test')

    client = live_client if account_type == 'live' else test_client

    # Fetch current position
    current_positions = client.get_position_risk(symbol=symbol)
    logging.info(f'Current positions: {current_positions}')

    current_position = None

    for position in current_positions:
        if position['symbol'] == symbol:
            current_position = position
            break

    order_amt_to_close_position = 0
    if current_position:
        # Calculate order amount to close position
        order_amt_to_close_position = float(current_position['positionAmt'])

    # Determine if the existing position direction is opposite to the new order direction
    existing_position_opposite = (order_amt_to_close_position < 0 and action == 'buy') or (order_amt_to_close_position > 0 and action == 'sell')

    # Calculate the net order amount
    if existing_position_opposite:
        net_order_amount = trade_amount + abs(order_amt_to_close_position)
    else:
        net_order_amount = max(0, trade_amount - abs(order_amt_to_close_position))

    # Open new market order
    order_side = "BUY" if action == 'buy' else "SELL"
    try:
        client.new_order(symbol=symbol, side=order_side, type='MARKET', quantity=net_order_amount)
    except ClientError as e:
        # Log the error along with the symbol that caused it
        logging.error(f"Error when placing order for symbol '{symbol}': {e}")
        return {
            "code": "error",
            "message": f"Failed to place order for symbol '{symbol}': {e}"
        }, 500

    return {
        "code": "success",
        "message": "webhook received"
    }, 200
    

if __name__ == "__main__":
    app.run(port=5000)
