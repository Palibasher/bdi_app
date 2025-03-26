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
    df = pd.read_excel(uploaded_file, parse_dates=['ArchiveDate', 'StartDate', 'GroupDesc'])
    df['ArchiveDate'] = pd.to_datetime(df['ArchiveDate'], format='%Y-%m-%d', errors='coerce')  # Убедимся, что тип datetime

    min_date = df.loc[df['GroupDesc'] == 'BFA Cape', 'ArchiveDate'].min()
    max_date = df.loc[df['GroupDesc'] == 'BFA Cape', 'ArchiveDate'].max()

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
        selected_months = st.multiselect("Выберите месяц", available_months)

        available_dates = df[df['ArchiveDate'].dt.strftime('%Y-%m').isin(selected_months)]['ArchiveDate'].unique()
        selected_dates = st.multiselect("Выберите даты", sorted(available_dates),
                                        format_func=lambda x: x.strftime('%Y-%m-%d'))
        if not selected_dates:
            st.write("⚠️ Выберите хотя бы одну дату.")
            st.stop()


    # Переключатель для отображения фактических данных
    full_data = st.selectbox("Выберите вариант отображения фактических данных:",
                             ['До прогнозной даты', 'От прогнозной даты', 'Полностью'], index=0)

    # Выбор типа прогноза
    if mode == "Одна дата":
        forecast_types = st.multiselect("Выберите тип прогноза",
                                        ['Monthly Contract (MON)', 'Quarterly Contract (Q)',
                                         'Calendar Year Contract (CAL)'],
                                        default=['Monthly Contract (MON)'])
    else:
        forecast_types = st.multiselect("Выберите тип прогноза",
                                        ['Monthly Contract (MON)', 'Quarterly Contract (Q)',
                                         'Calendar Year Contract (CAL)'],
                                        default=['Monthly Contract (MON)'])
    # Функция для построения графика
    def plot_ffa_forecast(df, full_data, forecast_types, dates):
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
        combined_subsets = []

        if len(dates) == 1:
            for category in forecast_types:
                forecast_data = df[df['ArchiveDate'] == dates[0]]
                subset = forecast_data[forecast_data['Category'] == category]
                subset_for_print = subset[['Category', 'ArchiveDate', 'RouteAverage','Index_Label', 'StartDate']]
                combined_subsets.append(subset_for_print)
                plt.plot(subset['StartDate'], subset['RouteAverage'], 'o-', color=categories[category], label=category)
        else:

            colors = ['orange', 'purple', 'brown', 'pink', 'cyan', 'magenta', 'lime', 'navy', 'teal', 'gold']
            date_colors = {dates[i]: colors[i % len(colors)] for i in range(len(dates))}

            for date in dates:
                forecast_data = df[df['ArchiveDate'] == date]
                for i,category in enumerate(forecast_types):
                    subset = forecast_data[forecast_data['Category'] == category]
                    subset_for_print = subset[['Category','ArchiveDate', 'RouteAverage', 'Index_Label', 'StartDate']]
                    plt.plot(subset['StartDate'], subset['RouteAverage'], 'o-', color=date_colors[date],
                             label=f"{category} ({date.strftime('%Y-%m-%d')})", alpha=0.8)
                    combined_subsets.append(subset_for_print)

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

        # Объедините все DataFrame в один
        combined_df = pd.concat(combined_subsets, ignore_index=True)
        combined_df['ArchiveDate'] = combined_df['ArchiveDate'].dt.strftime('%Y-%m-%d')
        combined_df['Index_Label'] = combined_df['Index_Label'].str.split("_").str[1]

        # Теперь вы можете использовать combined_df по своему усмотрению
        unique_values = combined_df['Category'].unique()

        for value in unique_values:
            filtered_df = combined_df[combined_df['Category'] == value]
            st.subheader(value)


            df_cleaned = filtered_df.drop(columns=['Category']).sort_values(by='StartDate')

            index_label_startdate_pairs = list(zip(df_cleaned['Index_Label'], df_cleaned['StartDate']))
            sorted_index_labels = list(dict.fromkeys([pair[0] for pair in index_label_startdate_pairs]))

            # Делаем pivot, чтобы 'Index_Label' стал столбцами
            df_pivoted = df_cleaned.pivot(index='ArchiveDate', columns='Index_Label', values='RouteAverage')[sorted_index_labels]
            print(df_pivoted)

            # Выводим результат
            st.dataframe(df_pivoted, width=1000)






    # Построение графика после выбора параметров
    if st.button("Построить график") and selected_dates:
        plot_ffa_forecast(df, full_data, forecast_types, selected_dates)

