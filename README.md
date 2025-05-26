# Portfolio Manager

A Streamlit-based portfolio management application for tracking investment positions.

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the Streamlit application:
```bash
streamlit run app.py
```

## Features

- Add new portfolio positions with ticker, entry date, price, quantity, and notes
- View current portfolio holdings in a table format
- Edit or delete existing positions
- View basic portfolio statistics
- Data persistence using CSV storage

## File Structure

- `app.py` - Main Streamlit application
- `portfolio.csv` - Portfolio data storage
- `requirements.txt` - Python dependencies

## Usage

1. Launch the application using `streamlit run app.py`
2. Use the "Add New Position" form to add positions to your portfolio
3. View your current positions in the table
4. Use the expander sections to edit or delete existing positions
5. Monitor your portfolio statistics at the bottom of the page 