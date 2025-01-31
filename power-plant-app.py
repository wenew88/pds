import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Power Plant Economic Analysis Dashboard",
    page_icon="⚡",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
        .stApp {
            background-color: #f5f7fa;
        }
        .metric-card {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .success-metric { color: #28a745; }
        .warning-metric { color: #ffc107; }
        .danger-metric { color: #dc3545; }
    </style>
""", unsafe_allow_html=True)

# Engine specifications
ENGINE_SPECS = {
    "Wärtsilä W16V25SG": {
        "power": 3000,
        "consumption": 777,
        "price": 6000000
    },
    "DHA": {
        "power": 315,
        "consumption": 84,
        "price": 2000000
    },
    "Jenbacher 612": {
        "power": 2200,
        "consumption": 444.30,
        "price": 5000000
    }
}

def load_data():
    df = pd.read_csv('d24.csv')
    # Convert column names to hours for better visualization
    df.columns = [f"Hour {i:02d}" for i in range(24)]
    return df

def calculate_metrics(engine_type, num_engines, load_percentage, gas_price, price_data, monthly_expenses):
    engine = ENGINE_SPECS[engine_type]
    
    # Basic calculations
    generation = engine["power"] * num_engines * (load_percentage / 100)
    consumption = engine["consumption"] * num_engines * (load_percentage / 100)
    investment = engine["price"] * num_engines * 1.2
    
    # Price analysis
    hourly_prices = price_data.values.flatten()
    min_price = hourly_prices.min()
    max_price = hourly_prices.max()
    avg_price = hourly_prices.mean()
    
    # Financial metrics
    total_monthly_expenses = sum(monthly_expenses.values())
    annual_revenue = generation * avg_price * 8760  # 8760 hours in a year
    monthly_revenue = annual_revenue / 12 - total_monthly_expenses
    
    # ROE and ROA
    roe = (annual_revenue / investment) * 100
    roa = (annual_revenue / (investment * 1.2)) * 100
    
    # Plant availability calculation
    total_hours = len(hourly_prices)
    operating_hours = len(hourly_prices[hourly_prices > min_price])
    availability = (operating_hours / total_hours) * 100
    
    return {
        "generation": generation,
        "consumption": consumption,
        "investment": investment,
        "monthly_revenue": monthly_revenue,
        "roe": roe,
        "roa": roa,
        "availability": availability,
        "min_price": min_price,
        "max_price": max_price,
        "avg_price": avg_price
    }

def main():
    st.title("⚡ Power Plant Economic Analysis Dashboard")
    
    # Load data
    df = load_data()
    
    # Sidebar for inputs
    with st.sidebar:
        st.header("Configuration")
        
        # Engine selection
        engine_type = st.selectbox(
            "Select Engine Type",
            list(ENGINE_SPECS.keys())
        )
        
        num_engines = st.number_input(
            "Number of Engines",
            min_value=1,
            value=1
        )
        
        load_percentage = st.slider(
            "Load Percentage",
            min_value=0,
            max_value=100,
            value=100
        )
        
        gas_price = st.number_input(
            "Gas Price (per m³)",
            min_value=0.0,
            value=1.0,
            step=0.1
        )
        
        st.header("Monthly Expenses")
        monthly_expenses = {
            "Oil": st.number_input("Oil", value=32800),
            "Service and Parts": st.number_input("Service and Parts", value=41000),
            "Workers": st.number_input("Workers (3)", value=49200),
            "Salary Taxes": st.number_input("Salary Taxes (22%)", value=10824),
            "Other Expenses": st.number_input("Other Expenses", value=61500)
        }

    # Main content area
    metrics = calculate_metrics(engine_type, num_engines, load_percentage, gas_price, df, monthly_expenses)
    
    # Display key metrics in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Generation (kWe)", f"{metrics['generation']:,.2f}")
        st.metric("Investment + 20%", f"{metrics['investment']:,.2f}")
    
    with col2:
        st.metric("ROE", f"{metrics['roe']:.2f}%")
        st.metric("ROA", f"{metrics['roa']:.2f}%")
    
    with col3:
        st.metric("Plant Availability", f"{metrics['availability']:.2f}%")
        st.metric("Monthly Revenue", f"{metrics['monthly_revenue']:,.2f}")

    # Price analysis visualization
    st.header("Price Analysis")
    
    # Create hourly price heatmap
    fig = px.imshow(
        df,
        labels=dict(x="Hour of Day", y="Day", color="Price"),
        title="Hourly Price Heatmap",
        color_continuous_scale="Viridis"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Price distribution
    fig_dist = go.Figure()
    fig_dist.add_trace(go.Histogram(x=df.values.flatten(), nbinsx=50))
    fig_dist.update_layout(
        title="Price Distribution",
        xaxis_title="Price",
        yaxis_title="Frequency"
    )
    st.plotly_chart(fig_dist, use_container_width=True)
    
    # Display daily statistics
    st.header("Daily Statistics")
    daily_stats = pd.DataFrame({
        'Min Price': df.min(axis=1),
        'Max Price': df.max(axis=1),
        'Average Price': df.mean(axis=1)
    })
    st.line_chart(daily_stats)

    # Financial summary
    st.header("Financial Summary")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Monthly Expenses")
        fig_expenses = px.pie(
            values=list(monthly_expenses.values()),
            names=list(monthly_expenses.keys()),
            title="Monthly Expenses Distribution"
        )
        st.plotly_chart(fig_expenses, use_container_width=True)
    
    with col2:
        st.subheader("Key Financial Metrics")
        metrics_df = pd.DataFrame({
            'Metric': ['Monthly Revenue', 'ROE', 'ROA', 'Plant Availability'],
            'Value': [
                f"{metrics['monthly_revenue']:,.2f}",
                f"{metrics['roe']:.2f}%",
                f"{metrics['roa']:.2f}%",
                f"{metrics['availability']:.2f}%"
            ]
        })
        st.table(metrics_df)

if __name__ == "__main__":
    main()