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
            fixed_expenses_dict[day] = list(zip(group['Descrição'], group['Valor']))
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


def add_fixed_expense(day, amount, description):
    if day in st.session_state.fixed_expenses:
        st.session_state.fixed_expenses[day].append((amount, description))
    else:
        st.session_state.fixed_expenses[day] = [(amount, description)]

def main():
    st.title('🌡️💰 Termômetro Financeiro')

    transactions_df, fixed_expenses_df = load_data()
    
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
                new_fixed_expense = pd.DataFrame({
                    'Dia': [day],
                    'Descrição': [description],
                    'Valor': [amount]
                })
                fixed_expenses_df = pd.concat([fixed_expenses_df, new_fixed_expense], ignore_index=True)
                st.write(fixed_expenses_df)
                save_data()
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
            st.write(fixed_expenses_df)
        else:
            st.write('Nenhuma despesa fixa cadastrada até o momento.')
    with tab3:
        st.subheader('Criar Nova Planilha Financeira')
if __name__ == '__main__':
    main()