from langchain_community.llms import Ollama
import re
from utils import *

llm = Ollama(model="deepseek-r1:1.5b")
all_comps = get_top_n_companies(250)


def remove_think(text_lst):
    """
    Removes text between <think> tags from a list of strings.
    
    Args:
        text_lst (list): List of strings containing potential <think> tags
        
    Returns:
        list: List of strings with <think> tag content removed
    """
    result = []
    for text in text_lst:
        result.append(re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL))
    return result


def analyze(messages: list):
    """
    Processes a list of messages through an LLM to analyze a company.
    
    Args:
        messages (list): List of prompts/messages to process sequentially
        
    Returns:
        list: Accumulated responses from the LLM with thinking tags removed
    """
    memory_buffer = []
    for mes in messages:
        memory = prompts['memory'].format(memory=remove_think(memory_buffer))
        result = llm.invoke(memory + mes)
        logging.info(result)
        memory_buffer.extend(remove_think([result]))

    return memory_buffer


def stream_analyze(messages: list):
    """
    Processes a list of messages through an LLM to analyze a company.

    Args:
        messages (list): List of prompts/messages to process sequentially

    Returns:
        list: Accumulated responses from the LLM with thinking tags removed
    """
    memory_buffer = []
    for mes in messages:
        memory = prompts['memory'].format(memory=remove_think(memory_buffer))
        stream = llm.stream(memory + mes)

        response_text = ""
        for chunk in stream:
            response_text += chunk  # Accumulate chunks
            yield chunk

        memory_buffer.extend(remove_think([response_text]))

    return memory_buffer


def build_prompts(comp_data, symbol):
    """
    Constructs a series of analysis prompts using company data.
    
    Args:
        comp_data (dict): Dictionary containing company financial and market data
        symbol (str): Company stock symbol
        
    Returns:
        list: Formatted prompts for company analysis including overview, health check,
             financial stability, valuation, and market sentiment
    """
    data = comp_data[symbol]
    raw_hist_data = process_historical_data(data['historical_price'])
    messages = [
        prompts['company-overview-agent'].format(
            symbol=symbol + ':' + all_comps[symbol],
            industry=data['assetProfile']['industry'],
            sector=data['assetProfile']['sector'],
            current_stock_price=data['price']['regularMarketPrice'],
            market_cap=data['price']['marketCap'],
            trend=define_trend(data['price']['regularMarketChange'])
        ),
        prompts['health-check-agent'].format(
            revenue=data['financialData']['totalRevenue'],
            net_income=data['financialData']['totalRevenue'] * data['financialData']['profitMargins'],
            eps_trends=get_eps_trend(data['income_statement']),
            ebitda=data['financialData']['ebitda'],
            operating_margin=data['financialData']['operatingMargins'],
            profit_margin=data['financialData']['profitMargins']
        ),
        prompts['financial-stability-agent'].format(
            input=compute_financial_metrics(data['balance_sheet'], data['cash_flow'])
        ),
        prompts['valuation-agent'].format(
            pe_ratio_trailing=data['summaryDetail']['trailingPE'],
            pe_ratio_forward=data['defaultKeyStatistics']['forwardPE'],
            pb_ratio=data['defaultKeyStatistics']['priceToBook'],
            peg_ratio=data['summaryDetail']['trailingPE'] / data['defaultKeyStatistics']['earningsQuarterlyGrowth'],
            ev_ebitda=data['defaultKeyStatistics']['enterpriseToEbitda'],
            dividend_yield=data['summaryDetail']['dividendYield'],
            market_cap=data['summaryDetail']['marketCap']
        ),
        prompts['market-sentiment-agent'].format(
            analyst_rate=data['recommendationTrend']['trend'][0],
            hist_data=filter_financial_summary(raw_hist_data),
            sentiment=define_sentiment(raw_hist_data)
        ),
        # prompts['risk-analyze-agent'].format(
        #     competition="",
        #     regulatory_risk="",
        #     macroeconomic=""
        # ),
        prompts['decision-making-agent']
    ]

    return messages


def analyze_comp(symbol):
    """
    Overall function to analyze a company with given symbol.
    :param symbol: company symbol, e.g. AAPL
    :return:
    """
    temp = get_company_data(symbol)
    messages = build_prompts(temp, symbol)
    analysis = analyze(messages)
    with open(f"./data/{symbol}_analysis.md", "w") as file:
        file.write("\n".join(analysis))
    return analysis


def stream_analyze_comp(symbol):
    """
    Streams company analysis results instead of waiting for all responses.

    Args:
        symbol (str): Company stock symbol

    Yields:
        str: Streamed responses as they arrive
    """
    temp = get_company_data(symbol)
    messages = build_prompts(temp, symbol)

    with open(f"./data/{symbol}_analysis.md", "w") as file:
        for response in stream_analyze(messages):
            file.write(response + "\n")
            yield response  # Stream each response

    logging.info(f"Analysis completed for {symbol}")
