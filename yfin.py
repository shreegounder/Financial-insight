import streamlit as st
import yfinance as yf
import pandas as pd

def fetch_financials(ticker):
    try:
        stock = yf.Ticker(ticker)
        income_stmt = stock.financials
        balance_sheet = stock.balance_sheet
        cash_flow = stock.cashflow
        return income_stmt, balance_sheet, cash_flow
    except Exception as e:
        return str(e), None, None

def main():
    st.title("Stock Financials Viewer")
    ticker = st.text_input("Enter Stock Ticker (e.g., MSFT, AAPL, GOOGL):")
    
    if ticker:
        income_stmt, balance_sheet, cash_flow = fetch_financials(ticker)
        
        if isinstance(income_stmt, str):
            st.error(f"Error: {income_stmt}")
        else:
            st.subheader("Income Statement")
            st.dataframe(income_stmt)
            
            st.subheader("Balance Sheet")
            st.dataframe(balance_sheet)
            
            st.subheader("Cash Flow Statement")
            st.dataframe(cash_flow)
            
            csv = income_stmt.to_csv().encode('utf-8')
            st.download_button("Download Income Statement as CSV", data=csv, file_name=f"{ticker}_income_statement.csv", mime='text/csv')
            
            csv = balance_sheet.to_csv().encode('utf-8')
            st.download_button("Download Balance Sheet as CSV", data=csv, file_name=f"{ticker}_balance_sheet.csv", mime='text/csv')
            
            csv = cash_flow.to_csv().encode('utf-8')
            st.download_button("Download Cash Flow Statement as CSV", data=csv, file_name=f"{ticker}_cash_flow.csv", mime='text/csv')

if __name__ == "__main__":
    main()
