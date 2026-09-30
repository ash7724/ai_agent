
import sqlite3
from pathlib import Path
from datetime import date

import pandas as pd
import requests
import streamlit as st

# ============================================================
# CONFIGURATION
# ============================================================

DB_PATH = Path("finance.db")
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:7b"

# ============================================================
# DATABASE
# ============================================================

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()

    conn.executescript("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        description TEXT NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        type TEXT NOT NULL,
        account TEXT,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        value REAL NOT NULL,
        as_of TEXT NOT NULL,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS liabilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        balance REAL NOT NULL,
        interest_rate REAL DEFAULT 0,
        emi REAL DEFAULT 0,
        as_of TEXT NOT NULL,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS holdings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        name TEXT,
        asset_class TEXT NOT NULL,
        quantity REAL NOT NULL,
        avg_cost REAL NOT NULL,
        current_price REAL NOT NULL,
        as_of TEXT NOT NULL,
        notes TEXT
    );
    """)

    conn.commit()
    conn.close()


# ============================================================
# DATABASE INSERTS
# ============================================================

def add_transaction(d, description, category, amount, typ, account, notes):
    conn = db()
    conn.execute("""
        INSERT INTO transactions
        (date, description, category, amount, type, account, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (d, description, category, amount, typ, account, notes))
    conn.commit()
    conn.close()


def add_asset(name, category, value, as_of, notes):
    conn = db()
    conn.execute("""
        INSERT INTO assets
        (name, category, value, as_of, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (name, category, value, as_of, notes))
    conn.commit()
    conn.close()


def add_liability(name, category, balance, rate, emi, as_of, notes):
    conn = db()
    conn.execute("""
        INSERT INTO liabilities
        (name, category, balance, interest_rate, emi, as_of, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, category, balance, rate, emi, as_of, notes))
    conn.commit()
    conn.close()


def add_holding(symbol, name, asset_class, quantity,
                avg_cost, current_price, as_of, notes):

    conn = db()

    conn.execute("""
        INSERT INTO holdings
        (symbol, name, asset_class, quantity,
         avg_cost, current_price, as_of, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        symbol,
        name,
        asset_class,
        quantity,
        avg_cost,
        current_price,
        as_of,
        notes
    ))

    conn.commit()
    conn.close()


# ============================================================
# DATA READERS
# ============================================================

def get_transactions():

    conn = db()

    df = pd.read_sql_query(
        "SELECT * FROM transactions ORDER BY date DESC, id DESC",
        conn
    )

    conn.close()

    return df


def get_assets():

    conn = db()

    df = pd.read_sql_query(
        "SELECT * FROM assets ORDER BY value DESC",
        conn
    )

    conn.close()

    return df


def get_liabilities():

    conn = db()

    df = pd.read_sql_query(
        "SELECT * FROM liabilities ORDER BY balance DESC",
        conn
    )

    conn.close()

    return df


def get_holdings():

    conn = db()

    df = pd.read_sql_query(
        "SELECT * FROM holdings ORDER BY symbol",
        conn
    )

    conn.close()

    return df


# ============================================================
# FINANCIAL CALCULATIONS
# ============================================================

def calculate_metrics():

    transactions = get_transactions()
    assets = get_assets()
    liabilities = get_liabilities()
    holdings = get_holdings()

    income = 0
    expenses = 0
    asset_value = 0
    liability_value = 0
    portfolio_value = 0
    portfolio_cost = 0

    if not transactions.empty:

        income = transactions.loc[
            transactions["type"] == "income",
            "amount"
        ].sum()

        expenses = transactions.loc[
            transactions["type"] == "expense",
            "amount"
        ].sum()

    if not assets.empty:
        asset_value = assets["value"].sum()

    if not liabilities.empty:
        liability_value = liabilities["balance"].sum()

    if not holdings.empty:

        portfolio_value = (
            holdings["quantity"] *
            holdings["current_price"]
        ).sum()

        portfolio_cost = (
            holdings["quantity"] *
            holdings["avg_cost"]
        ).sum()

    total_assets = asset_value + portfolio_value

    net_worth = total_assets - liability_value

    cashflow = income - expenses

    portfolio_profit = portfolio_value - portfolio_cost

    return {
        "income": income,
        "expenses": expenses,
        "cashflow": cashflow,
        "assets": total_assets,
        "liabilities": liability_value,
        "net_worth": net_worth,
        "portfolio_value": portfolio_value,
        "portfolio_cost": portfolio_cost,
        "portfolio_profit": portfolio_profit
    }


def expense_categories():

    df = get_transactions()

    if df.empty:
        return pd.DataFrame()

    df = df[df["type"] == "expense"]

    if df.empty:
        return pd.DataFrame()

    return (
        df.groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
    )


def monthly_cashflow():

    df = get_transactions()

    if df.empty:
        return pd.DataFrame()

    df["month"] = pd.to_datetime(
        df["date"]
    ).dt.to_period("M").astype(str)

    result = df.pivot_table(
        index="month",
        columns="type",
        values="amount",
        aggfunc="sum",
        fill_value=0
    )

    if "income" not in result.columns:
        result["income"] = 0

    if "expense" not in result.columns:
        result["expense"] = 0

    result["cashflow"] = (
        result["income"] -
        result["expense"]
    )

    return result


# ============================================================
# AI ANALYST
# ============================================================

def generate_ai_analysis():

    metrics = calculate_metrics()

    categories = expense_categories()

    monthly = monthly_cashflow()

    category_data = {}

    if not categories.empty:
        category_data = categories.head(10).to_dict()

    monthly_data = {}

    if not monthly.empty:
        monthly_data = monthly.tail(6).to_dict()

    prompt = f"""
You are a personal finance analysis assistant.

Analyze the following calculated financial information.

Do NOT invent transactions.
Do NOT invent investment prices.
Do NOT make claims that are not supported by the data.

FINANCIAL METRICS:

{metrics}

TOP EXPENSE CATEGORIES:

{category_data}

RECENT MONTHLY CASH FLOW:

{monthly_data}

Provide:

1. FACTUAL OBSERVATIONS
Give 3 observations based only on the numbers.

2. THINGS TO MONITOR
Give 3 areas the user should monitor.

3. PRACTICAL ACTIONS
Give 3 practical suggestions.

4. QUESTIONS
Give 1 useful question that would help improve the analysis.

Clearly separate facts from suggestions.
"""

    try:

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        response.raise_for_status()

        return response.json()["response"]

    except Exception as e:

        return f"""
Local AI is not currently available.

The finance dashboard itself is working.

To enable AI analysis:

1. Install Ollama.
2. Run:

   ollama pull qwen2.5:7b

3. Start Ollama.
4. Come back and click Generate AI Analysis.

Technical message:

{e}
"""


# ============================================================
# STREAMLIT INTERFACE
# ============================================================

init_db()

st.set_page_config(
    page_title="Personal Finance AI",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Personal Finance AI Agent")

st.caption(
    "Local-first personal finance tracker and AI analyst"
)

metrics = calculate_metrics()

# ------------------------------------------------------------
# TOP METRICS
# ------------------------------------------------------------

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Net Worth",
    f"₹{metrics['net_worth']:,.0f}"
)

c2.metric(
    "Cash Flow",
    f"₹{metrics['cashflow']:,.0f}"
)

c3.metric(
    "Portfolio",
    f"₹{metrics['portfolio_value']:,.0f}"
)

c4.metric(
    "Liabilities",
    f"₹{metrics['liabilities']:,.0f}"
)

# ------------------------------------------------------------
# TABS
# ------------------------------------------------------------

overview, transactions_tab, assets_tab, portfolio_tab, ai_tab = st.tabs([
    "📊 Overview",
    "💳 Transactions",
    "🏠 Assets & Debt",
    "📈 Portfolio",
    "🤖 AI Analyst"
])


# ============================================================
# OVERVIEW
# ============================================================

with overview:

    st.header("Financial Overview")

    st.subheader("Monthly Cash Flow")

    monthly = monthly_cashflow()

    if not monthly.empty:

        st.line_chart(
            monthly[
                ["income", "expense", "cashflow"]
            ]
        )

    else:

        st.info(
            "Add transactions to see your monthly cash flow."
        )

    st.subheader("Expense Categories")

    categories = expense_categories()

    if not categories.empty:

        st.bar_chart(categories)

    else:

        st.info(
            "Add expenses to see spending categories."
        )

    st.subheader("Current Financial Position")

    position = pd.DataFrame({
        "Metric": [
            "Income",
            "Expenses",
            "Cash Flow",
            "Assets",
            "Liabilities",
            "Net Worth",
            "Portfolio Value",
            "Portfolio Cost",
            "Portfolio P/L"
        ],

        "Amount": [
            metrics["income"],
            metrics["expenses"],
            metrics["cashflow"],
            metrics["assets"],
            metrics["liabilities"],
            metrics["net_worth"],
            metrics["portfolio_value"],
            metrics["portfolio_cost"],
            metrics["portfolio_profit"]
        ]
    })

    st.dataframe(
        position,
        use_container_width=True
    )


# ============================================================
# TRANSACTIONS
# ============================================================

with transactions_tab:

    st.header("Transactions")

    with st.form("transaction_form"):

        d = st.date_input(
            "Date",
            date.today()
        )

        description = st.text_input(
            "Description"
        )

        category = st.text_input(
            "Category",
            "Other"
        )

        amount = st.number_input(
            "Amount",
            min_value=0.0,
            step=100.0
        )

        typ = st.selectbox(
            "Type",
            ["expense", "income"]
        )

        account = st.text_input(
            "Account",
            "Bank"
        )

        notes = st.text_input(
            "Notes"
        )

        submitted = st.form_submit_button(
            "Save Transaction"
        )

        if submitted:

            if not description:

                st.error(
                    "Description is required."
                )

            elif amount <= 0:

                st.error(
                    "Amount must be greater than zero."
                )

            else:

                add_transaction(
                    str(d),
                    description,
                    category,
                    amount,
                    typ,
                    account,
                    notes
                )

                st.success(
                    "Transaction saved."
                )

    st.divider()

    st.subheader(
        "Import Transactions from CSV"
    )

    uploaded = st.file_uploader(
        "Choose CSV file",
        type=["csv"]
    )

    if uploaded is not None:

        if st.button("Import CSV"):

            df = pd.read_csv(uploaded)

            required = {
                "date",
                "description",
                "category",
                "amount",
                "type"
            }

            missing = required - set(df.columns)

            if missing:

                st.error(
                    "Missing columns: " +
                    ", ".join(missing)
                )

            else:

                for _, row in df.iterrows():

                    add_transaction(
                        str(row["date"]),
                        str(row["description"]),
                        str(row["category"]),
                        float(row["amount"]),
                        str(row["type"]),
                        str(row.get("account", "")),
                        str(row.get("notes", ""))
                    )

                st.success(
                    f"Imported {len(df)} transactions."
                )

    df = get_transactions()

    if not df.empty:

        st.dataframe(
            df,
            use_container_width=True
        )


# ============================================================
# ASSETS & DEBT
# ============================================================

with assets_tab:

    st.header("Assets")

    with st.form("asset_form"):

        name = st.text_input(
            "Asset Name"
        )

        category = st.text_input(
            "Asset Category",
            "Cash"
        )

        value = st.number_input(
            "Current Value",
            min_value=0.0,
            step=1000.0
        )

        as_of = st.date_input(
            "As Of",
            date.today(),
            key="asset_date"
        )

        notes = st.text_input(
            "Notes",
            key="asset_notes"
        )

        submitted = st.form_submit_button(
            "Save Asset"
        )

        if submitted and name:

            add_asset(
                name,
                category,
                value,
                str(as_of),
                notes
            )

            st.success(
                "Asset saved."
            )

    assets = get_assets()

    if not assets.empty:

        st.dataframe(
            assets,
            use_container_width=True
        )

    st.divider()

    st.header("Liabilities / Debt")

    with st.form("liability_form"):

        name = st.text_input(
            "Liability Name"
        )

        category = st.text_input(
            "Debt Category",
            "Loan"
        )

        balance = st.number_input(
            "Outstanding Balance",
            min_value=0.0,
            step=1000.0
        )

        interest = st.number_input(
            "Interest Rate %",
            min_value=0.0,
            step=0.1
        )

        emi = st.number_input(
            "EMI",
            min_value=0.0,
            step=100.0
        )

        as_of = st.date_input(
            "As Of",
            date.today(),
            key="debt_date"
        )

        notes = st.text_input(
            "Notes",
            key="debt_notes"
        )

        submitted = st.form_submit_button(
            "Save Liability"
        )

        if submitted and name:

            add_liability(
                name,
                category,
                balance,
                interest,
                emi,
                str(as_of),
                notes
            )

            st.success(
                "Liability saved."
            )

    liabilities = get_liabilities()

    if not liabilities.empty:

        st.dataframe(
            liabilities,
            use_container_width=True
        )


# ============================================================
# PORTFOLIO
# ============================================================

with portfolio_tab:

    st.header("Investment Portfolio")

    with st.form("holding_form"):

        symbol = st.text_input(
            "Symbol"
        )

        name = st.text_input(
            "Investment Name"
        )

        asset_class = st.selectbox(
            "Asset Class",
            [
                "Equity",
                "Mutual Fund",
                "ETF",
                "Bond",
                "Gold",
                "Crypto",
                "Other"
            ]
        )

        quantity = st.number_input(
            "Quantity",
            min_value=0.0,
            step=1.0
        )

        avg_cost = st.number_input(
            "Average Cost",
            min_value=0.0,
            step=1.0
        )

        current_price = st.number_input(
            "Current Price",
            min_value=0.0,
            step=1.0
        )

        as_of = st.date_input(
            "Price As Of",
            date.today(),
            key="holding_date"
        )

        notes = st.text_input(
            "Notes",
            key="holding_notes"
        )

        submitted = st.form_submit_button(
            "Save Holding"
        )

        if submitted and symbol and quantity > 0:

            add_holding(
                symbol,
                name,
                asset_class,
                quantity,
                avg_cost,
                current_price,
                str(as_of),
                notes
            )

            st.success(
                "Holding saved."
            )

    holdings = get_holdings()

    if not holdings.empty:

        holdings["value"] = (
            holdings["quantity"] *
            holdings["current_price"]
        )

        holdings["cost"] = (
            holdings["quantity"] *
            holdings["avg_cost"]
        )

        holdings["pnl"] = (
            holdings["value"] -
            holdings["cost"]
        )

        st.dataframe(
            holdings,
            use_container_width=True
        )

        st.subheader(
            "Portfolio Allocation"
        )

        allocation = holdings.groupby(
            "asset_class"
        )["value"].sum()

        st.bar_chart(
            allocation
        )

        st.metric(
            "Portfolio P/L",
            f"₹{holdings['pnl'].sum():,.0f}"
        )

    else:

        st.info(
            "Add your investment holdings above."
        )


# ============================================================
# AI ANALYST
# ============================================================

with ai_tab:

    st.header(
        "🤖 Local AI Financial Analyst"
    )

    st.write(
        "The AI receives calculated financial summaries. "
        "It does not need your bank password or brokerage credentials."
    )

    st.warning(
        "AI output is informational. Verify important financial "
        "decisions independently."
    )

    if st.button(
        "Generate AI Analysis"
    ):

        with st.spinner(
            "Analyzing your financial data locally..."
        ):

            result = generate_ai_analysis()

        st.markdown(
            result
        )
