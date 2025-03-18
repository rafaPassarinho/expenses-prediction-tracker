import streamlit as st
import pandas as pd
import datetime
import calendar

from datetime import date, timedelta
from collections import defaultdict

st.set_page_config(
    page_title="Termômetro Financeiro",
    layout="wide")

if 'fixed_expenses' not in st.session_state:
    st.session_state.fixed_expenses = {}
if 'gastos_fixos' not in st.session_state:
    st.session_state.gastos_fixos = pd.DataFrame(columns=['Dia', 'Descrição', 'Valor'])
if 'transacoes' not in st.session_state:
    st.session_state.transacoes = pd.DataFrame(columns=['Dia', 'Entrada', 'Saída', 'Diário', 'Saldo', 'Descrição'])

def add_fixed_expense(day, description, amount):
    if day in st.session_state.fixed_expenses:
        st.session_state.fixed_expenses[day].append((description, amount))
    else:
        st.session_state.fixed_expenses[day] = [(description, amount)]

def load_data():
    try:
        transacoes = pd.read_csv(rf'data/transacoes.csv', parse_dates=['Dia'])
        gastos_fixos = pd.read_csv(rf'data/gastos_fixos.csv', parse_dates=['Dia'])
        return transacoes, gastos_fixos
    except FileNotFoundError:
        return pd.DataFrame(), pd.DataFrame()

def save_data(transacoes, gastos_fixos):
    transacoes.to_csv(rf'data/transacoes.csv', index=False)
    gastos_fixos.to_csv(rf'data/gastos_fixos.csv', index=False)

def main():

    st.title('🌡️💰 Termômetro Financeiro')
    with st.expander('ℹ️ Sobre o app'):
        st.write('''
        Este app permite criar, modificar e visualizar sua planilha de gastos mensais e diários.
        ''')
    transacoes, gastos_fixos = load_data()
    if transacoes.empty:
        with st.form(key='expenses_form'):
            st.header('Adicione Novo Gasto Fixo')

            day = st.selectbox('Dia do mês:', list(range(1, 32)), index=29)
            description = st.text_input('Descrição:')
            amount = st.number_input('Valor:', min_value=0.0, format='%.2f')
            submitted = st.form_submit_button(label='Adicionar Gasto')
        if submitted:
            if description and amount > 0:
                add_fixed_expense(day, description, amount)
                st.success(f'Adicionado {description} (R$ {amount:.2f}) no dia {day}.')
            else:
                st.error('Por favor, preencha todos os campos.')
        with st.expander('📅 Gastos Fixos'):
            for day, expenses in st.session_state.fixed_expenses.items():
                st.write(f'**Dia {day}**')
                for description, amount in expenses:
                    st.write(f'- {description} (R$ {amount:.2f})')
        fixed_expenses_dict = {day: sum(amount for _, amount in expenses) for day, expenses in st.session_state.fixed_expenses.items()}
        gastos_fixos = pd.DataFrame([(day, description, amount) for day, expenses in st.session_state.fixed_expenses.items() for description, amount in expenses], columns=['Dia', 'Descrição', 'Valor'])

        with st.form(key='create_expenses_form'):
            st.header('Insira informações iniciais')
            saldo_inicial = st.number_input('Saldo inicial:', value=1000)
            data_salario = st.selectbox('Dia do salário:', list(range(1, 32)), index=29) 
            valor_salario = st.number_input('Valor do salário:', value=1000.0)
            gasto_diario = st.number_input('Gasto diário:', value=30.0, min_value=0.0, step=0.01)
            submit_button = st.form_submit_button(label='Criar planilha')
        if submit_button:
            st.write('''
            ## **Planilha Financeira**
            ''')
            transacoes = defaultdict(list)
            dates = [(date.today() + timedelta(days=x)) for x in range((date(date.today().year, 12, 31) - date.today()).days + 1)]
            saldo_atual = saldo_inicial
            for dia in dates:
                description_actions = []
                entrada = 0
                saida = 0
                if dia.day == data_salario:
                    saldo_atual += valor_salario
                    entrada = valor_salario
                    description_actions.append('Salário')
                if dia.day in fixed_expenses_dict:
                    saldo_atual -= fixed_expenses_dict[dia.day]
                    saida = fixed_expenses_dict[dia.day]
                    for description, amount in st.session_state.fixed_expenses[dia.day]:
                        description_actions.append(description)
                saldo_atual -= gasto_diario
                description_actions.append('Gasto diário')
                transacoes['Dia'].append(dia)
                transacoes['Entrada'].append(entrada)
                transacoes['Saída'].append(saida)
                transacoes['Saldo'].append(saldo_atual)
                transacoes['Descrição'].append(' + '.join(description_actions))
    else:
        df = pd.DataFrame(transacoes)
        st.write(df)
        st.write(gastos_fixos)
        st.line_chart(data=df, x='Dia', y='Saldo')

        # for dia in range(1, calendar.monthrange(date.today().year, date.today().month)[1] + 1):
        #     if dia == data_salario:
        #         saldo_atual += valor_salario
        #         transacoes['Dia'].append(dia)
        #         transacoes['Descrição'].append('Salário')
        #         transacoes['Valor'].append(valor_salario)
        #         transacoes['Saldo'].append(saldo_atual)
        #     else:
        #         saldo_atual -= gasto_diario
        #         transacoes['Dia'].append(dia)
        #         transacoes['Descrição'].append('Gasto diário')
        #         transacoes['Valor'].append(-gasto_diario


        

if __name__ == '__main__':
    main()