import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Загрузка файла
uploaded_file = st.file_uploader("Загрузите Excel-файл", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, parse_dates=['ArchiveDate', 'StartDate'])

    min_date = df['ArchiveDate'].min().date()
    max_date = df['ArchiveDate'].max().date()

    # Выбор даты через календарь (ограничиваем min и max)
    selected_date = st.date_input("Выберите дату", min_date, min_value=min_date, max_value=max_date)

    # Переключатель для отображения фактических данных
    full_data = st.selectbox("Выберите вариант отображения фактических данных:",
                         ['До прогнозной даты', 'Полностью'], index=0)

    # Выбор типа прогноза
    forecast_type = st.selectbox("Выберите тип прогноза",
                                 ['Все', 'Monthly Contract (MON)', 'Quarterly Contract (Q)', 'Calendar Year Contract (CAL)'])

    # Функция для построения графика
    def plot_ffa_forecast(df, full_data, forecast_type='Все', date=None):
        """Построение графика: факт до выбранной даты, прогноз с выбранной даты"""
        plt.figure(figsize=(12, 6))

        df_copy = df.copy()  # Делаем копию, чтобы не менять оригинальный DataFrame
        df_copy['ArchiveDate'] = df_copy['ArchiveDate'].dt.date  # Преобразуем в date

        # Фильтруем факт до выбранной даты
        if full_data == 'До прогнозной даты':
            actual_data = df_copy[(df_copy['Category'] == 'C5TC FACT') & (df_copy['ArchiveDate'] < date)]
        else:
            actual_data = df_copy[df_copy['Category'] == 'C5TC FACT']

        # Фильтруем прогноз на выбранную дату
        forecast_data = df_copy[df_copy['ArchiveDate'] == date]

        # Категории прогнозов
        categories = {
            'Monthly Contract (MON)': 'blue',
            'Quarterly Contract (Q)': 'green',
            'Calendar Year Contract (CAL)': 'red'
        }

        # Фактические данные
        plt.plot(actual_data['ArchiveDate'], actual_data['RouteAverage'], 'k-', label='Actual (C5TC FACT)')

        # Прогнозы
        for category, color in categories.items():
            if forecast_type == 'Все' or forecast_type == category:
                subset = forecast_data[forecast_data['Category'] == category]
                plt.plot(subset['StartDate'], subset['RouteAverage'], 'o-', color=color, label=category)

        # Настройки графика
        plt.xlabel("Дата")
        plt.ylabel("Route Average")
        plt.title("FFA Forecast vs Actual")
        plt.legend()
        plt.grid(True)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.xticks(rotation=45)

        st.pyplot(plt)  # Выводим график в Streamlit

    # Построение графика после выбора параметров
    if st.button("Построить график"):
        plot_ffa_forecast(df, full_data, forecast_type, selected_date)
