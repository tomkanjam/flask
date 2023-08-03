from flask import Flask, request
from binance.um_futures import UMFutures
from binance.lib.utils import config_logging
import logging

api_key = 'fa04b7d881a6d9926f7afcc7c9890791b4a171e9016825f2525df7ebd54f54c9'
api_secret = '0fffbecdc98fb483d485c13bfbf8531e34b5bf3e5d8f86b45f14921affe44c08'

client = UMFutures(api_key, api_secret, base_url='https://testnet.binancefuture.com')

app = Flask(__name__)

TRADE_AMOUNT = .001

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    action = data.get('strategy.order.action')
    symbol = data.get('ticker')

    # Fetch current position
    current_positions = client.get_position_risk(symbol=symbol)
    logging.info(f'Current positions: {current_positions}')

    current_position = None

    for position in current_positions:
        if position['symbol'] == symbol:
            current_position = position
            break
    
    if current_position:
        # Calculate order amount to close position
        order_amt_to_close_position = float(current_position['positionAmt'])

        if order_amt_to_close_position != 0:
            # Create a new market order in opposite direction to close position
            order_side = "BUY" if order_amt_to_close_position < 0 else "SELL"
            client.new_order(symbol=symbol, side=order_side, 
                         type='MARKET',
                         quantity=abs(order_amt_to_close_position))

    # Open new market order
    order_side = "BUY" if action == 'buy' else "SELL"
    client.new_order(symbol=symbol, side=order_side, type='MARKET', 
                 quantity=TRADE_AMOUNT)

    return {
        "code": "success",
        "message": "webhook received"
    }, 200

if __name__ == "__main__":
    app.run(port=5000)
