# 💰 smart-tax-filer

An AI-powered tax agent that automates expense categorization using Python and Claude 3.5 Sonnet. Designed for US small business owners and contractors to streamline Schedule C preparation and provide reliable audit trails.

---

## 🚀 Features

- **AI-Powered Categorization:** Automatically maps receipts to IRS Schedule C categories using Claude 3.5 Sonnet.
- **Audit Trails:** Generates professional justifications for every deduction to ensure audit readiness.
- **Interactive Dashboard:** Built with Streamlit for a seamless user experience, including real-time analytics.
- **Data Export:** Easily download your structured tax records in CSV format for use in TurboTax or with your CPA.
- **Visual Analytics:** Dynamic pie charts to track your spending by category throughout the year.

---

## 🛠️ Tech Stack

- **Language:** Python 3.x
- **Framework:** Streamlit
- **AI Model:** Claude 3.5 Sonnet (via Anthropic API)
- **Data Handling:** Pandas, Plotly

---

## ⚙️ Installation

To run this project locally, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/yysecret/smart-tax-filer.git](https://github.com/yysecret/smart-tax-filer.git)
   cd smart-tax-filer

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt

3. **Set up your environment variables: Create a .env file in the root directory and add your API keys:**
   ANTHROPIC_API_KEY=your_actual_key_here

4. **Run the application:**
   ```bash
   streamlit run app.py

## 📖 Usage

Open the application in your browser (usually at http://localhost:8501).

Upload a receipt image or enter a description of the expense.

The AI agent will categorize the expense and provide an audit justification.

View your categorized history and download the full report whenever needed.

## 🛡️ License

This project is licensed under the MIT License.
   

   
