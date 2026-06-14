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

## 📊 Sample Report

The script generates a clean, detailed HTML report for each search, highlighting the best deals found. New priority alerts are listed at the top, with a full index of all scanned products below.

!Sample HTML Report

---

## 🛠️ How to Use

This bot is designed to be run on your local computer.

### Prerequisites

-   Python 3.x installed.
-   Google Chrome browser installed.

### Setup and Launch

**Easy Method (Recommended):**

1.  Download the project files. You can do this by clicking the green `<> Code` button on the GitHub page and selecting **"Download ZIP"**.
2.  Unzip the folder to a location on your computer.
3.  Simply double-click the `run_bot.bat` file. A terminal will open, automatically install the required libraries, and launch the application.

**Manual Launch (for developers):**

This method is for users who are comfortable with the command line and Git.

1.  **Clone the Repository:** Open your terminal and run the following command to download the project files.
    ```bash
    git clone https://github.com/Nepstro/Daraz-bot.git
    ```

2.  **Navigate into the Directory:**
    ```bash
    cd Daraz-bot
    ```
3.  **Install Required Libraries:**
    ```bash
    pip install pandas seleniumbase
    ```
4.  **Run the Script:**
    ```bash
    python Daraz_Bot_by_Nepstro.py
    ```
5.  Follow the interactive prompts in the terminal to start your search.

---

## ⚠️ Disclaimer

This tool is provided for educational and informational purposes only. The creator is not responsible for any decisions made based on the data, financial losses, or any other consequences of using this software. Always double-check information on the official Daraz website before making any purchases. Use at your own risk.

---

## 🏆 Credits

 -   **Author**: [Nepstro](https://github.com/Nepstro)