import streamlit as st
import pandas as pd
import datetime
import calendar
import os

from datetime import date, timedelta

st.set_page_config(
    page_title="Termômetro Financeiro",
    layout="wide")

DATA_DIR = 'data'
TRANSACTIONS_FILE = os.path.join(DATA_DIR, 'transacoes.csv')
FIXED_EXPENSES_FILE = os.path.join(DATA_DIR, 'despesas_fixas.csv')

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# initialize session state
if 'fixed_expenses_dict' not in st.session_state:
    st.session_state.fixed_expenses_dict = {}

if 'transactions_dict' not in st.session_state:
    st.session_state.transactions_dict = {}

# fixed expenses dict conversion functions
def fixed_expenses_dict_to_df(fixed_expenses_dict):
    rows = []
    for day, expenses in fixed_expenses_dict.items():
        for amount, description in expenses:
            print(day, description, amount)
            rows.append({
                'Dia': int(day),
                'Descrição': description,
                'Valor': float(amount)
            })
    return pd.DataFrame(rows)

def fixed_expenses_df_to_dict(fixed_expenses_df):
    fixed_expenses_dict = {}
    if not fixed_expenses_df.empty:
        for day, group in fixed_expenses_df.groupby('Dia'):
            fixed_expenses_dict[day] = list(zip(group['Valor'], group['Descrição']))
    return fixed_expenses_dict

# transactions dict conversion functions
def transactions_dict_to_df(transactions_dict):
    rows = []
    for date_str, transactions in transactions_dict.items():
        rows.append({
            'Dia': date_str,
            'Entrada': float(transactions.get('Entrada', 0)),
            'Saída': float(transactions.get('Saída', 0)),
            'Diário': float(transactions.get('Diário', 0)),
            'Saldo': float(transactions.get('Saldo', 0)),
            'Descrição': transactions.get('Descrição', '')
        })
    return pd.DataFrame(rows)

def transactions_df_to_dict(transactions_df):
    transactions_dict = {}
    if not transactions_df.empty:
        for _, row in transactions_df.iterrows():
            date_str = row['Dia']
            transactions_dict[date_str] = {
                'Entrada': float(row['Entrada']),
                'Saída': float(row['Saída']),
                'Diário': float(row['Diário']),
                'Saldo': float(row['Saldo']),
                'Descrição': row['Descrição']
            }
    return transactions_dict

# load data from CSV files
def load_data():
    if os.path.exists(FIXED_EXPENSES_FILE):
        fixed_expenses_df = pd.read_csv(FIXED_EXPENSES_FILE)
        st.session_state.fixed_expenses_dict = fixed_expenses_df_to_dict(fixed_expenses_df)
    
    if os.path.exists(TRANSACTIONS_FILE):
        transactions_df = pd.read_csv(TRANSACTIONS_FILE)
        st.session_state.transactions_dict = transactions_df_to_dict(transactions_df)

def save_data():
    # convert dicts to DataFrames for saving
    fixed_expenses_df = fixed_expenses_dict_to_df(st.session_state.fixed_expenses_dict)
    if not fixed_expenses_df.empty:
        fixed_expenses_df.to_csv(FIXED_EXPENSES_FILE, index=False)
    
    transactions_df = transactions_dict_to_df(st.session_state.transactions_dict)
    if not transactions_df.empty:
        transactions_df.to_csv(TRANSACTIONS_FILE, index=False)

# add functions for each data type
def add_fixed_expense(day, amount, description):
    if day in st.session_state.fixed_expenses_dict:
        st.session_state.fixed_expenses_dict[day].append((amount, description))
    else:
        st.session_state.fixed_expenses_dict[day] = [(amount, description)]
    save_data()

def add_transaction(date_str, amount, type, description):
    pass

def main():
    st.title('🌡️💰 Termômetro Financeiro')

    # load data
    load_data()
    fixed_expenses_df = fixed_expenses_dict_to_df(st.session_state.fixed_expenses_dict)
    transactions_df = transactions_dict_to_df(st.session_state.transactions_dict)
    
    # sidebar controls
    with st.sidebar:
        st.header('Adicionar Transação')

        st.header('Adicionar Despesa Fixa')
        day = st.selectbox('Dia do mês', list(range(1, 32)), index=0)
        description = st.text_input('Descrição')
        amount = st.number_input('Valor', min_value=0.0, step=10.0, format='%.2f')
        add_submit = st.button('Adicionar Despesa Fixa')

        if add_submit:
            if description and amount > 0:
                add_fixed_expense(day, amount, description)
                fixed_expenses_df = fixed_expenses_dict_to_df(st.session_state.fixed_expenses_dict)
                st.success(f'Adicionado {description} (R$ {amount:.2f}) no dia {day}.')
            else:
                st.error('Por favor, preencha todos os campos.')

    # Main display
    with st.expander('ℹ️ Informações Gerais'):
        st.write('Este é o Termômetro Financeiro, uma aplicação para controle de gastos e previsão de saldo.')
        st.write('Aqui você pode adicionar despesas fixas, despesas diárias e visualizar o saldo atual e previsões futuras.')
        st.write('Para começar, clique em uma das abas abaixo.')        
    tab1, tab2, tab3 = st.tabs(['Dashboard', 'Despesas Fixas', 'Criar Planilha Financeira'])

    with tab1:
        st.subheader('Planilha de Gastos')
    
    with tab2:
        st.subheader('Despesas Fixas')
        if not fixed_expenses_df.empty:
            st.dataframe(fixed_expenses_df, hide_index=True)
            col1, col2 = st.columns(2)
            col1.subheader('Despesas Fixas por Dia')
            daily_expenses = fixed_expenses_df.groupby('Dia')['Valor'].sum()
            col1.write(daily_expenses)
            col2.subheader(f'Total de Despesas Fixas R${fixed_expenses_df["Valor"].sum():.2f}')
            
        else:
            st.write('Nenhuma despesa fixa cadastrada até o momento.')
    with tab3:
        st.subheader('Criar Nova Planilha Financeira')
if __name__ == '__main__':
    main()