#!/usr/bin/env python3
"""
Swing Trading Analysis Script - Main Worker
============================================

This script performs the complete swing trading analysis workflow:
1. Fetches stock data for all configured symbols
2. Calculates technical indicators
3. Identifies breakout signals
4. Generates trade plans with risk management
5. Ranks candidates by RSI
6. Saves results to database

Usage:
    python run_analysis.py

This script is designed to be run daily to identify new trading opportunities.
"""

import sys
import os
import logging
from datetime import datetime
from typing import List, Dict, Any

# Add the project root to Python path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import configuration and modules
from config import STRATEGY_PARAMS, Config
from app.analyzer import (
    get_stock_data, 
    calculate_indicators, 
    check_breakout_signal, 
    generate_trade_plan, 
    calculate_trailing_stop
)
from app.database import (
    init_db, 
    clear_todays_signals, 
    save_signal
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('swing_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def analyze_stock(symbol: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform complete analysis for a single stock symbol.
    
    Args:
        symbol (str): Stock symbol to analyze
        config (dict): Configuration parameters
        
    Returns:
        dict: Complete analysis results or None if no breakout
    """
    try:
        logger.info(f"🔍 Analyzing {symbol}...")
        
        # Step 1: Fetch stock data
        data = get_stock_data(symbol)
        if data is None:
            logger.warning(f"❌ Failed to fetch data for {symbol}")
            return None
            
        # Step 2: Calculate technical indicators
        enriched_data = calculate_indicators(data)
        if enriched_data is None or enriched_data.empty:
            logger.warning(f"❌ Failed to calculate indicators for {symbol}")
            return None
            
        # Step 3: Check for breakout signal
        breakout_result = check_breakout_signal(enriched_data, config)
        
        # If no breakout detected, return None
        if not breakout_result or not isinstance(breakout_result, dict):
            logger.info(f"📉 No breakout signal for {symbol}")
            return None
            
        logger.info(f"🚀 BREAKOUT DETECTED for {symbol}! RSI: {breakout_result['rsi']}")
        
        # Step 4: Generate trade plan
        trade_plan = generate_trade_plan(enriched_data, config['risk_per_trade'])
        if trade_plan is None:
            logger.warning(f"❌ Failed to generate trade plan for {symbol}")
            return None
            
        # Step 5: Calculate trailing stop
        trailing_stop = calculate_trailing_stop(enriched_data)
        if trailing_stop is None:
            logger.warning(f"❌ Failed to calculate trailing stop for {symbol}")
            return None
            
        # Step 6: Compile complete candidate data
        candidate = {
            'symbol': symbol,
            'rsi': breakout_result['rsi'],
            'close': breakout_result['close'],
            'volume': breakout_result['volume'],
            'conditions_met': breakout_result['conditions_met'],
            'entry_price': trade_plan['entry_price'],
            'initial_stop_loss': trade_plan['initial_stop_loss'],
            'position_size': trade_plan['position_size'],
            'risk_per_share': trade_plan['risk_per_share'],
            'actual_risk': trade_plan['actual_risk'],
            'trailing_stop': trailing_stop,
            'current_price': breakout_result['close'],
            'atr_14': trade_plan['atr_14']
        }
        
        logger.info(f"✅ Complete analysis for {symbol}:")
        logger.info(f"   RSI: {candidate['rsi']}")
        logger.info(f"   Entry: ₹{candidate['entry_price']}")
        logger.info(f"   Stop Loss: ₹{candidate['initial_stop_loss']}")
        logger.info(f"   Position: {candidate['position_size']} shares")
        logger.info(f"   Trailing Stop: ₹{candidate['trailing_stop']}")
        
        return candidate
        
    except Exception as e:
        logger.error(f"❌ Error analyzing {symbol}: {str(e)}")
        return None


def rank_candidates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Rank candidates in descending order based on RSI value.
    
    Args:
        candidates (list): List of candidate dictionaries
        
    Returns:
        list: Sorted list with highest RSI first
    """
    try:
        logger.info(f"📊 Ranking {len(candidates)} candidates by RSI...")
        
        # Sort by RSI in descending order (highest RSI first)
        ranked_candidates = sorted(candidates, key=lambda x: x['rsi'], reverse=True)
        
        logger.info("🏆 RANKING RESULTS:")
        for i, candidate in enumerate(ranked_candidates, 1):
            logger.info(f"   {i}. {candidate['symbol']} - RSI: {candidate['rsi']}")
            
        return ranked_candidates
        
    except Exception as e:
        logger.error(f"❌ Error ranking candidates: {str(e)}")
        return candidates


def save_candidates_to_database(ranked_candidates: List[Dict[str, Any]]) -> bool:
    """
    Save ranked candidates to the database with assigned rank numbers.
    
    Args:
        ranked_candidates (list): List of ranked candidate dictionaries
        
    Returns:
        bool: True if all saves successful, False otherwise
    """
    try:
        logger.info(f"💾 Saving {len(ranked_candidates)} candidates to database...")
        
        success_count = 0
        
        for rank, candidate in enumerate(ranked_candidates, 1):
            # Prepare signal data for database
            signal_data = {
                'symbol': candidate['symbol'],
                'rank': rank,
                'buy_signal': 1,  # All breakouts are buy signals
                'entry_price': candidate['entry_price'],
                'initial_stop_loss': candidate['initial_stop_loss'],
                'position_size': candidate['position_size'],
                'trailing_stop': candidate['trailing_stop'],
                'current_price': candidate['current_price']
            }
            
            # Save to database
            if save_signal(signal_data):
                success_count += 1
                logger.info(f"✅ Saved Rank {rank}: {candidate['symbol']}")
            else:
                logger.error(f"❌ Failed to save {candidate['symbol']}")
                
        logger.info(f"💾 Database save complete: {success_count}/{len(ranked_candidates)} successful")
        return success_count == len(ranked_candidates)
        
    except Exception as e:
        logger.error(f"❌ Error saving candidates to database: {str(e)}")
        return False


def main():
    """
    Main analysis workflow function.
    """
    try:
        # Print header
        print("=" * 60)
        print("🎯 SWING TRADING ANALYSIS - DAILY SCAN")
        print("=" * 60)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📈 Symbols to analyze: {len(Config.STOCK_SYMBOLS)}")
        print(f"💰 Risk per trade: ₹{Config.RISK_PER_TRADE}")
        print("=" * 60)
        
        logger.info("🚀 Starting swing trading analysis...")
        
        # Step 1: Initialize database
        logger.info("📊 Initializing database...")
        if not init_db():
            logger.error("❌ Failed to initialize database. Exiting.")
            return False
        logger.info("✅ Database initialized successfully")
        
        # Step 2: Clear today's signals
        logger.info("🧹 Clearing today's signals...")
        if not clear_todays_signals():
            logger.warning("⚠️ Failed to clear today's signals, continuing anyway...")
        else:
            logger.info("✅ Today's signals cleared")
        
        # Step 3: Initialize candidates list
        breakout_candidates = []
        
        # Step 4: Analyze each stock symbol
        logger.info(f"🔍 Analyzing {len(Config.STOCK_SYMBOLS)} symbols...")
        print(f"\n🔍 STOCK ANALYSIS:")
        
        for i, symbol in enumerate(Config.STOCK_SYMBOLS, 1):
            print(f"   {i}/{len(Config.STOCK_SYMBOLS)}: {symbol}")
            
            # Analyze the stock
            candidate = analyze_stock(symbol, STRATEGY_PARAMS)
            
            # Add to candidates list if breakout detected
            if candidate:
                breakout_candidates.append(candidate)
                print(f"      ✅ BREAKOUT! RSI: {candidate['rsi']}")
            else:
                print(f"      📉 No signal")
        
        # Step 5: Check if any candidates found
        if not breakout_candidates:
            logger.info("📉 No breakout candidates found today")
            print(f"\n📉 RESULTS: No breakout signals detected")
            return True
            
        # Step 6: Rank candidates by RSI
        ranked_candidates = rank_candidates(breakout_candidates)
        
        # Step 7: Save to database with ranks
        success = save_candidates_to_database(ranked_candidates)
        
        # Print final results
        print(f"\n🏆 FINAL RESULTS:")
        print(f"   📊 Total candidates: {len(ranked_candidates)}")
        print(f"   💾 Database saves: {'✅ Success' if success else '❌ Failed'}")
        print(f"\n📋 TOP CANDIDATES:")
        
        for i, candidate in enumerate(ranked_candidates[:5], 1):  # Show top 5
            print(f"   {i}. {candidate['symbol']}")
            print(f"      RSI: {candidate['rsi']}")
            print(f"      Entry: ₹{candidate['entry_price']}")
            print(f"      Stop: ₹{candidate['initial_stop_loss']}")
            print(f"      Size: {candidate['position_size']} shares")
            print()
        
        logger.info(f"🎉 Analysis complete! Found {len(ranked_candidates)} breakout candidates")
        print("=" * 60)
        print("🎉 ANALYSIS COMPLETE!")
        print("=" * 60)
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Critical error in main workflow: {str(e)}")
        print(f"❌ CRITICAL ERROR: {str(e)}")
        return False


if __name__ == "__main__":
    """
    Script entry point when run directly.
    """
    try:
        # Run the main analysis
        success = main()
        
        # Exit with appropriate code
        exit_code = 0 if success else 1
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        logger.info("⏹️ Analysis interrupted by user")
        print("\n⏹️ Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        print(f"❌ UNEXPECTED ERROR: {str(e)}")
        sys.exit(1)
