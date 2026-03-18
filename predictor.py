import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

def predict_future_returns(returns, days=30):
    """
    Predicts future N-day returns using a Linear Regression model 
    """
    predictions = {}
    
    for coin in returns.columns:
        # Create a temporary dataframe 
        df_coin = pd.DataFrame(returns[coin].copy())
        df_coin.columns = ['daily_return']
        
        
        # Claculates how the coin performed over the last 1, 3, 7 days to capture momentum patterns
        df_coin['Lag_1'] = df_coin['daily_return'].shift(1)
        df_coin['Lag_3'] = (1 + df_coin['daily_return']).rolling(window=3).apply(np.prod, raw=True) - 1

        df_coin['Lag_7'] = (1 + df_coin['daily_return']).rolling(window=7).apply(np.prod, raw=True) - 1
        
       #Calculates the actual return that we want the model to predict
        future_return = (1 + df_coin['daily_return']).rolling(window=days).apply(np.prod, raw=True) - 1
        df_coin['Target'] = future_return.shift(-days)
        latest_features = df_coin.iloc[-1][['Lag_1', 'Lag_3', 'Lag_7']].to_frame().T
        train_df = df_coin.dropna()
        
        # Ensure we have enough historical data to train
        if len(train_df) < 10:
            print(f"Not enough data to train model for {coin}. Defaulting to 0%.")
            predictions[coin] = 0.0
            continue
            
        X_train = train_df[['Lag_1', 'Lag_3', 'Lag_7']]
        y_train = train_df['Target']
        
        #Train & Predict
        model = LinearRegression()
        model.fit(X_train, y_train)
        # Predict the future return
        predicted_return = model.predict(latest_features)[0] * 100
        
        predictions[coin] = round(predicted_return, 2)
        
    return predictions