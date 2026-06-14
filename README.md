# Daraz Deep Search Price Anomaly Bot

This Python script is a powerful tool designed to scan Daraz.lk for significant price drops and potential pricing errors. It automates the process of crawling multiple pages of search results, analyzing market prices, and flagging items that are listed significantly below the calculated median price for that product category.

## 🚀 Features

-   **Deep Catalog Crawling**: Scans multiple pages of search results for a given product query.
-   **Intelligent Filtering**:
    -   Filters out irrelevant items based on keywords in the product title.
    -   Allows exclusion of accessories and other unwanted items via negative keywords (e.g., `case`, `cover`, `protector`).
    -   Uses a base price floor to ignore cheap accessories.
-   **Adaptive Median Pricing**: Calculates a "true" market median price by intelligently filtering the dataset, providing a reliable baseline for comparison.
-   **Anomaly Detection**: Flags products priced significantly below the market median based on a user-defined percentage threshold.
-   **Persistent Alert Logging**: Remembers previously found deals in a `triggered_glitches_log.csv` to only notify you of *new* discoveries.
-   **Rich HTML Reports**: Generates a detailed, easy-to-read HTML report for each search, highlighting new deals and providing a full index of all products found.
-   **Automated Browser Handling**: Uses `seleniumbase` to manage the browser, including minimizing the window on startup to keep your terminal visible.

## 🛠️ How to Use

### 1. Prerequisites

-   Python 3.x installed.
-   Google Chrome browser installed.

### 2. Setup

1.  **Clone the repository or download the files.**
2.  **Navigate to the project directory** in your terminal:
    ```bash
    cd "c:\Users\Zoohunter\Desktop\Daraz bot"
    ```
3.  **Install the required Python libraries**:
    ```bash
    pip install pandas seleniumbase
    ```

### 3. Running the Bot

**Easy Method (Recommended):**

Simply double-click the `run_bot.bat` file in the project folder. A terminal will open, automatically handle the setup, and launch the application.

**Manual Method (For developers):**

1.  Open a terminal or command prompt in the project folder.
2.  Run the script directly: `python Daraz_Bot_by_Nepstro.py`
3.  **Follow the on-screen prompts:**
    -   **Enter target product**: Type the name of the product you want to search for (e.g., `air fryer`, `samsung s24 ultra`).
    -   **Enter minimum base price**: Set a price floor to ignore cheap accessories. For example, if you're looking for a phone, you might set this to `10000` to ignore cases and screen protectors.
    -   **Enter price drop trigger**: The percentage drop from the median price that should trigger an alert (e.g., `50` for 50%).
    -   **Enter keywords to EXCLUDE**: Comma-separated words to filter out unwanted items (e.g., `case,cover,paper,pot`).

The script will then launch a browser, perform the search, and generate an HTML report which will open automatically. New, critical alerts will be printed directly to your terminal.

## ⚠️ Disclaimer

This tool is provided for educational and informational purposes only. The creator is not responsible for any decisions made based on the data, financial losses, or any other consequences of using this software. Always double-check information on the official Daraz website before making any purchases. Use at your own risk.

---

## 🏆 Credits

 -   **Author**: [Nepstro](https://github.com/Nepstro)