import streamlit as st
from llm_tools import analyze_comp
from utils import get_top_n_companies, get_company_data
import plotly.graph_objects as go
from fpdf import FPDF
import base64

def generate_pdf(company_name, company_data, analysis_text):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", style='B', size=16)
    pdf.cell(200, 10, f"Financial Report: {company_name}", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"Industry: {company_data['assetProfile']['industry']}", ln=True)
    pdf.cell(200, 10, f"Sector: {company_data['assetProfile']['sector']}", ln=True)
    pdf.cell(200, 10, f"Current Stock Price: ${company_data['price']['regularMarketPrice']:.2f}", ln=True)
    pdf.ln(5)
    
    pdf.cell(200, 10, "Financial Health:", ln=True, style='B')
    pdf.cell(200, 10, f"Revenue: ${company_data['financialData']['totalRevenue'] / 1_000_000:,.2f}M", ln=True)
    pdf.cell(200, 10, f"EBITDA: ${company_data['financialData']['ebitda'] / 1_000_000:,.2f}M", ln=True)
    pdf.cell(200, 10, f"Profit Margin: {company_data['financialData']['profitMargins']:.2%}", ln=True)
    pdf.ln(5)
    
    pdf.cell(200, 10, "AI-Powered Analysis:", ln=True, style='B')
    pdf.multi_cell(0, 10, analysis_text)
    
    pdf_output = f"{company_name}_financial_report.pdf"
    pdf.output(pdf_output)
    
    return pdf_output

def main():
    st.title("DeepSeek Financial Analysis")
    
    st.sidebar.header("Company Selection")
    companies = get_top_n_companies(100)

    if "selected_company" not in st.session_state:
        st.session_state.selected_company = list(companies.keys())[0]
        st.session_state.company_data = get_company_data(st.session_state.selected_company)

    selected_company = st.sidebar.selectbox("Choose a company", list(companies.keys()), index=list(companies.keys()).index(st.session_state.selected_company))

    if selected_company != st.session_state.selected_company:
        st.session_state.selected_company = selected_company
        st.session_state.company_data = get_company_data(selected_company)

    company_data = st.session_state.company_data
    
    st.header(f"Analysis for {companies[selected_company]} ({selected_company})")
    
    st.subheader("Company Overview")
    st.write(f"Industry: {company_data[selected_company]['assetProfile']['industry']}")
    st.write(f"Sector: {company_data[selected_company]['assetProfile']['sector']}")
    st.write(f"Current Stock Price: ${company_data[selected_company]['price']['regularMarketPrice']:.2f}")
    
    st.subheader("Financial Health")
    col1, col2, col3 = st.columns(3)
    col1.metric("Revenue", f"${company_data[selected_company]['financialData']['totalRevenue'] / 1_000_000:,.2f}M")
    col2.metric("EBITDA", f"${company_data[selected_company]['financialData']['ebitda'] / 1_000_000:,.2f}M")
    col3.metric("Profit Margin", f"{company_data[selected_company]['financialData']['profitMargins']:.2%}")
    
    st.subheader("Stock Price History")
    historical_data = company_data[selected_company]['historical_price']
    fig = go.Figure(data=go.Scatter(x=historical_data['date'], y=historical_data['close'], mode="lines", name="Stock Price"))
    st.plotly_chart(fig)
    
    st.subheader("AI-Powered Analysis")
    analysis_text = ""
    if st.button("Generate Analysis"):
        analysis_placeholder = st.empty()
        analysis_placeholder.text("Generating analysis...")
        for chunk in analyze_comp(selected_company):
            analysis_text += chunk + "\n"
            analysis_placeholder.markdown(analysis_text)
    
    if analysis_text:
        pdf_file = generate_pdf(selected_company, company_data[selected_company], analysis_text)
        with open(pdf_file, "rb") as f:
            pdf_bytes = f.read()
            b64_pdf = base64.b64encode(pdf_bytes).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64_pdf}" download="{pdf_file}">Download PDF Report</a>'
            st.markdown(href, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
