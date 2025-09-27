"""
Flask routes for the Swing Trading application.
"""

from flask import Blueprint, render_template, jsonify
import logging
from datetime import datetime
from config import STRATEGY_PARAMS
from app.database import get_todays_signals, init_db

# Configure logging
logger = logging.getLogger(__name__)

# Create a blueprint for main routes
main = Blueprint('main', __name__)


@main.route('/')
def index():
    """
    Home page route - displays today's trading signals.
    
    Queries the trading_signals.db to get all of today's signals ordered by rank,
    then passes the list to the index.html template for rendering.
    """
    try:
        logger.info("Loading homepage with today's trading signals")
        
        # Initialize database if it doesn't exist
        init_db()
        
        # Get today's signals from database, ordered by rank
        todays_signals = get_todays_signals()
        
        if todays_signals is None:
            logger.error("Failed to retrieve today's signals from database")
            todays_signals = []
        
        # Get current date for display
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().strftime('%H:%M:%S')
        
        # Count total signals
        signal_count = len(todays_signals)
        
        logger.info(f"Retrieved {signal_count} trading signals for {current_date}")
        
        # Pass data to template
        template_data = {
            'signals': todays_signals,
            'strategy_params': STRATEGY_PARAMS,
            'current_date': current_date,
            'current_time': current_time,
            'signal_count': signal_count
        }
        
        return render_template('index.html', **template_data)
        
    except Exception as e:
        logger.error(f"Error loading homepage: {str(e)}")
        
        # Return error page with fallback data
        error_data = {
            'signals': [],
            'strategy_params': STRATEGY_PARAMS,
            'current_date': datetime.now().strftime('%Y-%m-%d'),
            'current_time': datetime.now().strftime('%H:%M:%S'),
            'signal_count': 0,
            'error_message': f"Error loading signals: {str(e)}"
        }
        
        return render_template('index.html', **error_data)


@main.route('/api/signals')
def api_signals():
    """
    API endpoint to get today's signals as JSON.
    Useful for AJAX requests or external integrations.
    """
    try:
        logger.info("API request for today's signals")
        
        # Get today's signals
        todays_signals = get_todays_signals()
        
        if todays_signals is None:
            return jsonify({
                'status': 'error',
                'message': 'Failed to retrieve signals',
                'signals': []
            }), 500
        
        return jsonify({
            'status': 'success',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'count': len(todays_signals),
            'signals': todays_signals
        })
        
    except Exception as e:
        logger.error(f"Error in API signals endpoint: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'signals': []
        }), 500


@main.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy', 
        'message': 'Swing Trader API is running',
        'timestamp': datetime.now().isoformat()
    })
