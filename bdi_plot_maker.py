import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta
from mpl_toolkits.axes_grid1.inset_locator import inset_axes


def plot_ffa_forecast(df,historical_data_types, forecast_types, dates, start_date, end_date, sma_90=False, sma_200=False, ewma_30=False,
                      ewma_90=False,rolling_std_90=False,rolling_std_200=False):
    """Построение графика для нескольких прогнозных дат"""
    fig, ax1 = plt.subplots(figsize=(16, 8))
    # Фильтруем факт
    start_datetime = pd.to_datetime(start_date)
    end_datetime = pd.to_datetime(end_date)

    # Фильтруем данные для 'C5TC FACT'
    actual_data = df[df['Category'].isin(historical_data_types)].copy()

    # Рассчитываем скользящее среднее для фактических данных
    actual_data = actual_data.copy()  # Создаем копию, чтобы избежать проблем


    if sma_90:
        actual_data.loc[:, 'SMA_90'] = actual_data['RouteAverage'].rolling(window=90, min_periods=1).mean()
        # Присваиваем рассчитанные значения обратно в основной DataFrame
        df.loc[df['Category'] == 'C5TC FACT', 'SMA_90'] = actual_data['SMA_90']
    if sma_200:
        actual_data.loc[:, 'SMA_200'] = actual_data['RouteAverage'].rolling(window=200, min_periods=1).mean()
        df.loc[df['Category'] == 'C5TC FACT', 'SMA_200'] = actual_data['SMA_200']
    if ewma_90:
        actual_data.loc[:, 'EWMA_90'] = actual_data['RouteAverage'].ewm(span=90, adjust=False).mean()
        df.loc[df['Category'] == 'C5TC FACT', 'EWMA_90'] = actual_data['EWMA_90']
    if ewma_30:
        actual_data.loc[:, 'EWMA_30'] = actual_data['RouteAverage'].ewm(span=30, adjust=False).mean()
        df.loc[df['Category'] == 'C5TC FACT', 'EWMA_30'] = actual_data['EWMA_30']
    if rolling_std_90:
        actual_data.loc[:, 'Rolling_Std_90'] = actual_data['RouteAverage'].rolling(window=90).std()
        df.loc[df['Category'] == 'C5TC FACT', 'Rolling_Std_90'] = actual_data['Rolling_Std_90']
    if rolling_std_200:
        actual_data.loc[:, 'Rolling_Std_200'] = actual_data['RouteAverage'].rolling(window=200).std()
        df.loc[df['Category'] == 'C5TC FACT', 'Rolling_Std_200'] = actual_data['Rolling_Std_200']


    actual_data_period = df[
        (df['Category'].isin(historical_data_types)) &
        (df['ArchiveDate'] >= start_datetime) &
        (df['ArchiveDate'] <= end_datetime)
        ]

    # Построение графиков для каждой категории
    for data_type in historical_data_types:
        category_data = actual_data_period[actual_data_period['Category'] == data_type]
        if data_type == "Brent Oil":  # Используем вторую ось
            ax2 = ax1.twinx()
            ax2.plot(category_data['ArchiveDate'], category_data['RouteAverage'], 'g-', label='Brent Oil')
            ax2.set_ylabel("Brent Oil Price", color='g')
            ax2.set_ylim(
                    actual_data_period[actual_data_period['Category'] == "Brent Oil"]['RouteAverage'].min() * 0.9,
                    actual_data_period[actual_data_period['Category'] == "Brent Oil"]['RouteAverage'].max() * 1.1)

            ax2.xaxis.set_visible(False)  # Прячем подписи у ax2
            ax1.plot([], [], 'g-', label='Brent Oil (Second Y-Axis)')
        elif data_type == "C5TC / P5TC":
            ax2 = ax1.twinx()
            c5tc_data = actual_data[actual_data['Category'] == 'C5TC FACT']
            p5tc_data = actual_data[actual_data['Category'] == 'P5TC FACT']
            # Объединяем эти два DataFrame по общей дате (предполагаем, что даты совпадают)
            merged_data = pd.merge(c5tc_data[['ArchiveDate', 'RouteAverage']],
                                   p5tc_data[['ArchiveDate', 'RouteAverage']], on='ArchiveDate',
                                   suffixes=('_C5TC', '_P5TC'))
            merged_data['RouteAverage_C5TC_P5TC_Ratio'] = merged_data['RouteAverage_C5TC'] / merged_data[
                'RouteAverage_P5TC']

            filtered_merged_data = merged_data[(merged_data['ArchiveDate'] >= start_datetime) & (merged_data['ArchiveDate'] <= end_datetime)]
            print(filtered_merged_data)
            # Строим график для соотношения C5TC / P5TC, теперь с ограничением по датам


            ax2.bar(filtered_merged_data['ArchiveDate'],
                    filtered_merged_data['RouteAverage_C5TC_P5TC_Ratio'] - 1,  # Отклонение от 1
                    color=['g' if x > 1 else 'r' for x in filtered_merged_data['RouteAverage_C5TC_P5TC_Ratio']],
                    alpha=0.5,)

            # Горизонтальная линия в 0 (где C5TC = P5TC)
            ax2.axhline(0, color='black', linestyle='--', linewidth=1)

            # ax2.plot(filtered_merged_data['ArchiveDate'], filtered_merged_data['RouteAverage_C5TC_P5TC_Ratio'], color='g')
            # ax2.set_ylim(5, -1)
            # ax2.set_ylabel("C5TC / P5TC Ratio", color='g')
            ax1.plot([], [], 'g-', label='C5TC / P5TC Ratio')

        else:  # Основная ось
            ax1.plot(category_data['ArchiveDate'], category_data['RouteAverage'], label=f'Actual ({data_type})')

    # ax1.legend(loc='upper left')

    if sma_90:
        ax1.plot(actual_data_period['ArchiveDate'], actual_data_period['SMA_90'], 'g--', alpha=0.6, label='90-day SMA')
    if sma_200:
        ax1.plot(actual_data_period['ArchiveDate'], actual_data_period['SMA_200'], 'r--', alpha=0.6,label='200-day SMA')
    if ewma_90:
        ax1.plot(actual_data_period['ArchiveDate'], actual_data_period['EWMA_90'], 'b-', alpha=0.6, label='90-day EWMA')
    if ewma_30:
        ax1.plot(actual_data_period['ArchiveDate'], actual_data_period['EWMA_30'], 'm-', alpha=0.6, label='30-day EWMA')
    if rolling_std_90:
        ax1.fill_between(actual_data_period['ArchiveDate'],
                         actual_data_period['SMA_90'] - actual_data_period['Rolling_Std_90'],
                         actual_data_period['SMA_90'] + actual_data_period['Rolling_Std_90'],
                         color='yellow', alpha=0.2, label='90-day Rolling Std Area')
    if rolling_std_200:
        ax1.fill_between(actual_data_period['ArchiveDate'],
                         actual_data_period['SMA_200'] - actual_data_period['Rolling_Std_200'],
                         actual_data_period['SMA_200'] + actual_data_period['Rolling_Std_200'],
                         color='black', alpha=0.2, label='200-day Rolling Std Area')
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
            subset_for_print = subset[['Category', 'ArchiveDate', 'RouteAverage', 'Index_Label', 'StartDate']]
            combined_subsets.append(subset_for_print)
            ax1.plot(subset['StartDate'], subset['RouteAverage'], 'o-', color=categories[category], label=category)
    else:
        colors = ['orange', 'purple', 'brown', 'pink', 'cyan', 'magenta', 'lime', 'navy', 'teal', 'gold']
        date_colors = {dates[i]: colors[i % len(colors)] for i in range(len(dates))}

        for date in dates:
            forecast_data = df[df['ArchiveDate'] == date]
            for i, category in enumerate(forecast_types):
                subset = forecast_data[forecast_data['Category'] == category]
                subset_for_print = subset[['Category', 'ArchiveDate', 'RouteAverage', 'Index_Label', 'StartDate']]
                ax1.plot(subset['StartDate'], subset['RouteAverage'], 'o-', color=date_colors[date],
                         label=f"{category} ({date.strftime('%Y-%m-%d')})", alpha=0.8)
                combined_subsets.append(subset_for_print)

    ax1.legend(loc='upper right')
    # Настройки графика
    plt.title("FFA Forecast vs Actual", fontsize=16, color='darkblue')
    plt.xlabel("Дата", fontsize=12, fontweight='light')
    plt.ylabel("Route Average", fontsize=12, fontweight='light')
    # plt.legend()
    plt.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.8)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.xticks(rotation=45)
    plt.tight_layout()
    fig.autofmt_xdate()
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
        df_pivoted = df_cleaned.pivot(index='ArchiveDate', columns='Index_Label', values='RouteAverage')[
            sorted_index_labels]

        # Выводим результат
        st.dataframe(df_pivoted, width=1000)
