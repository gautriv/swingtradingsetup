"""
Stock data analyzer module for the Swing Trading application.
Contains functions for fetching stock data and calculating technical indicators.
"""

import pandas as pd
import yfinance as yf
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_stock_data(symbol: str, max_retries: int = 3, retry_delay: float = 1.0) -> Optional[pd.DataFrame]:
    """
    Download 1 year of daily stock data for a given symbol using yfinance with retry logic.
    
    Args:
        symbol (str): Stock symbol (e.g., 'RELIANCE.NS')
        max_retries (int): Maximum number of retry attempts (default: 3)
        retry_delay (float): Delay between retries in seconds (default: 1.0)
        
    Returns:
        pd.DataFrame: Stock data with OHLCV columns, or None if failed
        
    Raises:
        None: All exceptions are caught and logged
    """
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                logger.info(f"Retry {attempt}/{max_retries-1} for symbol: {symbol}")
                time.sleep(retry_delay)
            else:
                logger.info(f"Fetching stock data for symbol: {symbol}")
            
            # Calculate date range (1 year from today)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            # Create yfinance Ticker object
            ticker = yf.Ticker(symbol)
            
            # First, try to validate if the symbol exists by getting basic info
            try:
                info = ticker.info
                if not info or info.get('symbol') is None:
                    logger.warning(f"Symbol {symbol} may not exist or be delisted")
                    # Don't retry for non-existent symbols
                    return None
            except Exception as info_error:
                logger.debug(f"Could not fetch info for {symbol}: {str(info_error)}")
                # Continue with data fetch attempt
            
            # Download historical data
            data = ticker.history(
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                interval='1d',
                auto_adjust=True,  # Automatically adjust for splits and dividends
                prepost=False      # Don't include pre/post market data
            )
            
            # Check if data is empty
            if data.empty:
                logger.warning(f"No data returned for symbol: {symbol} (attempt {attempt + 1})")
                if attempt == max_retries - 1:
                    logger.error(f"No data found for symbol: {symbol} after {max_retries} attempts")
                    return None
                continue  # Try again
                
            # Check if we have sufficient data (at least 30 days for meaningful analysis)
            if len(data) < 30:
                logger.warning(f"Insufficient data for symbol {symbol}: only {len(data)} days")
                return None
                
            # Reset index to make Date a column
            data.reset_index(inplace=True)
            
            # Ensure we have the expected columns
            expected_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            missing_columns = [col for col in expected_columns if col not in data.columns]
            
            if missing_columns:
                logger.error(f"Missing expected columns for {symbol}: {missing_columns}")
                return None
                
            logger.info(f"Successfully fetched {len(data)} days of data for {symbol}")
            return data
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check for specific error types that shouldn't be retried
            if any(phrase in error_msg for phrase in ['delisted', 'not found', 'no timezone']):
                logger.warning(f"Symbol {symbol} appears to be delisted or invalid: {str(e)}")
                return None
            
            # For other errors, log and potentially retry
            logger.warning(f"Error fetching data for symbol {symbol} (attempt {attempt + 1}): {str(e)}")
            
            if attempt == max_retries - 1:
                logger.error(f"Failed to fetch data for {symbol} after {max_retries} attempts")
                return None
    
    return None


def calculate_indicators(data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate technical indicators and add them as columns to the DataFrame.
    
    Args:
        data (pd.DataFrame): Stock data with OHLCV columns
        
    Returns:
        pd.DataFrame: Original data with additional indicator columns:
                     '20DMA', '50DMA', '100DMA', '200DMA', '30_day_avg_volume', 'RSI_14'
                     
    Raises:
        ValueError: If required columns are missing from the DataFrame
    """
    try:
        logger.info("Calculating technical indicators")
        
        # Validate input data
        if data is None or data.empty:
            raise ValueError("Input data is None or empty")
            
        required_columns = ['Close', 'Volume']
        missing_columns = [col for col in required_columns if col not in data.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
            
        # Create a copy to avoid modifying the original data
        result_data = data.copy()
        
        # Calculate Displaced Moving Averages (DMA)
        result_data['20DMA'] = result_data['Close'].rolling(window=20, min_periods=1).mean()
        result_data['50DMA'] = result_data['Close'].rolling(window=50, min_periods=1).mean()
        result_data['100DMA'] = result_data['Close'].rolling(window=100, min_periods=1).mean()
        result_data['200DMA'] = result_data['Close'].rolling(window=200, min_periods=1).mean()
        
        # Calculate 30-day average volume
        result_data['30_day_avg_volume'] = result_data['Volume'].rolling(window=30, min_periods=1).mean()
        
        # Calculate RSI (Relative Strength Index) with 14-day period
        result_data['RSI_14'] = calculate_rsi(result_data['Close'], window=14)
        
        # Calculate 52-week high (rolling maximum over 252 trading days)
        result_data['52_week_high'] = result_data['High'].rolling(window=252, min_periods=1).max()
        
        # Calculate ATR (Average True Range) with 14-day period
        result_data['ATR_14'] = calculate_atr(result_data, window=14)
        
        # Log successful calculation
        indicators_added = ['20DMA', '50DMA', '100DMA', '200DMA', '30_day_avg_volume', 'RSI_14', '52_week_high', 'ATR_14']
        logger.info(f"Successfully calculated indicators: {', '.join(indicators_added)}")
        
        return result_data
        
    except Exception as e:
        logger.error(f"Error calculating indicators: {str(e)}")
        raise


def calculate_rsi(prices: pd.Series, window: int = 14) -> pd.Series:
    """
    Calculate the Relative Strength Index (RSI) for a given price series.
    
    Args:
        prices (pd.Series): Series of closing prices
        window (int): Period for RSI calculation (default: 14)
        
    Returns:
        pd.Series: RSI values
    """
    try:
        # Calculate price changes
        delta = prices.diff()
        
        # Separate gains and losses
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        
        # Calculate average gains and losses using exponential moving average
        avg_gains = gains.ewm(span=window, min_periods=1).mean()
        avg_losses = losses.ewm(span=window, min_periods=1).mean()
        
        # Calculate relative strength
        rs = avg_gains / avg_losses
        
        # Calculate RSI
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
        
    except Exception as e:
        logger.error(f"Error calculating RSI: {str(e)}")
        return pd.Series([None] * len(prices), index=prices.index)


def calculate_atr(data: pd.DataFrame, window: int = 14) -> pd.Series:
    """
    Calculate the Average True Range (ATR) for a given DataFrame.
    
    Args:
        data (pd.DataFrame): DataFrame with High, Low, Close columns
        window (int): Period for ATR calculation (default: 14)
        
    Returns:
        pd.Series: ATR values
    """
    try:
        # Calculate True Range components
        high_low = data['High'] - data['Low']
        high_close_prev = abs(data['High'] - data['Close'].shift(1))
        low_close_prev = abs(data['Low'] - data['Close'].shift(1))
        
        # True Range is the maximum of the three components
        true_range = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
        
        # Calculate ATR using exponential moving average
        atr = true_range.ewm(span=window, min_periods=1).mean()
        
        return atr
        
    except Exception as e:
        logger.error(f"Error calculating ATR: {str(e)}")
        return pd.Series([None] * len(data), index=data.index)


def get_stock_info(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get basic stock information for a given symbol.
    
    Args:
        symbol (str): Stock symbol (e.g., 'RELIANCE.NS')
        
    Returns:
        dict: Stock information or None if failed
    """
    try:
        logger.info(f"Fetching stock info for symbol: {symbol}")
        
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Extract relevant information
        stock_info = {
            'symbol': symbol,
            'name': info.get('longName', 'N/A'),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'market_cap': info.get('marketCap', 'N/A'),
            'currency': info.get('currency', 'INR')
        }
        
        logger.info(f"Successfully fetched info for {symbol}")
        return stock_info
        
    except Exception as e:
        logger.error(f"Error fetching stock info for {symbol}: {str(e)}")
        return None


def check_breakout_signal(data: pd.DataFrame, config: Dict[str, Any]) -> Union[bool, Dict[str, Any]]:
    """
    Check if the latest day's data meets all breakout signal conditions.
    
    Args:
        data (pd.DataFrame): Stock data with calculated indicators
        config (dict): Configuration settings containing thresholds
        
    Returns:
        Union[bool, dict]: False if no breakout, or dict with breakout info including RSI for ranking
        
    Conditions checked:
        1. Close is above all DMAs (20, 50, 100, 200)
        2. Close is within 2% of 52-week high (>= 52_week_high * 0.98)
        3. Volume is at least 1.5x the 30-day average volume
        4. RSI_14 is greater than 60
        
    If breakout detected, returns:
        {
            'breakout': True,
            'rsi': float,  # RSI value for ranking
            'close': float,
            'volume': float,
            'conditions_met': int
        }
    """
    try:
        logger.info("Checking breakout signal conditions")
        
        # Validate input data
        if data is None or data.empty:
            logger.warning("No data provided for breakout signal check")
            return False
            
        # Required columns for breakout analysis
        required_columns = [
            'Close', 'Volume', '20DMA', '50DMA', '100DMA', '200DMA',
            '30_day_avg_volume', 'RSI_14', '52_week_high'
        ]
        
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            logger.error(f"Missing required columns for breakout analysis: {missing_columns}")
            return False
            
        # Get the latest day's data (last row)
        latest_data = data.iloc[-1]
        
        # Extract values for readability
        close = latest_data['Close']
        volume = latest_data['Volume']
        dma_20 = latest_data['20DMA']
        dma_50 = latest_data['50DMA']
        dma_100 = latest_data['100DMA']
        dma_200 = latest_data['200DMA']
        avg_volume_30 = latest_data['30_day_avg_volume']
        rsi_14 = latest_data['RSI_14']
        week_52_high = latest_data['52_week_high']
        
        # Check for any NaN values that would prevent analysis
        if pd.isna([close, volume, dma_20, dma_50, dma_100, dma_200, 
                   avg_volume_30, rsi_14, week_52_high]).any():
            logger.warning("Some indicator values are NaN, cannot perform breakout analysis")
            return False
            
        # Get thresholds from config
        volume_multiplier = config.get('volume_multiplier', 1.5)
        rsi_threshold = config.get('rsi_threshold', 60)
        week_52_proximity = config.get('week_52_high_proximity', 0.98)
        
        logger.info(f"Latest data - Close: {close:.2f}, Volume: {volume:,.0f}, RSI: {rsi_14:.2f}")
        
        # Condition 1: Close is above all DMAs
        above_all_dmas = (close > dma_20 and close > dma_50 and 
                         close > dma_100 and close > dma_200)
        
        logger.info(f"Above all DMAs: {above_all_dmas} "
                   f"(20DMA: {dma_20:.2f}, 50DMA: {dma_50:.2f}, "
                   f"100DMA: {dma_100:.2f}, 200DMA: {dma_200:.2f})")
        
        # Condition 2: Close is within 2% of 52-week high
        min_close_for_proximity = week_52_high * week_52_proximity
        near_52_week_high = close >= min_close_for_proximity
        
        logger.info(f"Near 52-week high: {near_52_week_high} "
                   f"(Close: {close:.2f} >= {min_close_for_proximity:.2f}, "
                   f"52W High: {week_52_high:.2f})")
        
        # Condition 3: Volume is at least 1.5x the 30-day average
        min_volume_required = avg_volume_30 * volume_multiplier
        high_volume = volume >= min_volume_required
        
        logger.info(f"High volume: {high_volume} "
                   f"(Volume: {volume:,.0f} >= {min_volume_required:,.0f}, "
                   f"30D Avg: {avg_volume_30:,.0f})")
        
        # Condition 4: RSI is greater than 60
        strong_rsi = rsi_14 > rsi_threshold
        
        logger.info(f"Strong RSI: {strong_rsi} "
                   f"(RSI: {rsi_14:.2f} > {rsi_threshold})")
        
        # All conditions must be met
        breakout_signal = (above_all_dmas and near_52_week_high and 
                          high_volume and strong_rsi)
        
        conditions_met = sum([above_all_dmas, near_52_week_high, high_volume, strong_rsi])
        
        logger.info(f"Breakout signal result: {breakout_signal}")
        
        if breakout_signal:
            logger.info("🚀 BREAKOUT SIGNAL DETECTED! All conditions met.")
            
            # Return breakout information including RSI for ranking
            breakout_info = {
                'breakout': True,
                'rsi': round(rsi_14, 2),
                'close': round(close, 2),
                'volume': round(volume, 0),
                'conditions_met': conditions_met,
                'above_all_dmas': above_all_dmas,
                'near_52_week_high': near_52_week_high,
                'high_volume': high_volume,
                'strong_rsi': strong_rsi
            }
            
            logger.info(f"Breakout info: RSI={breakout_info['rsi']}, Close=₹{breakout_info['close']}")
            return breakout_info
        else:
            logger.info(f"Breakout signal not detected. {conditions_met}/4 conditions met.")
            return False
        
    except Exception as e:
        logger.error(f"Error checking breakout signal: {str(e)}")
        return False


def generate_trade_plan(data: pd.DataFrame, risk_capital: float) -> Optional[Dict[str, Any]]:
    """
    Generate a complete trade plan based on breakout data and risk capital.
    
    Args:
        data (pd.DataFrame): Stock data with calculated indicators (including ATR_14)
        risk_capital (float): Amount of capital to risk per trade (e.g., 1000 INR)
        
    Returns:
        dict: Trade plan containing entry_price, initial_stop_loss, and position_size
              Returns None if unable to generate plan
              
    Trade Plan Components:
        - entry_price: High of the breakout day (latest day)
        - initial_stop_loss: entry_price - (2.5 * ATR_14)
        - position_size: risk_capital / (entry_price - initial_stop_loss), rounded to whole number
    """
    try:
        logger.info("Generating trade plan")
        
        # Validate input data
        if data is None or data.empty:
            logger.error("No data provided for trade plan generation")
            return None
            
        if risk_capital <= 0:
            logger.error(f"Invalid risk capital: {risk_capital}. Must be positive.")
            return None
            
        # Required columns for trade plan generation
        required_columns = ['High', 'ATR_14']
        missing_columns = [col for col in required_columns if col not in data.columns]
        
        if missing_columns:
            logger.error(f"Missing required columns for trade plan: {missing_columns}")
            return None
            
        # Get the latest day's data (breakout day)
        latest_data = data.iloc[-1]
        
        # Extract values
        high = latest_data['High']
        atr_14 = latest_data['ATR_14']
        
        # Check for NaN values
        if pd.isna(high) or pd.isna(atr_14):
            logger.error("High or ATR_14 values are NaN, cannot generate trade plan")
            return None
            
        # Calculate trade plan components
        entry_price = high  # Entry at the high of breakout day
        atr_multiplier = 2.5
        initial_stop_loss = entry_price - (atr_multiplier * atr_14)
        
        # Calculate risk per share
        risk_per_share = entry_price - initial_stop_loss
        
        if risk_per_share <= 0:
            logger.error(f"Invalid risk per share: {risk_per_share}. Stop loss is above entry price.")
            return None
            
        # Calculate position size and round to whole number
        position_size_float = risk_capital / risk_per_share
        position_size = round(position_size_float)
        
        # Ensure minimum position size of 1
        if position_size < 1:
            position_size = 1
            logger.warning(f"Position size calculated as {position_size_float:.2f}, "
                          f"rounded up to minimum of 1 share")
        
        # Calculate actual risk with rounded position size
        actual_risk = position_size * risk_per_share
        
        # Create trade plan dictionary
        trade_plan = {
            'entry_price': round(entry_price, 2),
            'initial_stop_loss': round(initial_stop_loss, 2),
            'position_size': position_size,
            'risk_per_share': round(risk_per_share, 2),
            'planned_risk': round(risk_capital, 2),
            'actual_risk': round(actual_risk, 2),
            'atr_14': round(atr_14, 2),
            'atr_multiplier': atr_multiplier
        }
        
        logger.info(f"Trade plan generated successfully:")
        logger.info(f"  Entry Price: ₹{trade_plan['entry_price']}")
        logger.info(f"  Stop Loss: ₹{trade_plan['initial_stop_loss']}")
        logger.info(f"  Position Size: {trade_plan['position_size']} shares")
        logger.info(f"  Risk per Share: ₹{trade_plan['risk_per_share']}")
        logger.info(f"  Planned Risk: ₹{trade_plan['planned_risk']}")
        logger.info(f"  Actual Risk: ₹{trade_plan['actual_risk']}")
        logger.info(f"  ATR(14): {trade_plan['atr_14']}")
        
        return trade_plan
        
    except Exception as e:
        logger.error(f"Error generating trade plan: {str(e)}")
        return None


def calculate_trailing_stop(data: pd.DataFrame) -> Optional[float]:
    """
    Calculate the trailing stop-loss price based on the 20-day low.
    
    Args:
        data (pd.DataFrame): Stock data with Low column
        
    Returns:
        float: The 20-day low price to be used as trailing stop-loss, or None if unable to calculate
    """
    try:
        logger.info("Calculating trailing stop (20-day low)")
        
        # Validate input data
        if data is None or data.empty:
            logger.error("No data provided for trailing stop calculation")
            return None
            
        # Check for required column
        if 'Low' not in data.columns:
            logger.error("Missing 'Low' column for trailing stop calculation")
            return None
            
        # Calculate 20-day rolling minimum of Low prices
        twenty_day_low = data['Low'].rolling(window=20, min_periods=1).min()
        
        # Get the latest 20-day low (most recent value)
        latest_trailing_stop = twenty_day_low.iloc[-1]
        
        # Check for NaN value
        if pd.isna(latest_trailing_stop):
            logger.error("20-day low calculation resulted in NaN")
            return None
            
        trailing_stop = round(latest_trailing_stop, 2)
        
        logger.info(f"Trailing stop (20-day low): ₹{trailing_stop}")
        
        return trailing_stop
        
    except Exception as e:
        logger.error(f"Error calculating trailing stop: {str(e)}")
        return None
