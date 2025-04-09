import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import streamlit as st


class FFAForecastPlotter:
    def __init__(self, df, sma_90, sma_200, ewma_30, ewma_90, rolling_std_90, rolling_std_200):
        self.df = df.copy()
        self.combined_subsets = []
        self.sma_90 = sma_90
        self.sma_200 = sma_200
        self.ewma_30 = ewma_30
        self.ewma_90 = ewma_90
        self.rolling_std_90 = rolling_std_90
        self.rolling_std_200 = rolling_std_200

    def _compute_indicators(
            self,
            ax1,
            historical_data_types,start_datetime,end_datetime,
            data_flag=False):
        if self.sma_90: self.df['SMA_90'] = np.nan
        if self.sma_200: self.df['SMA_200'] = np.nan
        if self.ewma_30: self.df['EWMA_30'] = np.nan
        if self.ewma_90: self.df['EWMA_90'] = np.nan
        if self.rolling_std_90: self.df['Rolling_Std_90'] = np.nan
        if self.rolling_std_200: self.df['Rolling_Std_200'] = np.nan
        # Если в будущем захочу рисовать не только P5TC
        if not data_flag:
            historical_data_types = ['C5TC FACT']

        for category in historical_data_types:
            subset = self.df[self.df['Category'] == category].copy()
            subset = subset.sort_values('ArchiveDate')

            # 90-day SMA
            if self.sma_90:
                sma_90_values = subset['RouteAverage'].rolling(window=90, min_periods=1).mean()
                self.df.loc[self.df['Category'] == category, 'SMA_90'] = sma_90_values.values
                print(f"Plotting SMA_90 for category {category}")

                # Создаём датафрейм для фильтрации
                sma_90_df = pd.DataFrame({
                    'ArchiveDate': subset['ArchiveDate'],
                    'SMA_90': sma_90_values
                })

                # Если считаем стандартное отклонение
                if self.rolling_std_90:
                    rolling_std_90_values = subset['RouteAverage'].rolling(window=90).std()
                    self.df.loc[self.df['Category'] == category, 'Rolling_Std_90'] = rolling_std_90_values.values

                    sma_90_df['Rolling_Std_90'] = rolling_std_90_values

                # Фильтруем по диапазону дат
                sma_90_df_filtered = sma_90_df[
                    (sma_90_df['ArchiveDate'] >= start_datetime) &
                    (sma_90_df['ArchiveDate'] <= end_datetime)
                    ]

                # Линия SMA
                ax1.plot(sma_90_df_filtered['ArchiveDate'], sma_90_df_filtered['SMA_90'],
                         'g--', alpha=0.6, label=f'90-day SMA ({category})')

                # Площадь стандартного отклонения
                if self.rolling_std_90:
                    ax1.fill_between(sma_90_df_filtered['ArchiveDate'],
                                     sma_90_df_filtered['SMA_90'] - sma_90_df_filtered['Rolling_Std_90'],
                                     sma_90_df_filtered['SMA_90'] + sma_90_df_filtered['Rolling_Std_90'],
                                     color='yellow', alpha=0.2, label='90-day Rolling Std Area')

            # 200-day SMA
            if self.sma_200:
                sma_200_values = subset['RouteAverage'].rolling(window=200, min_periods=1).mean()
                self.df.loc[self.df['Category'] == category, 'SMA_200'] = sma_200_values.values
                print(f"Plotting SMA_200 for category {category}")

                # Собираем датафрейм для фильтрации
                sma_200_df = pd.DataFrame({
                    'ArchiveDate': subset['ArchiveDate'],
                    'SMA_200': sma_200_values
                })

                # Если считаем rolling std
                if self.rolling_std_200:
                    rolling_std_200_values = subset['RouteAverage'].rolling(window=200).std()
                    self.df.loc[self.df['Category'] == category, 'Rolling_Std_200'] = rolling_std_200_values.values

                    sma_200_df['Rolling_Std_200'] = rolling_std_200_values

                # Фильтрация по дате
                sma_200_df_filtered = sma_200_df[
                    (sma_200_df['ArchiveDate'] >= start_datetime) &
                    (sma_200_df['ArchiveDate'] <= end_datetime)
                    ]

                # Линия SMA
                ax1.plot(sma_200_df_filtered['ArchiveDate'], sma_200_df_filtered['SMA_200'],
                         'b--', alpha=0.6, label=f'200-day SMA ({category})')

                # Площадь стандартного отклонения
                if self.rolling_std_200:
                    ax1.fill_between(sma_200_df_filtered['ArchiveDate'],
                                     sma_200_df_filtered['SMA_200'] - sma_200_df_filtered['Rolling_Std_200'],
                                     sma_200_df_filtered['SMA_200'] + sma_200_df_filtered['Rolling_Std_200'],
                                     color='black', alpha=0.2, label='200-day Rolling Std Area')

            # 30-day EWMA
            if self.ewma_30:
                ewma_30_values = subset['RouteAverage'].ewm(span=30, adjust=False).mean()
                self.df.loc[self.df['Category'] == category, 'EWMA_30'] = ewma_30_values.values
                # Создаем DataFrame с датами и значениями EWMA
                ewma_30_df = pd.DataFrame({
                    'ArchiveDate': subset['ArchiveDate'],
                    'EWMA_30': ewma_30_values
                })
                # Фильтруем по датам
                ewma_30_df_filtered = ewma_30_df[
                    (ewma_30_df['ArchiveDate'] >= start_datetime) &
                    (ewma_30_df['ArchiveDate'] <= end_datetime)
                    ]
                print(f"Plotting EWMA_30 for category {category}")  # Добавил вывод
                ax1.plot(ewma_30_df_filtered['ArchiveDate'], ewma_30_df_filtered['EWMA_30'], 'r-', alpha=0.6,
                         label=f'30-day EWMA ({category})')

            # 90-day EWMA
            if self.ewma_90:
                ewma_90_values = subset['RouteAverage'].ewm(span=90, adjust=False).mean()
                self.df.loc[self.df['Category'] == category, 'EWMA_90'] = ewma_90_values.values
                ewma_90_df = pd.DataFrame({
                    'ArchiveDate': subset['ArchiveDate'],
                    'EWMA_90': ewma_90_values
                })
                # Фильтруем по датам
                ewma_90_df_filtered = ewma_90_df[
                    (ewma_90_df['ArchiveDate'] >= start_datetime) &
                    (ewma_90_df['ArchiveDate'] <= end_datetime)
                    ]
                print(f"Plotting EWMA_90 for category {category}")  # Добавил вывод
                ax1.plot(ewma_90_df_filtered['ArchiveDate'], ewma_90_df_filtered['EWMA_90'], 'm-', alpha=0.6, label=f'90-day EWMA ({category})')

    def _plot_historical_data(self, ax1, actual_data_period, historical_data_types):
        for data_type in historical_data_types:
            category_data = actual_data_period[actual_data_period['Category'] == data_type]
            if data_type == "Brent Oil":
                ax2 = ax1.twinx()
                ax2.plot(category_data['ArchiveDate'], category_data['RouteAverage'], 'g-', label='Brent Oil')
                ax2.set_ylabel("Brent Oil Price", color='g')
                ax2.set_ylim(
                    actual_data_period[actual_data_period['Category'] == "Brent Oil"]['RouteAverage'].min() * 0.9,
                    actual_data_period[actual_data_period['Category'] == "Brent Oil"]['RouteAverage'].max() * 1.1)
                ax1.plot([], [], 'g-', label='Brent Oil (Second Y-Axis)')
            elif data_type == "C5TC / P5TC":
                ax2 = ax1.twinx()
                c5tc_data = actual_data_period[actual_data_period['Category'] == 'C5TC FACT']
                p5tc_data = actual_data_period[actual_data_period['Category'] == 'P5TC FACT']
                # Объединяем эти два DataFrame по общей дате (предполагаем, что даты совпадают)
                merged_data = pd.merge(c5tc_data[['ArchiveDate', 'RouteAverage']],
                                       p5tc_data[['ArchiveDate', 'RouteAverage']], on='ArchiveDate',
                                       suffixes=('_C5TC', '_P5TC'))
                merged_data['RouteAverage_C5TC_P5TC_Ratio'] = merged_data['RouteAverage_C5TC'] / merged_data[
                    'RouteAverage_P5TC']

                # Задаем минимальные и максимальные значения для отображения
                start_datetime = actual_data_period['ArchiveDate'].min()
                end_datetime = actual_data_period['ArchiveDate'].max()
                filtered_merged_data = merged_data[
                    (merged_data['ArchiveDate'] >= start_datetime) & (merged_data['ArchiveDate'] <= end_datetime)]

                # Построение графика соотношения C5TC/P5TC без вычитания 1
                ax2.bar(filtered_merged_data['ArchiveDate'],
                        filtered_merged_data['RouteAverage_C5TC_P5TC_Ratio'],
                        color=['g' if x > 1 else 'r' for x in filtered_merged_data['RouteAverage_C5TC_P5TC_Ratio']],
                        alpha=0.4)  # Увеличиваем прозрачность



                # Легенда для графика
                ax1.plot([], [], 'g-', label='C5TC / P5TC Ratio')

                # Настройки осей
                ax2.set_ylabel("C5TC / P5TC Ratio", color='g')
                ax2.set_ylim(min(filtered_merged_data['RouteAverage_C5TC_P5TC_Ratio']) * 0.9,
                             max(filtered_merged_data['RouteAverage_C5TC_P5TC_Ratio']) * 1.1)
            else:
                ax1.plot(category_data['ArchiveDate'], category_data['RouteAverage'], label=f'Actual ({data_type})')

    def _plot_forecasts(self, ax1, forecast_types, dates, average_forcast_mode):
        self.combined_subsets.clear()

        category_colors = {
            'Monthly Contract (MON)': 'blue',
            'Quarterly Contract (Q)': 'green',
            'Calendar Year Contract (CAL)': 'red'
        }

        # Назначим дополнительные цвета, если категорий больше
        extra_colors = ['orange', 'purple', 'brown', 'pink', 'cyan', 'magenta']
        for i, cat in enumerate(forecast_types):
            if cat not in category_colors:
                category_colors[cat] = extra_colors[i % len(extra_colors)]
        if len(dates) > 9 and not average_forcast_mode:
            self.show_legend = False
        for date in dates:
            forecast_data = self.df[self.df['ArchiveDate'] == date]

            for category in forecast_types:
                subset = forecast_data[forecast_data['Category'] == category]
                self.combined_subsets.append(
                    subset[['Category', 'ArchiveDate', 'RouteAverage', 'Index_Label', 'StartDate']])

                # Отрисовываем, только если не режим среднего
                if not average_forcast_mode:
                    ax1.plot(subset['StartDate'], subset['RouteAverage'], 'o-',
                             color=category_colors[category],
                             label=f"{category} ({date.strftime('%Y-%m-%d')})",
                             alpha=0.8)

        # Добавляем среднюю линию, если режим average
        if average_forcast_mode:
            combined_df = pd.concat(self.combined_subsets, ignore_index=True)
            for category in forecast_types:
                cat_df = combined_df[combined_df['Category'] == category]
                if cat_df.empty:
                    continue
                avg_df = cat_df.groupby('StartDate', as_index=False)['RouteAverage'].mean()
                avg_df = avg_df.sort_values('StartDate')
                ax1.plot(avg_df['StartDate'], avg_df['RouteAverage'], '--',
                         color=category_colors[category],
                         label=f"{category} (Average)",
                         linewidth=2)
    def _finalize_plot(self, ax1):
        if getattr(self, 'show_legend', True):
            ax1.legend(loc='upper right')
        ax1.set_title("FFA Forecast vs Actual", fontsize=16, color='darkblue')
        ax1.set_xlabel("Дата", fontsize=12, fontweight='light')
        ax1.set_ylabel("Route Average", fontsize=12, fontweight='light')
        ax1.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.8)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.xticks(rotation=45)


    def _prepare_combined_dataframe(self):
        combined_df = pd.concat(self.combined_subsets, ignore_index=True)
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
            # Выводим результат
            st.dataframe(df_pivoted, width=1000)


    def plot_forecast(self, historical_data_types, forecast_types, dates, start_date, end_date,average_forcast_mode):
        fig, ax1 = plt.subplots(figsize=(16, 8))
        start_datetime = pd.to_datetime(start_date)
        end_datetime = pd.to_datetime(end_date)
        actual_data_period = self.df[
            (self.df['Category'].isin(historical_data_types)) &
            (self.df['ArchiveDate'] >= start_datetime) &
            (self.df['ArchiveDate'] <= end_datetime)
            ]
        fig.autofmt_xdate()

        self._plot_historical_data(ax1, actual_data_period, historical_data_types)
        self._plot_forecasts(ax1, forecast_types, dates, average_forcast_mode)
        self._compute_indicators(ax1, historical_data_types,start_datetime,end_datetime)
        self._finalize_plot(ax1)
        st.pyplot(plt, clear_figure=True)
        self._prepare_combined_dataframe()



        # # Объедините все DataFrame в один
        # self._prepare_combined_dataframe()
