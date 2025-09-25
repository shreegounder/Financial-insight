import streamlit as st
from llm_tools import analyze_comp, stream_analyze_comp
from utils import get_top_n_companies, get_company_data
import plotly.graph_objects as go
import streamlit as st

def main():
    st.title("DeepSeek Financial Analysis")
    
    # Sidebar for company selection
    st.sidebar.header("Company Selection")
    companies = get_top_n_companies(100)

    if "selected_company" not in st.session_state:
        st.session_state.selected_company = list(companies.keys())[0]  # Default first company
        st.session_state.company_data = get_company_data(st.session_state.selected_company)

    selected_company = st.sidebar.selectbox("Choose a company", list(companies.keys()), index=list(companies.keys()).index(st.session_state.selected_company))

    # Update session state when selection changes
    if selected_company != st.session_state.selected_company:
        st.session_state.selected_company = selected_company
        st.session_state.company_data = get_company_data(selected_company)

    company_data = st.session_state.company_data

    # Display basic company info
    st.header(f"Analysis for {companies[selected_company]} ({selected_company})")
    
    st.subheader("Company Overview")
    st.write(f"Industry: {company_data[selected_company]['assetProfile']['industry']}")
    st.write(f"Sector: {company_data[selected_company]['assetProfile']['sector']}")
    st.write(f"Current Stock Price: ${company_data[selected_company]['price']['regularMarketPrice']:.2f}")

    # Financial Health Indicators
    st.subheader("Financial Health")
    col1, col2, col3 = st.columns(3)
    col1.metric("Revenue", f"${company_data[selected_company]['financialData']['totalRevenue'] / 1_000_000:,.2f}M")
    col2.metric("EBITDA", f"${company_data[selected_company]['financialData']['ebitda'] / 1_000_000:,.2f}M")
    col3.metric("Profit Margin", f"{company_data[selected_company]['financialData']['profitMargins']:.2%}")

    # Stock Price Chart
    st.subheader("Stock Price History")
    historical_data = company_data[selected_company]['historical_price']
    fig = go.Figure(data=go.Scatter(x=historical_data['date'], y=historical_data['close'], mode="lines", name="Stock Price"))
    st.plotly_chart(fig)

    st.subheader("AI-Powered Analysis")
    if st.button("Generate Analysis"):
            analysis_placeholder = st.empty()
            analysis_placeholder.text("Generating analysis...")
            
            for chunk in analyze_comp(selected_company):
                analysis_placeholder.markdown(chunk)

if __name__ == "__main__":
    main()
