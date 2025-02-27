import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta

# Загрузка файла
uploaded_file = st.file_uploader("Загрузите Excel-файл", type=["xlsx"])

def empty_date_checker(df, selected_date):
    """Проверяет, есть ли данные для выбранной даты."""
    selected_date = pd.to_datetime(selected_date)  # Приводим к единому типу
    return not df[(df['GroupDesc'] == 'BFA Cape') & (df['ArchiveDate'] == selected_date)].empty

if uploaded_file:
    df = pd.read_excel(uploaded_file, parse_dates=['ArchiveDate', 'StartDate'])
    df['ArchiveDate'] = pd.to_datetime(df['ArchiveDate'])  # Убедимся, что тип datetime

    min_date = df['ArchiveDate'].min()
    max_date = df['ArchiveDate'].max()

    # Выбор режима
    mode = st.radio("Выберите режим", ["Одна дата", "Несколько дат"])

    if mode == "Одна дата":
        selected_date = st.date_input("Выберите дату", min_date, min_value=min_date, max_value=max_date)
        selected_date = pd.to_datetime(selected_date)  # Приводим к единому типу

        if empty_date_checker(df, selected_date):
            st.write("✅ Данные найдены!")
        else:
            st.write("⚠️ Данных за эту дату нет.")
            data_found = False
            for days_delta in range(15):
                selected_date -= timedelta(days=1)  # Уменьшаем дату на 1 день
                if empty_date_checker(df, selected_date):
                    st.write(f"Выбранная ближайшая дата: {selected_date.strftime('%Y-%m-%d')}.")
                    data_found = True
                    break
            if not data_found:
                st.write("Данные не найдены за последние 15 дней.")

        selected_dates = [selected_date]  # Оборачиваем в список для унификации кода

    elif mode == "Несколько дат":
        # Выбор месяца
        available_months = sorted(df['ArchiveDate'].dt.strftime('%Y-%m').unique(), reverse=True)
        selected_month = st.selectbox("Выберите месяц", available_months)

        # Фильтруем даты по выбранному месяцу
        available_dates = df[df['ArchiveDate'].dt.strftime('%Y-%m') == selected_month]['ArchiveDate'].unique()
        selected_dates = st.multiselect("Выберите даты", sorted(available_dates), format_func=lambda x: x.strftime('%Y-%m-%d'))

        if not selected_dates:
            st.write("⚠️ Выберите хотя бы одну дату.")
            st.stop()

        # Проверяем, что выбранные даты содержат данные
        valid_dates = []
        for date in selected_dates:
            if empty_date_checker(df, date):
                valid_dates.append(date)
            else:
                st.warning(f"Данных за дату {date.strftime('%Y-%m-%d')} нет.")
        selected_dates = valid_dates

        if not selected_dates:
            st.write("⚠️ Нет данных для выбранных дат.")
            st.stop()

    # Переключатель для отображения фактических данных
    full_data = st.selectbox("Выберите вариант отображения фактических данных:",
                             ['До прогнозной даты', 'От прогнозной даты', 'Полностью'], index=0)

    # Выбор типа прогноза
    if mode == "Одна дата":
        forecast_type = st.selectbox("Выберите тип прогноза",
                                 ['Все', 'Monthly Contract (MON)', 'Quarterly Contract (Q)', 'Calendar Year Contract (CAL)'])
    else:
        forecast_type = st.selectbox("Выберите тип прогноза",
                                     ['Monthly Contract (MON)', 'Quarterly Contract (Q)',
                                      'Calendar Year Contract (CAL)'])
    # Функция для построения графика
    def plot_ffa_forecast(df, full_data, forecast_type, dates):
        """Построение графика для нескольких прогнозных дат"""
        plt.figure(figsize=(12, 6))

        # Фильтруем факт
        if full_data == 'До прогнозной даты':
            actual_data = df[(df['Category'] == 'C5TC FACT') & (df['ArchiveDate'] < min(dates))]
        elif full_data == 'От прогнозной даты':
            actual_data = df[(df['Category'] == 'C5TC FACT') & (df['ArchiveDate'] > min(dates))]
        else:
            actual_data = df[df['Category'] == 'C5TC FACT']

        # Фактические данные
        plt.plot(actual_data['ArchiveDate'], actual_data['RouteAverage'], 'k-', label='Actual (C5TC FACT)')

        # Категории прогнозов
        categories = {
            'Monthly Contract (MON)': 'blue',
            'Quarterly Contract (Q)': 'green',
            'Calendar Year Contract (CAL)': 'red'
        }

        if len(dates) == 1:
            for category, color in categories.items():
                if forecast_type == 'Все' or forecast_type == category:
                    forecast_data = df[df['ArchiveDate'] == dates[0]]
                    subset = forecast_data[forecast_data['Category'] == category]
                    plt.plot(subset['StartDate'], subset['RouteAverage'], 'o-', color=color, label=category)
        else:

            colors = ['orange', 'purple', 'brown', 'pink', 'cyan', 'magenta', 'lime', 'navy', 'teal', 'gold']
            date_colors = {dates[i]: colors[i % len(colors)] for i in range(len(dates))}

            for date in dates:
                forecast_data = df[df['ArchiveDate'] == date]

                for category, color in categories.items():
                    if forecast_type == 'Все' or forecast_type == category:
                        subset = forecast_data[forecast_data['Category'] == category]
                        plt.plot(subset['StartDate'], subset['RouteAverage'], 'o-',
                                 color=date_colors[date], label=f"{category} ({date.strftime('%Y-%m-%d')})", alpha=0.8)

        # Настройки графика
        plt.xlabel("Дата")
        plt.ylabel("Route Average")
        plt.title("FFA Forecast vs Actual")
        plt.legend()
        plt.grid(True)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.xticks(rotation=45)
        plt.tight_layout()

        st.pyplot(plt, clear_figure=True)  # Выводим график в Streamlit

    # Построение графика после выбора параметров
    if st.button("Построить график") and selected_dates:
        plot_ffa_forecast(df, full_data, forecast_type, selected_dates)

