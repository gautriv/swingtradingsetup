# Swing Trading Stock Analysis Application

This is a **Python Flask application** that analyzes stocks based on technical indicators and generates buy signals. The app uses **moving averages (DMA)**, **RSI**, **support and resistance levels**, and **volume confirmation** to determine whether a stock is a good buy. The system is designed for swing trading strategies, focusing on short- to medium-term stock holding periods.

## Features

- **Technical Indicators:**
  - **20-Day Moving Average (DMA)**
  - **50-Day DMA**
  - **100-Day DMA**
  - **200-Day DMA**
  - **RSI (Relative Strength Index)**
  - **Support and Resistance levels**
  - **Volume Confirmation**

- **Buy Signal Logic**:
  - A buy signal is generated based on a combination of:
    - Bullish trend (moving averages aligned in an uptrend)
    - RSI below 30 (oversold condition)
    - Price near support level (within 10%)
    - Price not near resistance level (within 10%)
    - Volume higher than or near the 20-day average volume

## Setup and Installation

### Prerequisites

Ensure you have the following installed:

- **Python 3.x**
- **Flask**: Install Flask via `pip` if you haven't already:

    ```bash
    pip install Flask
    ```

- **pandas**: Used for data manipulation:

    ```bash
    pip install pandas
    ```

- **yfinance**: For fetching stock data:

    ```bash
    pip install yfinance
    ```

### Installation

1. Clone the Repository:

    ```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
    ```

2. Install Dependencies:

    Install the required Python libraries by running:

    ```bash
    pip install -r requirements.txt
    ```

    If you don't have a `requirements.txt` file yet, you can create one using the command:

    ```bash
    pip freeze > requirements.txt
    ```

3. Run the Application:

    To start the Flask development server:

    ```bash
    flask run
    ```

    By default, the app will be running at [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Usage

Open your browser and navigate to [http://127.0.0.1:5000](http://127.0.0.1:5000).  
The app will display a table with stock analysis results, including:

- Current stock price
- Moving averages
- RSI
- 52-week high and low
- Support and resistance levels
- Buy signal based on the defined logic

### Buy Signal Logic

The app uses the following conditions to generate a "BUY" signal:

- **Bullish Trend**: The 20-day, 50-day, 100-day, and 200-day moving averages must be aligned in a bullish trend (20 DMA > 50 DMA > 100 DMA > 200 DMA).
- **RSI**: The stock's RSI (Relative Strength Index) must be below 30, indicating an oversold condition.
- **Price Near Support**: The stock's price must be within 10% of a key support level.
- **Price Not Near Resistance**: The stock's price must not be within 10% of the resistance level.
- **Volume Confirmation**: The trading volume must be higher than or near the 20-day average volume.

## File Structure

```bash
├── app/
│   ├── __init__.py         # Initialize the Flask app
│   ├── routes.py           # Define the app routes and logic
│   ├── stock_analyzer.py   # Main stock analysis logic
│   └── templates/
│       └── index.html      # HTML template for displaying stock data
├── static/
│   └── style.css           # CSS for table styling
├── README.md               # You're reading this!
├── requirements.txt        # Dependencies for the app
└── app.py                  # Main entry point for the Flask app
```

## Contributing
Contributions are welcome! Feel free to open issues or submit pull requests.

## License
## License

This project is licensed under the [MIT License](LICENSE) - see the LICENSE file for details.

