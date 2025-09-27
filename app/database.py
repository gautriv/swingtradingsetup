"""
Database module for the Swing Trading application.
Handles SQLite database operations for trading signals storage and retrieval.
"""

import sqlite3
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_NAME = 'trading_signals.db'
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), DATABASE_NAME)


def init_db() -> bool:
    """
    Initialize the SQLite database and create the signals table if it doesn't exist.
    
    Returns:
        bool: True if database initialization successful, False otherwise
        
    Table Schema:
        - date: Date of the signal (TEXT)
        - symbol: Stock symbol (TEXT)
        - rank: Ranking based on RSI (INTEGER)
        - buy_signal: Whether it's a buy signal (INTEGER - 0 or 1)
        - entry_price: Entry price for the trade (REAL)
        - initial_stop_loss: Initial stop loss price (REAL)
        - position_size: Number of shares to buy (INTEGER)
        - trailing_stop: Trailing stop loss price (REAL)
        - current_price: Current market price (REAL)
    """
    try:
        logger.info(f"Initializing database: {DATABASE_PATH}")
        
        # Create connection to SQLite database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Create signals table with all required columns
        create_table_query = """
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            symbol TEXT NOT NULL,
            rank INTEGER,
            buy_signal INTEGER NOT NULL DEFAULT 1,
            entry_price REAL,
            initial_stop_loss REAL,
            position_size INTEGER,
            trailing_stop REAL,
            current_price REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        cursor.execute(create_table_query)
        
        # Create index for faster queries on date and symbol
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_date_symbol ON signals(date, symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_date ON signals(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbol ON signals(symbol)")
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        logger.info("Database initialized successfully")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"SQLite error during database initialization: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during database initialization: {str(e)}")
        return False


def clear_todays_signals() -> bool:
    """
    Delete all signal records from the signals table for the current date.
    
    Returns:
        bool: True if deletion successful, False otherwise
    """
    try:
        # Get today's date in YYYY-MM-DD format
        today = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"Clearing today's signals for date: {today}")
        
        # Create connection to database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Delete all records for today's date
        delete_query = "DELETE FROM signals WHERE date = ?"
        cursor.execute(delete_query, (today,))
        
        # Get number of deleted records
        deleted_count = cursor.rowcount
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        logger.info(f"Successfully deleted {deleted_count} signal(s) for {today}")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"SQLite error during signal deletion: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during signal deletion: {str(e)}")
        return False


def save_signal(signal_data: Dict[str, Any]) -> bool:
    """
    Save a trading signal to the signals table.
    
    Args:
        signal_data (dict): Dictionary containing signal data with keys:
                          - symbol: Stock symbol (required)
                          - rank: RSI-based ranking (optional)
                          - buy_signal: 1 for buy, 0 for sell (optional, defaults to 1)
                          - entry_price: Entry price (optional)
                          - initial_stop_loss: Initial stop loss (optional)
                          - position_size: Number of shares (optional)
                          - trailing_stop: Trailing stop price (optional)
                          - current_price: Current market price (optional)
                          - date: Signal date (optional, defaults to today)
    
    Returns:
        bool: True if save successful, False otherwise
    """
    try:
        logger.info(f"Saving signal data for symbol: {signal_data.get('symbol', 'Unknown')}")
        
        # Validate required fields
        if 'symbol' not in signal_data or not signal_data['symbol']:
            logger.error("Signal data missing required 'symbol' field")
            return False
            
        # Set default values
        today = datetime.now().strftime('%Y-%m-%d')
        signal_date = signal_data.get('date', today)
        
        # Create connection to database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Prepare insert query
        insert_query = """
        INSERT INTO signals (
            date, symbol, rank, buy_signal, entry_price, 
            initial_stop_loss, position_size, trailing_stop, current_price
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        # Extract values with defaults
        values = (
            signal_date,
            signal_data['symbol'],
            signal_data.get('rank'),
            signal_data.get('buy_signal', 1),
            signal_data.get('entry_price'),
            signal_data.get('initial_stop_loss'),
            signal_data.get('position_size'),
            signal_data.get('trailing_stop'),
            signal_data.get('current_price')
        )
        
        # Execute insert
        cursor.execute(insert_query, values)
        
        # Get the ID of the inserted record
        signal_id = cursor.lastrowid
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        logger.info(f"Successfully saved signal with ID: {signal_id} for symbol: {signal_data['symbol']}")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"SQLite error during signal save: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during signal save: {str(e)}")
        return False


def get_todays_signals() -> Optional[List[Dict[str, Any]]]:
    """
    Retrieve all trading signals for today's date.
    
    Returns:
        List[Dict]: List of signal dictionaries, or None if error
    """
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        logger.info(f"Retrieving signals for date: {today}")
        
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()
        
        query = """
        SELECT * FROM signals 
        WHERE date = ? 
        ORDER BY rank ASC, symbol ASC
        """
        
        cursor.execute(query, (today,))
        rows = cursor.fetchall()
        
        # Convert rows to list of dictionaries
        signals = [dict(row) for row in rows]
        
        conn.close()
        
        logger.info(f"Retrieved {len(signals)} signal(s) for {today}")
        return signals
        
    except sqlite3.Error as e:
        logger.error(f"SQLite error during signal retrieval: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during signal retrieval: {str(e)}")
        return None


def get_signals_by_symbol(symbol: str, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
    """
    Retrieve recent trading signals for a specific symbol.
    
    Args:
        symbol (str): Stock symbol to search for
        limit (int): Maximum number of records to return
        
    Returns:
        List[Dict]: List of signal dictionaries, or None if error
    """
    try:
        logger.info(f"Retrieving signals for symbol: {symbol}")
        
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
        SELECT * FROM signals 
        WHERE symbol = ? 
        ORDER BY date DESC, created_at DESC
        LIMIT ?
        """
        
        cursor.execute(query, (symbol, limit))
        rows = cursor.fetchall()
        
        signals = [dict(row) for row in rows]
        
        conn.close()
        
        logger.info(f"Retrieved {len(signals)} signal(s) for symbol: {symbol}")
        return signals
        
    except sqlite3.Error as e:
        logger.error(f"SQLite error during symbol signal retrieval: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during symbol signal retrieval: {str(e)}")
        return None


def update_signal_prices(symbol: str, current_price: float, trailing_stop: float = None) -> bool:
    """
    Update current price and optionally trailing stop for today's signal of a specific symbol.
    
    Args:
        symbol (str): Stock symbol to update
        current_price (float): New current price
        trailing_stop (float): New trailing stop price (optional)
        
    Returns:
        bool: True if update successful, False otherwise
    """
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        logger.info(f"Updating prices for {symbol} on {today}")
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Build update query based on whether trailing_stop is provided
        if trailing_stop is not None:
            query = """
            UPDATE signals 
            SET current_price = ?, trailing_stop = ?, updated_at = CURRENT_TIMESTAMP
            WHERE symbol = ? AND date = ?
            """
            values = (current_price, trailing_stop, symbol, today)
        else:
            query = """
            UPDATE signals 
            SET current_price = ?, updated_at = CURRENT_TIMESTAMP
            WHERE symbol = ? AND date = ?
            """
            values = (current_price, symbol, today)
        
        cursor.execute(query, values)
        updated_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        if updated_count > 0:
            logger.info(f"Successfully updated {updated_count} record(s) for {symbol}")
            return True
        else:
            logger.warning(f"No records found to update for {symbol} on {today}")
            return False
            
    except sqlite3.Error as e:
        logger.error(f"SQLite error during price update: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during price update: {str(e)}")
        return False
