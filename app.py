import streamlit as st
import pandas as pd

st.set_page_config(page_title="THD 提成测算看板", layout="wide")

# ----------------- 提点规则定义 -----------------
def get_senior_op_rate(x):
    """Valerie（高级运营）全额提点率 (X: 万美金)"""
    if x <= 0:
        return 0.0
    elif x <= 10:
        return 0.0
    elif x <= 40:
        return 0.003
    elif x <= 60:
        return 0.0035
    elif x <= 80:
        return 0.004
    elif x <= 150:
        return 0.005
    else:
        return 0.008

def get_junior_op_rate(x):
    """June & Zoey（初级运营）全额提点率 (X: 万美金)"""
    if x <= 0:
        return 0.0
    elif x <= 8:
        return 0.0
    elif x <= 20:
        return 0.001
    elif x <= 30:
        return 0.0015
    else:
        return 0.0015

# 表头高亮渲染辅助函数
def render_custom_table(df, format_dict, highlight_cols, red_cols=[]):
    """自定义 HTML 表格渲染，用于高亮特定表头并保留负数变红逻辑"""
    df_formatted = df.copy()
    
    # 格式化数值字段
    for col, fmt in format_dict.items():
        if col in df_formatted.columns:
            df_formatted[col] = df_formatted[col].apply(lambda v: fmt.format(v) if isinstance(v, (int, float)) else v)

    # 转换 HTML
    html = "
