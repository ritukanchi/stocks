import os
import pandas as pd
from upstox_api.api import Upstox, ScripType, TransactionType
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('API_KEY')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')

def get_option_chain_data(instrument_name: str, expiry_date: str, side: str) -> pd.DataFrame:
    upstox = Upstox(API_KEY, ACCESS_TOKEN)
    try:
        option_chain = upstox.get_option_chain(instrument_name, expiry_date)
        option_data = []
        if side == 'PE':
            option_data = [
                {
                    'instrument_name': instrument_name,
                    'strike_price': contract['strike'],
                    'side': 'PE',
                    'bid/ask': contract['PE']['bid_price']
                }
                for contract in option_chain['options'] if contract['PE']['bid_price'] is not None
            ]
        elif side == 'CE':
            option_data = [
                {
                    'instrument_name': instrument_name,
                    'strike_price': contract['strike'],
                    'side': 'CE',
                    'bid/ask': contract['CE']['ask_price']
                }
                for contract in option_chain['options'] if contract['CE']['ask_price'] is not None
            ]
        else:
            raise ValueError("Invalid side. Use 'PE' for Put and 'CE' for Call.")

        return pd.DataFrame(option_data)
    except Exception as e:
        print(f"Error fetching option chain data: {e}")
        return pd.DataFrame()

def calculate_margin_and_premium(data: pd.DataFrame) -> pd.DataFrame:
    upstox = Upstox(API_KEY, ACCESS_TOKEN)
    data['margin_required'] = 0
    data['premium_earned'] = 0

    for index, row in data.iterrows():
        try:
            margin = upstox.get_margin_for_order(
                ScripType.OPTION,
                row['instrument_name'],
                row['strike_price'],
                row['side'],
                TransactionType.SELL,
                1
            )
            data.at[index, 'margin_required'] = margin

            lot_size = 75 if row['instrument_name'] == 'NIFTY' else 25
            premium = row['bid/ask'] * lot_size
            data.at[index, 'premium_earned'] = premium
        except Exception as e:
            print(f"Error calculating margin and premium for {row['instrument_name']} {row['strike_price']} {row['side']}: {e}")

    return data

# Example usage:
if __name__ == "__main__":
    option_data = get_option_chain_data('NIFTY', '2023-12-31', 'CE')
    result = calculate_margin_and_premium(option_data)
    print(result)