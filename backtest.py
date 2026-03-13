import pandas as pd
import numpy as np

def calculate_atr(df, period=14):
    tr1 = df['High'] - df['Low']
    tr2 = (df['High'] - df['Close'].shift()).abs()
    tr3 = (df['Low'] - df['Close'].shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def run_backtest(file_path):
    print(f"Loading data from {file_path}...")
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return
        
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    df.set_index('Datetime', inplace=True)
    df.sort_index(inplace=True)

    print("Calculating indicators...")
    # 1. Trend Filter : EMA 200
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    
    # 2. Trigger : RSI & CCI (ML Proxy)
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    sma_tp = tp.rolling(20).mean()
    mad = tp.rolling(20).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
    df['CCI'] = (tp - sma_tp) / (0.015 * mad)
    
    df['ATR'] = calculate_atr(df, 14)

    # 3. Order Block Proxy: Price returning to recent extreme zones
    df['Local_Low_20'] = df['Low'].rolling(20).min()
    df['Local_High_20'] = df['High'].rolling(20).max()
    
    # Drop NaNs
    df.dropna(inplace=True)

    # Trading Logic
    # Buy when: Uptrend AND RSI oversold AND Price in discount zone (near local low)
    buy_condition = (
        (df['Close'] > df['EMA200']) & 
        (df['RSI'] < 40) & 
        (df['Low'] <= df['Local_Low_20'] * 1.001) # Within 0.1% of 20-bar low
    )

    # Sell when: Downtrend AND RSI overbought AND Price in premium zone (near local high)
    sell_condition = (
        (df['Close'] < df['EMA200']) & 
        (df['RSI'] > 60) & 
        (df['High'] >= df['Local_High_20'] * 0.999) # Within 0.1% of 20-bar high
    )

    print("Simulating trades...")
    trades = []
    in_trade = False
    entry_price = 0
    trade_type = 0 # 1 for Buy, -1 for Sell
    entry_idx = None
    sl = 0
    tp_price = 0

    for idx, row in df.iterrows():
        if not in_trade:
            if buy_condition.loc[idx]:
                in_trade = True
                entry_price = row['Close']
                trade_type = 1
                entry_idx = idx
                sl = entry_price - (1.5 * row['ATR'])
                tp_price = entry_price + (3.0 * row['ATR'])
            elif sell_condition.loc[idx]:
                in_trade = True
                entry_price = row['Close']
                trade_type = -1
                entry_idx = idx
                sl = entry_price + (1.5 * row['ATR'])
                tp_price = entry_price - (3.0 * row['ATR'])
        else:
            # Check exit
            if trade_type == 1:
                if row['Low'] <= sl: # Stop Loss
                    trades.append({'Type': 'Buy', 'Entry': entry_price, 'Exit': sl, 'Profit': sl - entry_price, 'Duration': idx - entry_idx})
                    in_trade = False
                elif row['High'] >= tp_price: # Take Profit
                    trades.append({'Type': 'Buy', 'Entry': entry_price, 'Exit': tp_price, 'Profit': tp_price - entry_price, 'Duration': idx - entry_idx})
                    in_trade = False
            elif trade_type == -1:
                if row['High'] >= sl: # Stop Loss
                    trades.append({'Type': 'Sell', 'Entry': entry_price, 'Exit': sl, 'Profit': entry_price - sl, 'Duration': idx - entry_idx})
                    in_trade = False
                elif row['Low'] <= tp_price: # Take Profit
                    trades.append({'Type': 'Sell', 'Entry': entry_price, 'Exit': tp_price, 'Profit': entry_price - tp_price, 'Duration': idx - entry_idx})
                    in_trade = False

    trade_df = pd.DataFrame(trades)
    
    if len(trade_df) > 0:
        wins = trade_df[trade_df['Profit'] > 0]
        losses = trade_df[trade_df['Profit'] <= 0]
        winrate = len(wins) / len(trade_df) * 100
        avg_win = wins['Profit'].mean() if len(wins) > 0 else 0
        avg_loss = losses['Profit'].mean() if len(losses) > 0 else 0
        ev = (winrate / 100 * avg_win) + ((100 - winrate) / 100 * avg_loss)
        
        print("\n=== BACKTEST RESULTS ===")
        print(f"Total Trades: {len(trade_df)}")
        print(f"Winrate: {winrate:.2f}%")
        print(f"Average Win: ${avg_win:.2f}")
        print(f"Average Loss: ${avg_loss:.2f}")
        print(f"Expected Value (EV): ${ev:.2f} per trade")
        print(f"Net Profit (Points): {trade_df['Profit'].sum():.2f}")
    else:
        print("No trades taken with given conditions.")

if __name__ == "__main__":
    run_backtest(r"d:\Cá nhân\Trading\Indicator\XAUUSD_M15.csv")
