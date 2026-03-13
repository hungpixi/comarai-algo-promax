import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')
from sklearn.preprocessing import MinMaxScaler
import xgboost as xgb
import sys, os

# Copying SMC Features from the repo
def find_swing_points(df, lookback=5):
    highs = df['High'].values
    lows  = df['Low'].values
    n     = len(df)
    swing_highs = np.zeros(n, dtype=float)
    swing_lows  = np.zeros(n, dtype=float)

    for i in range(lookback, n - lookback):
        left_h  = highs[i - lookback:i]
        right_h = highs[i + 1:i + lookback + 1]
        if highs[i] > left_h.max() and highs[i] > right_h.max():
            swing_highs[i] = highs[i]

        left_l  = lows[i - lookback:i]
        right_l = lows[i + 1:i + lookback + 1]
        if lows[i] < left_l.min() and lows[i] < right_l.min():
            swing_lows[i] = lows[i]

    df = df.copy()
    df['SwingHigh'] = swing_highs
    df['SwingLow']  = swing_lows
    return df

def get_market_structure(df):
    structure = np.zeros(len(df))
    pivot_highs = df[df['SwingHigh'] > 0]['SwingHigh']
    pivot_lows  = df[df['SwingLow']  > 0]['SwingLow']

    ph_diff = pivot_highs.diff()
    pl_diff = pivot_lows.diff()

    for i in range(len(df)):
        ts = df.index[i]
        recent_ph = ph_diff[ph_diff.index < ts].tail(1)
        recent_pl = pl_diff[pl_diff.index < ts].tail(1)

        ph_up = (recent_ph > 0).any()   
        pl_up = (recent_pl > 0).any()   
        ph_dn = (recent_ph < 0).any()   
        pl_dn = (recent_pl < 0).any()   

        if ph_up and pl_up:
            structure[i] = 1   
        elif ph_dn and pl_dn:
            structure[i] = -1  

    df = df.copy()
    df['MS_Structure'] = structure
    return df

def find_order_blocks(df, min_move_atr=1.5):
    df = df.copy()
    atr14 = (df['High'] - df['Low']).rolling(14).mean()

    bull_ob_high = np.nan * np.ones(len(df))
    bull_ob_low  = np.nan * np.ones(len(df))
    bear_ob_high = np.nan * np.ones(len(df))
    bear_ob_low  = np.nan * np.ones(len(df))

    for i in range(1, len(df) - 1):
        next_range = df['High'].iloc[i] - df['Low'].iloc[i]
        threshold  = min_move_atr * (atr14.iloc[i] if not np.isnan(atr14.iloc[i]) else 1)

        is_bullish_impulse = (df['Close'].iloc[i] > df['Open'].iloc[i] and next_range >= threshold)
        if is_bullish_impulse and df['Close'].iloc[i-1] < df['Open'].iloc[i-1]:
            bull_ob_high[i-1] = df['Open'].iloc[i-1]
            bull_ob_low[i-1]  = df['Low'].iloc[i-1]

        is_bearish_impulse = (df['Close'].iloc[i] < df['Open'].iloc[i] and next_range >= threshold)
        if is_bearish_impulse and df['Close'].iloc[i-1] > df['Open'].iloc[i-1]:
            bear_ob_high[i-1] = df['High'].iloc[i-1]
            bear_ob_low[i-1]  = df['Close'].iloc[i-1]

    df['BullOB_High'] = bull_ob_high
    df['BullOB_Low']  = bull_ob_low
    df['BearOB_High'] = bear_ob_high
    df['BearOB_Low']  = bear_ob_low
    return df

def find_fair_value_gaps(df):
    df = df.copy()
    n = len(df)
    bull_fvg = np.zeros(n)
    bear_fvg = np.zeros(n)

    for i in range(1, n - 1):
        gap_up   = df['Low'].iloc[i+1]  - df['High'].iloc[i-1]
        gap_down = df['Low'].iloc[i-1]  - df['High'].iloc[i+1]
        if gap_up > 0:
            bull_fvg[i]      = 1
        if gap_down > 0:
            bear_fvg[i]      = 1

    df['BullFVG']      = bull_fvg
    df['BearFVG']      = bear_fvg
    return df

def add_distance_features(df, lookback=50):
    df = df.copy()
    atr14 = (df['High'] - df['Low']).rolling(14).mean().values
    close = df['Close'].values

    dist_sh    = np.full(len(df), np.nan)  
    dist_sl    = np.full(len(df), np.nan)  
    dist_bull_ob = np.full(len(df), np.nan)
    dist_bear_ob = np.full(len(df), np.nan)
    near_fvg   = np.zeros(len(df))

    for i in range(lookback, len(df)):
        window = df.iloc[i - lookback:i]
        atr    = atr14[i] if not np.isnan(atr14[i]) else 1

        sh_vals = window['SwingHigh'][window['SwingHigh'] > 0]
        sl_vals = window['SwingLow'][window['SwingLow'] > 0]
        if not sh_vals.empty:
            dist_sh[i] = (sh_vals.iloc[-1] - close[i]) / atr
        if not sl_vals.empty:
            dist_sl[i] = (close[i] - sl_vals.iloc[-1]) / atr

        bull_obs = window['BullOB_High'].dropna()
        bear_obs = window['BearOB_Low'].dropna()
        if not bull_obs.empty:
            dist_bull_ob[i] = (close[i] - bull_obs.iloc[-1]) / atr
        if not bear_obs.empty:
            dist_bear_ob[i] = (bear_obs.iloc[-1] - close[i]) / atr

        recent = window.tail(10)
        if recent['BullFVG'].any() or recent['BearFVG'].any():
            near_fvg[i] = 1

    df['Dist_SwingHigh']  = dist_sh
    df['Dist_SwingLow']   = dist_sl
    df['Dist_BullOB']     = dist_bull_ob
    df['Dist_BearOB']     = dist_bear_ob
    df['Near_FVG']        = near_fvg
    return df

def calculate_all_smc(df, swing_lookback=5, ob_min_atr=1.5, dist_lookback=50):
    df = find_swing_points(df, lookback=swing_lookback)
    df = get_market_structure(df)
    df = find_order_blocks(df, min_move_atr=ob_min_atr)
    df = find_fair_value_gaps(df)
    df = add_distance_features(df, lookback=dist_lookback)
    return df

def add_base_features(df):
    df = df.copy()
    df['Body']       = df['Close'] - df['Open']
    df['Body_Pct']   = (df['Body'] / df['Open']) * 100
    df['Range']      = df['High'] - df['Low']
    df['Upper_Wick'] = df['High'] - df[['Open','Close']].max(axis=1)
    df['Lower_Wick'] = df[['Open','Close']].min(axis=1) - df['Low']
    df['ATR_14']     = df['Range'].rolling(14).mean()
    df['BodyATR']    = df['Body'].abs() / df['ATR_14']
    df['RangeATR']   = df['Range'] / df['ATR_14']
    delta            = df['Close'].diff()
    g = (delta.where(delta > 0, 0)).rolling(14).mean()
    l = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI_14']     = 100 - (100 / (1 + g / l))
    df['ROC_5']      = df['Close'].pct_change(5) * 100
    df['ROC_20']     = df['Close'].pct_change(20) * 100
    df['Vol_Ratio']  = df['Volume'] / df['Volume'].rolling(20).mean()
    df['SMA_50']     = df['Close'].rolling(50).mean()
    df['SMA_200']    = df['Close'].rolling(200).mean()
    df['Trend_Up']   = np.where(df['SMA_50'] > df['SMA_200'], 1, -1)
    df['Hour']       = df.index.hour
    df['Is_Active']  = np.where(((df['Hour'] >= 7) & (df['Hour'] < 21)), 1, 0)
    
    df['Next_Body']  = df['Close'].shift(-1) - df['Open'].shift(-1)
    df['Target']     = np.where(df['Next_Body'] > 0, 1, 0)
    return df

XGB_FEATURES  = [
    'Body_Pct', 'Upper_Wick', 'Lower_Wick', 'BodyATR', 'RangeATR',
    'RSI_14', 'ROC_5', 'ROC_20', 'Trend_Up', 'Vol_Ratio',
    'MS_Structure', 'Near_FVG', 'BullFVG', 'BearFVG',
    'Dist_SwingHigh', 'Dist_SwingLow', 'Dist_BullOB', 'Dist_BearOB',
]

def train_xgboost(df):
    df2 = df.replace([np.inf, -np.inf], np.nan).dropna(subset=XGB_FEATURES + ['Target'])
    df2.reset_index(drop=True, inplace=True)

    split = int(len(df2) * 0.8)
    X_train = df2[XGB_FEATURES].iloc[:split]
    y_train = df2['Target'].iloc[:split]
    X_test  = df2[XGB_FEATURES].iloc[split:]
    y_test  = df2['Target'].iloc[split:]

    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=4,              
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=10,      
        eval_metric='logloss',
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    prob_test = model.predict_proba(X_test)[:, 1]
    
    test_df = df2.iloc[split:].copy()
    test_df['Prob_Up'] = prob_test
    return model, test_df

def get_structural_sl(test_df, sig_idx, direction, lookback=20):
    start = max(0, sig_idx - lookback)
    window = test_df.iloc[start:sig_idx]

    if direction == 'LONG':
        sl_candidates = window['SwingLow'][window['SwingLow'] > 0]
        if not sl_candidates.empty:
            return sl_candidates.iloc[-1] * 0.9999 
        return window['Low'].min() * 0.9999
    else:
        sl_candidates = window['SwingHigh'][window['SwingHigh'] > 0]
        if not sl_candidates.empty:
            return sl_candidates.iloc[-1] * 1.0001
        return window['High'].max() * 1.0001

def run_backtest_xgboost(file_path):
    print(f"Loading data from {file_path}...")
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return
        
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    df.set_index('Datetime', inplace=True)
    df.sort_index(inplace=True)

    print("[*] Base Features...")
    df = add_base_features(df)
    print("[*] SMC Feature Engineering...")
    df = calculate_all_smc(df, swing_lookback=5, dist_lookback=50)
    print("[*] Train XGBoost...")
    model, test_df = train_xgboost(df)

    CONFIDENCE = 0.60 
    MAX_BARS_HOLD = 30       

    print(f"[*] Simulating trades on test set...")
    wins = losses = 0
    results = []

    i = 0
    test_df = test_df.reset_index(drop=True)
    while i < len(test_df) - MAX_BARS_HOLD:
        row = test_df.iloc[i]

        if row['Is_Active'] == 0:
            i += 1; continue

        if row['Prob_Up'] >= CONFIDENCE and row['Trend_Up'] == 1:
            direction = 'LONG'
        elif row['Prob_Up'] <= 1 - CONFIDENCE and row['Trend_Up'] == -1:
            direction = 'SHORT'
        else:
            i += 1; continue

        entry = row['Open']
        sl    = get_structural_sl(test_df, i, direction, lookback=20)
        sl_dist = abs(entry - sl)

        if sl_dist < 2.0 or sl_dist > 5.0:
            i += 1; continue

        rr = 1.5
        tp = entry + sl_dist * rr if direction == 'LONG' else entry - sl_dist * rr

        outcome   = 'OPEN'
        bars_held = 0
        for j in range(i + 1, min(i + 1 + MAX_BARS_HOLD, len(test_df))):
            bar = test_df.iloc[j]
            bars_held = j - i
            if direction == 'LONG':
                if bar['Low']  <= sl: outcome = 'LOSS'; break
                if bar['High'] >= tp: outcome = 'WIN';  break
            else:
                if bar['High'] >= sl: outcome = 'LOSS'; break
                if bar['Low']  <= tp: outcome = 'WIN';  break

        if outcome == 'OPEN': outcome = 'LOSS'
        if outcome == 'WIN': wins += 1
        else: losses += 1

        results.append({'Dir': direction, 'Entry': entry, 'SL': sl, 'TP': tp,
                        'Outcome': outcome})

        i += (bars_held or 1) + 1

    total = wins + losses
    if total == 0:
        print("[-] Không có lệnh nào.")
        return

    wr = wins / total
    ev = wr * rr - (1 - wr)
    print(f"\n{'='*60}")
    print(f"📊 XGBoost + SMC Signal Engine — XAUUSD M15 (Test Data)")
    print(f"{'='*60}")
    print(f"  Tổng lệnh : {total} | Win: {wins} | Loss: {losses}")
    print(f"  Winrate   : {wr*100:.1f}%")
    print(f"  R:R       : 1:{rr}")
    print(f"  EV/lệnh   : {ev:+.3f}R  {'✅ EV DƯƠNG!' if ev > 0 else '❌ EV âm'}")
    print(f"{'='*60}")

if __name__ == "__main__":
    run_backtest_xgboost(r"d:\Cá nhân\Trading\Indicator\XAUUSD_M15.csv")
