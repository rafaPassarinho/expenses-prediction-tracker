import streamlit as st
import pandas as pd
import datetime
import calendar
import os
import plotly.express as px
import plotly.graph_objects as go

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
    if type not in ['Entrada', 'Saída', 'Diário']:
        st.error("Tipo inválido. Use 'Entrada', 'Saída' ou 'Diário'.")
        return
    
    from datetime import datetime
    current_date = datetime.strptime(date_str, '%d/%m/%Y')

    if date_str not in st.session_state.transactions_dict:
        st.session_state.transactions_dict[date_str] = {
            'Entrada': 0.0,
            'Saída': 0.0,
            'Diário': 0.0,
            'Saldo': 0.0,
            'Descrição': description
        }
    
    # Calculate the difference this transaction will make to the balance
    old_value = st.session_state.transactions_dict[date_str][type]
    
    # Update the specified column
    st.session_state.transactions_dict[date_str][type] = amount
    
    # If description provided, update or append it
    if description or description == '':
        # If description is empty, remove 'Gasto Diário' if present
        if description == '':
            description = st.session_state.transactions_dict[date_str]['Descrição']
            if 'Gasto Diário' in description:
                description = description.replace('Gasto Diário', '')
        if st.session_state.transactions_dict[date_str]['Descrição']:
            # Append to existing description removing 'Gasto Diário' if present
            if 'Gasto Diário' in st.session_state.transactions_dict[date_str]['Descrição']:
                st.session_state.transactions_dict[date_str]['Descrição'] = st.session_state.transactions_dict[date_str]['Descrição'].replace('Gasto Diário', '')
                st.session_state.transactions_dict[date_str]['Descrição'] += f'{description}'
            else:
                st.session_state.transactions_dict[date_str]['Descrição'] += f" + {description}"
        else:
            st.session_state.transactions_dict[date_str]['Descrição'] = description
    
    # Get all dates and sort chronologically
    all_dates = list(st.session_state.transactions_dict.keys())
    all_dates.sort(key=lambda d: datetime.strptime(d, '%d/%m/%Y'))
    
    # Find current date's position in the sorted list
    if date_str in all_dates:
        current_index = all_dates.index(date_str)
    else:
        # If date somehow isn't in the list, add it
        all_dates.append(date_str)
        all_dates.sort(key=lambda d: datetime.strptime(d, '%d/%m/%Y'))
        current_index = all_dates.index(date_str)
    
    # Update current day's balance and all future balances sequentially
    for i in range(current_index, len(all_dates)):
        current_date = all_dates[i]
        
        if i > 0:
            # Get previous day's balance
            prev_date = all_dates[i-1]
            prev_balance = st.session_state.transactions_dict[prev_date]['Saldo']
            
            # Calculate new balance
            entrada = st.session_state.transactions_dict[current_date]['Entrada']
            saida = st.session_state.transactions_dict[current_date]['Saída']
            diario = st.session_state.transactions_dict[current_date]['Diário']
            
            # Calculate daily net
            daily_net = entrada - saida - diario
            
            # Update balance
            st.session_state.transactions_dict[current_date]['Saldo'] = prev_balance + daily_net
        else:
            # For the first date in the sequence, there's no previous balance
            entrada = st.session_state.transactions_dict[current_date]['Entrada']
            saida = st.session_state.transactions_dict[current_date]['Saída']
            diario = st.session_state.transactions_dict[current_date]['Diário']
            
            # Set balance directly
            st.session_state.transactions_dict[current_date]['Saldo'] = entrada - saida - diario
    
    # Save the updated data
    save_data()

def parse_amount_expression(expression):
    try:
        clean_expr = expression.replace(',', '.')

        import re
        if not re.match(r'^[\d\.\+\-\*\/\(\)\s]+$', clean_expr):
            raise ValueError("Invalid characters in expression")
        
        result = eval(clean_expr)
        return float(result)
    except Exception as e:
        st.error(f"Erro ao calcular a expressão: {e}")
        return 0.0


def is_business_day(day):
    return day.weekday() < 5 # 0-4 are business days, 5-6 are weekend days

def get_fifth_business_day(year, month):
    bussiness_days = 0
    day = 1

    # get the maximum number of days in the month
    _, last_day = calendar.monthrange(year, month)

    # iterate through days until we reach the fifth business day
    while bussiness_days < 5 and day <= last_day:
        current_date = date(year, month, day)
        if is_business_day(current_date):
            bussiness_days += 1
        if bussiness_days == 5:
            return current_date
        day += 1
    return None

def get_last_business_day(year, month):
    _, last_day = calendar.monthrange(year, month)
    
    # start from the last day of the month and go backwards until we find a business day
    current_day = last_day
    while current_day > 0:
        current_date = date(year, month, current_day)
        if is_business_day(current_date):
            return current_date
        current_day -= 1
    return None
    
def color_by_value(val):
    if val > 2000:
        color = 'green'
    elif 1000 <= val <= 2000:
        color = 'lightgreen'
    elif 0 <= val < 1000:
        color = 'orange'
    else:
        color = 'red'
    return f'background-color: {color}; color: white;'

def main():
    st.title('🌡️💰 Termômetro Financeiro')

    # load data
    load_data()
    fixed_expenses_df = fixed_expenses_dict_to_df(st.session_state.fixed_expenses_dict)
    transactions_df = transactions_dict_to_df(st.session_state.transactions_dict)
    
    # sidebar controls
    with st.sidebar:
        st.header('Adicionar Transação')
        with st.form(key='add_transaction_form'):
            col1, col2 = st.columns(2)

            transaction_date = col1.date_input('Data', value=date.today())
            transaction_type = col2.selectbox('Tipo', ['Entrada', 'Saída', 'Diário'])

            transaction_amount_str = col2.text_input('Valor (ex: 25.50 ou 10+15)',
                                                     placeholder='Digite o valor ou expressão')
            transaction_description = col1.text_input('Descrição')

            submit_transaction_btn = st.form_submit_button('Adicionar Transação')

            if submit_transaction_btn:
                transaction_amount = parse_amount_expression(transaction_amount_str)
                if transaction_amount >= 0:
                    date_str = transaction_date.strftime('%d/%m/%Y')
                    add_transaction(date_str, transaction_amount, transaction_type, transaction_description)
                    st.success(f'Transação adicionada: {transaction_type} de R$ {transaction_amount:.2f} no dia {date_str}.')
                else:
                    st.error('Valor deve ser maior ou igual a zero.')
        st.header('Adicionar Despesa Fixa')
        day = st.selectbox('Dia do mês', list(range(1, 32)), index=0)
        description = st.text_input('Descrição')
        amount = st.number_input('Valor', min_value=0.0, step=10.0, format='%.2f')
        add_expense_submit_btn = st.button('Adicionar Despesa Fixa')

        if add_expense_submit_btn:
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
        transactions_df = transactions_dict_to_df(st.session_state.transactions_dict)
        
        if not transactions_df.empty:
            styled_transactions_df = transactions_df.style.format(
            {'Entrada': 'R${:.2f}', 'Saída': 'R${:.2f}', 'Diário': 'R${:.2f}', 'Saldo': 'R${:.2f}'},
            subset=['Entrada', 'Saída', 'Diário', 'Saldo']
        ).map(color_by_value, subset=['Saldo'])
            st.dataframe(styled_transactions_df, hide_index=True)
            st.subheader('Evolução do Saldo ao Longo do Tempo')
            
            plot_df = transactions_df.copy()
            plot_df['Dia'] = pd.to_datetime(plot_df['Dia'], format='%d/%m/%Y')
            
            plot_df = plot_df.sort_values('Dia')

            fig = px.line(plot_df, x='Dia', y='Saldo')

            for y_value, color in [(0, 'red'), (1000, 'orange'), (2000, 'green')]:
                fig.add_shape(
                    type='line',
                    x0=plot_df['Dia'].min(),
                    y0=y_value,
                    x1=plot_df['Dia'].max(),
                    y1=y_value,
                    line=dict(color=color, width=1, dash='dash'),
                )
                fig.add_annotation(
                    x=plot_df['Dia'].max(),
                    y=y_value,
                    text=f'R${y_value}',
                    showarrow=False,
                    xshift=10,
                    font=dict(color=color),
                )
            fig.update_layout(
                xaxis_title='Data',
                yaxis_title='Saldo (R$)',
                hovermode='x unified',
                height=500,
                margin=dict(l=20, r=20, t=40, b=20),
                plot_bgcolor='black',
                legend_title_text='Valores',
            )

            st.plotly_chart(fig, use_container_width=True)

            st.subheader('Entradas e Saídas do Dia')
            daily_transactions = transactions_df[transactions_df['Dia'] == date.today().strftime("%d/%m/%Y")]
            st.dataframe(daily_transactions[['Dia','Entrada', 'Saída', 'Diário', 'Saldo','Descrição']], hide_index=True)
        else:
            st.write('Planilha de gastos vazia. Crie uma nova planilha financeira na aba "Criar Planilha Financeira".')
    
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
        if not fixed_expenses_df.empty:
            with st.form(key='create_transactions_form'):
                starting_amount = st.number_input('Saldo Inicial', min_value=0.0, step=10.0, format='%.2f', value=1000.0)
                salary_day = st.selectbox('Dia do Salário',['Quinto dia útil', 'Último dia útil'] + list(range(1,32)), index=0)
                salary_amount = st.number_input('Valor do Salário', min_value=0.0, step=10.0, format='%.2f', value=1518.0)
                expense_per_day = st.number_input('Gasto Diária', min_value=0.0, step=10.0, format='%.2f', value=50.0)

                create_planner_submit_btn = st.form_submit_button('Criar Planilha')
            if create_planner_submit_btn:
                full_fixed_expenses_dict = {day: sum([amount for amount, _ in expenses]) for day, expenses in st.session_state.fixed_expenses_dict.items()}

                dates = [(date.today() + timedelta(days=i)) for i in range((date(date.today().year, 12, 31) - date.today()).days + 1)]
                current_balance = starting_amount

                for current_date in dates:
                    action_discription = []
                    income = 0
                    expense = 0

                    if salary_day == 'Quinto dia útil':
                        fifth_business_day = get_fifth_business_day(current_date.year, current_date.month)
                        if fifth_business_day and current_date == fifth_business_day:
                            income += salary_amount
                            action_discription.append('Salário')

                    elif salary_day == 'Último dia útil':
                        last_business_day = get_last_business_day(current_date.year, current_date.month)
                        if last_business_day and current_date == last_business_day:
                            income += salary_amount
                            action_discription.append('Salário')

                    # for numerical day of month
                    elif isinstance(salary_day, int) and current_date.day == salary_day:
                        income += salary_amount
                        action_discription.append('Salário')
                    
                    # check for fixed expenses on this day
                    day_of_month = current_date.day
                    if day_of_month in st.session_state.fixed_expenses_dict:
                        fixed_expense = full_fixed_expenses_dict[day_of_month]
                        expense += fixed_expense
                        for amount, description in st.session_state.fixed_expenses_dict[day_of_month]:
                            action_discription.append(f'{description}')
                    
                    # add daily expense
                    action_discription.append('Gasto Diário')

                    # calculate daily balance
                    daily_net = income - expense - expense_per_day
                    current_balance += daily_net
                    date_str = current_date.strftime('%d/%m/%Y')

                    # store in transactions dict
                    st.session_state.transactions_dict[date_str] = {
                        'Entrada': income,
                        'Saída': expense,
                        'Diário': expense_per_day,
                        'Saldo': current_balance,
                        'Descrição': ' + '.join(action_discription)
                    }
                save_data()
                transactions_df = transactions_dict_to_df(st.session_state.transactions_dict)
                st.success('Planilha financeira criada com sucesso!')
                st.rerun()

        else:
            st.write('Por favor, adicione despesas fixas antes de criar a planilha financeira.')
if __name__ == '__main__':
    main()