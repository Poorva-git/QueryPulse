"""
chart_generator.py - Auto-generates Plotly charts based on data columns
"""
from typing import Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def generate_auto_chart(data: list) -> Optional[go.Figure]:
    if not data or len(data) == 0:
        return None

    df = pd.DataFrame(data)
    if len(df) == 0 or len(df.columns) < 2:
        return None

    # Separate numeric and non-numeric columns
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    non_numeric_cols = df.select_dtypes(exclude=["number"]).columns.tolist()

    if not numeric_cols:
        return None

    y_col = numeric_cols[0]  # First numeric column for values

    # 1. Agar koi date / time column hai -> Line chart
    date_cols = [col for col in non_numeric_cols if "date" in col.lower() or "year" in col.lower() or "month" in col.lower()]
    if date_cols:
        x_col = date_cols[0]
        fig = px.line(
            df.head(50), 
            x=x_col, 
            y=y_col, 
            title=f"{y_col.replace('_', ' ').title()} over {x_col.replace('_', ' ').title()}",
            template="plotly_white"
        )
        return fig

    # 2. Agar categorical / text column hai -> Bar chart
    if non_numeric_cols:
        x_col = non_numeric_cols[0]
        fig = px.bar(
            df.head(20),  # Top 20 for readability
            x=x_col, 
            y=y_col, 
            title=f"{y_col.replace('_', ' ').title()} by {x_col.replace('_', ' ').title()}",
            template="plotly_white",
            color=y_col,
            color_continuous_scale="Blues"
        )
        return fig

    return None