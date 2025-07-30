import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import streamlit as st
from collections import Counter


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
            historical_data_types, start_datetime, end_datetime,
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
                ax1.plot(ewma_90_df_filtered['ArchiveDate'], ewma_90_df_filtered['EWMA_90'], 'm-', alpha=0.6,
                         label=f'90-day EWMA ({category})')

    def _plot_historical_data(self, ax1, actual_data_period, historical_data_types, low_thresholds,
                              high_thresholds):
        if low_thresholds is None:
            low_thresholds = []
        if high_thresholds is None:
            high_thresholds = []

        # Инициализируем DataFrame для возврата в самом начале
        final_signals_to_display = pd.DataFrame()

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

                if c5tc_data.empty or p5tc_data.empty:
                    continue

                merged_data = pd.merge(c5tc_data[['ArchiveDate', 'RouteAverage']],
                                       p5tc_data[['ArchiveDate', 'RouteAverage']], on='ArchiveDate',
                                       suffixes=('_C5TC', '_P5TC'))
                merged_data['Ratio'] = merged_data['RouteAverage_C5TC'] / merged_data['RouteAverage_P5TC']

                ax2.bar(merged_data['ArchiveDate'],
                        merged_data['Ratio'],
                        color=['g' if x > 1 else 'r' for x in merged_data['Ratio']],
                        alpha=0.3)

                merged_data['Ratio_prev'] = merged_data['Ratio'].shift(1)
                merged_data.dropna(inplace=True)

                all_signals = []
                for threshold in low_thresholds:
                    signals = merged_data[
                        (merged_data['Ratio'] < threshold) & (merged_data['Ratio_prev'] >= threshold)].copy()
                    if not signals.empty:
                        signals['Type'] = 'L'
                        signals['Threshold'] = threshold
                        all_signals.append(signals)

                for threshold in high_thresholds:
                    signals = merged_data[
                        (merged_data['Ratio'] > threshold) & (merged_data['Ratio_prev'] <= threshold)].copy()
                    if not signals.empty:
                        signals['Type'] = 'S'
                        signals['Threshold'] = threshold
                        all_signals.append(signals)

                if all_signals:
                    final_signals_df = pd.concat(all_signals, ignore_index=True)
                    final_signals_df['YearMonth'] = final_signals_df['ArchiveDate'].dt.to_period('M')
                    final_signals_df.sort_values('ArchiveDate', inplace=True)

                    filtered_signals = final_signals_df.drop_duplicates(subset=['YearMonth', 'Type'], keep='first')

                    # Присваиваем результат переменной, которую вернем в конце
                    final_signals_to_display = filtered_signals
                else:
                    filtered_signals = pd.DataFrame()

                if not filtered_signals.empty:
                    low_signals_to_plot = filtered_signals[filtered_signals['Type'] == 'L']
                    if not low_signals_to_plot.empty:
                        ax2.scatter(low_signals_to_plot['ArchiveDate'], low_signals_to_plot['Ratio'],
                                    color='blue', marker='^', s=120, zorder=5,
                                    label=f'Low Signal (пробой вниз)')
                        for i, point in low_signals_to_plot.iterrows():
                            ax2.text(point['ArchiveDate'], point['Ratio'] + 0.05, f"L\n({point['Threshold']})",
                                     ha='center', va='bottom', color='blue', fontsize=10, fontweight='bold')

                    high_signals_to_plot = filtered_signals[filtered_signals['Type'] == 'S']
                    if not high_signals_to_plot.empty:
                        ax2.scatter(high_signals_to_plot['ArchiveDate'], high_signals_to_plot['Ratio'],
                                    color='purple', marker='v', s=120, zorder=5,
                                    label=f'High Signal (пробой вверх)')
                        for i, point in high_signals_to_plot.iterrows():
                            ax2.text(point['ArchiveDate'], point['Ratio'] - 0.05, f"S\n({point['Threshold']})",
                                     ha='center', va='top', color='purple', fontsize=10, fontweight='bold')

                ax1.plot([], [], 'g-', label='C5TC / P5TC Ratio')
                ax2.set_ylabel("C5TC / P5TC Ratio", color='g')
                if not merged_data.empty:
                    ax2.set_ylim(min(merged_data['Ratio']) * 0.85, max(merged_data['Ratio']) * 1.15)
            else:
                ax1.plot(category_data['ArchiveDate'], category_data['RouteAverage'], label=f'Actual ({data_type})')

        # Гарантированный возврат DataFrame в конце функции
        return final_signals_to_display

    def _plot_forecasts(self, ax1, forecast_types, dates, average_forcast_mode, average_forcast_mode_group):
        self.combined_subsets.clear()

        category_colors = {
            'Monthly Contract (MON)': 'blue',
            'Quarterly Contract (Q)': 'green',
            'Calendar Year Contract (CAL)': 'red'
        }

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
                    subset[['Category', 'ArchiveDate', 'RouteAverage', 'Index_Label', 'StartDate']].copy()
                )

                if not average_forcast_mode:
                    ax1.plot(subset['StartDate'], subset['RouteAverage'], 'o-',
                             color=category_colors[category],
                             label=f"{category} ({date.strftime('%Y-%m-%d')})",
                             alpha=0.8)

        # --- Средний режим ---
        if average_forcast_mode:
            combined_df = pd.concat(self.combined_subsets, ignore_index=True)

            # Добавим колонку MonthYear
            combined_df['MonthYear'] = combined_df['StartDate'].dt.to_period('M')
            combined_df['QuarterStart'] = combined_df['StartDate'].dt.to_period('Q').dt.start_time

            for category in forecast_types:
                cat_df = combined_df[combined_df['Category'] == category]
                print(category)
                if cat_df.empty:
                    continue
                if average_forcast_mode_group == "Месяца до кварталов" and category == 'Monthly Contract (MON)':
                    print("start")
                    # Создаем столбец с началом квартала
                    cat_df['QuarterStart'] = cat_df['StartDate'].apply(
                        lambda x: pd.Timestamp(year=x.year, month=((x.month - 1) // 3) * 3 + 1, day=1))

                    # Группируем по ArchiveDate
                    grouped = cat_df.groupby('ArchiveDate')

                    # Словарь для хранения данных по кварталам
                    seen_quarter_sets = {}

                    for archive_date, group in grouped:
                        # Определяем квартал для каждой строки
                        quarter_set = tuple(sorted(group['QuarterStart'].astype(str).unique()))

                        # Принт для отладки
                        print(f"ArchiveDate: {archive_date} -> quarter_set: {quarter_set}")

                        # Убираем из quarter_set лишние кварталы, если их несколько
                        if len(quarter_set) > 1:
                            # Берем только первый квартал (по логике, это и есть нужный квартал)
                            quarter_set = (quarter_set[0],)
                            print(f"Warning: More than one quarter for {archive_date}, using the first one.")

                        if quarter_set not in seen_quarter_sets:
                            seen_quarter_sets[quarter_set] = []
                        seen_quarter_sets[quarter_set].append(group)

                    # Проверим, сколько данных собралось в каждом квартале
                    print(f"Total quarters: {len(seen_quarter_sets)}")

                    for quarter_set, group_list in seen_quarter_sets.items():
                        # Объединяем все данные по кварталу
                        merged = pd.concat(group_list)
                        print(f"Quarter: {quarter_set[0]} -> Merged data count: {len(merged)}")

                        # Сортируем по дате
                        merged['StartDate'] = merged['StartDate'].astype('datetime64[ns]')

                        # Группируем по дате и усредняем значения
                        avg_df = merged.groupby('StartDate', as_index=False)['RouteAverage'].mean()
                        avg_df = avg_df.sort_values('StartDate')

                        # Определяем метку для квартала
                        quarter_label = quarter_set[0] if quarter_set else "?"
                        quarter_dt = pd.to_datetime(quarter_label)
                        quarter_num = (quarter_dt.month - 1) // 3 + 1
                        label = f"{category} - {quarter_dt.year}-Q{quarter_num}"

                        # Рисуем одну линию для всего квартала
                        ax1.plot(avg_df['StartDate'], avg_df['RouteAverage'], '--',
                                 color=category_colors[category],
                                 label=label,
                                 linewidth=2)

                        print(f"Quarter label: {label}, Number of points in avg_df: {len(avg_df)}")

                elif average_forcast_mode_group == "Месяцам" or category != 'Monthly Contract (MON)':
                    # Группируем по ArchiveDate
                    grouped = cat_df.groupby('ArchiveDate')

                    seen_month_sets = {}

                    for archive_date, group in grouped:
                        month_set = tuple(sorted(group['MonthYear'].astype(str)))
                        if month_set not in seen_month_sets:
                            seen_month_sets[month_set] = []
                        seen_month_sets[month_set].append(group)

                    for month_set, group_list in seen_month_sets.items():
                        if len(group_list) > 1:
                            merged = pd.concat(group_list)
                            # Убедимся, что отсортировано по дате
                            month_label = month_set[0] if month_set else "?"
                            merged['StartDate'] = merged['StartDate'].astype('datetime64[ns]')
                            avg_df = merged.groupby('StartDate', as_index=False)['RouteAverage'].mean()
                            avg_df = avg_df.sort_values('StartDate')
                            ax1.plot(avg_df['StartDate'], avg_df['RouteAverage'], '--',
                                     color=category_colors[category],
                                     label=f"{category} - {month_label}",
                                     linewidth=2)
                else:
                    # Обычное усреднение по StartDate
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
            df_pivoted = df_cleaned.pivot(index='ArchiveDate', columns='Index_Label', values='RouteAverage')[
                sorted_index_labels]
            # Выводим результат
            st.dataframe(df_pivoted, width=1000)

    def plot_forecast(self, historical_data_types, forecast_types, dates, start_date, end_date, average_forcast_mode,
                      average_forcast_mode_group, low_thresholds, high_thresholds):
        fig, ax1 = plt.subplots(figsize=(16, 8))
        start_datetime = pd.to_datetime(start_date)
        end_datetime = pd.to_datetime(end_date)
        actual_data_period = self.df[
            (self.df['Category'].isin(historical_data_types)) &
            (self.df['ArchiveDate'] >= start_datetime) &
            (self.df['ArchiveDate'] <= end_datetime)
            ]
        fig.autofmt_xdate()

        # --- ИСПРАВЛЕНИЕ: ОДИН вызов, результат которого сохраняется ---
        triggered_signals_df = self._plot_historical_data(ax1, actual_data_period, historical_data_types,
                                                          low_thresholds, high_thresholds)

        # Остальные вызовы
        self._plot_forecasts(ax1, forecast_types, dates, average_forcast_mode, average_forcast_mode_group)
        self._compute_indicators(ax1, historical_data_types, start_datetime, end_datetime)
        self._finalize_plot(ax1)
        st.pyplot(plt, clear_figure=True)
        self._prepare_combined_dataframe()

        # --- ИСПРАВЛЕНИЕ: Возвращаем полученный DataFrame ---
        return triggered_signals_df
