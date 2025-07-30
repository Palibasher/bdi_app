import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta
from bdi_plot_maker import FFAForecastPlotter


@st.cache_data
def load_and_process_data(uploaded_file):
    df = pd.read_excel(uploaded_file, parse_dates=['ArchiveDate', 'StartDate'])
    df['ArchiveDate'] = pd.to_datetime(df['ArchiveDate'], format='%Y-%m-%d', errors='coerce')
    return df


st.markdown("""
    <style>
        .block-container {
            max-width: 1300px;
        }
        .custom-column {
            width: 80%;
        }
    </style>
""", unsafe_allow_html=True)


def empty_date_checker(df, selected_date):
    selected_date = pd.to_datetime(selected_date)
    return not df[(df['GroupDesc'] == 'BFA Cape') & (df['ArchiveDate'] == selected_date)].empty


# --- Функция для обработки введенных порогов ---
def parse_thresholds(text_input, default_values):
    """Преобразует строку с порогами в список чисел."""
    if not text_input.strip():
        return []  # Возвращаем значения по умолчанию, если поле пустое
    try:
        # Разделяем по запятой, убираем пробелы и преобразуем в float
        return [float(x.strip()) for x in text_input.split(',')]
    except ValueError:
        st.error(
            f"Ошибка в формате порогов: '{text_input}'. Используйте числа, разделенные запятой (например: 0.75, 0.5).")
        return None  # Возвращаем None в случае ошибки


# Загрузка файла
uploaded_file = st.file_uploader("Загрузите Excel-файл", type=["xlsx"])

col1, col2, col3 = st.columns([1.7, 1.2, 0.8])  # Немного изменил пропорции для новых полей

if uploaded_file:
    with col1:
        df = load_and_process_data(uploaded_file)
        df['ArchiveDate'] = pd.to_datetime(df['ArchiveDate'], format='%Y-%m-%d', errors='coerce')

        min_date = df.loc[df['GroupDesc'] == 'BFA Cape', 'ArchiveDate'].min()
        max_date = df.loc[df['GroupDesc'] == 'BFA Cape', 'ArchiveDate'].max()

        mode = st.radio("**Выберите режим**", ["Одна дата", "Несколько дат", "Месяц целиком"])

        if mode == "Одна дата":
            selected_date = st.date_input("**Выберите дату**", min_value=min_date, max_value=max_date)
            selected_date = pd.to_datetime(selected_date)
            if not empty_date_checker(df, selected_date):
                st.write("⚠️ Данных за эту дату нет. Ищем ближайшую...")
                data_found = False
                for _ in range(15):
                    selected_date -= timedelta(days=1)
                    if empty_date_checker(df, selected_date):
                        st.write(f"✅ Выбрана ближайшая дата: {selected_date.strftime('%Y-%m-%d')}.")
                        data_found = True
                        break
                if not data_found:
                    st.write("⛔ Данные не найдены за последние 15 дней.")
            selected_dates = [selected_date]

        elif mode == "Несколько дат":
            available_months = sorted(df['ArchiveDate'].dt.strftime('%Y-%m').unique(), reverse=True)
            selected_months = st.multiselect("Выберите месяц", available_months)
            available_dates = \
            df[(df['GroupDesc'] == 'BFA Cape') & (df['ArchiveDate'].dt.strftime('%Y-%m').isin(selected_months))][
                'ArchiveDate'].unique()
            selected_dates = st.multiselect("Выберите даты", sorted(available_dates),
                                            format_func=lambda x: x.strftime('%Y-%m-%d'))
            if not selected_dates:
                st.warning("⚠️ Выберите хотя бы одну дату.")
                st.stop()

        elif mode == "Месяц целиком":
            bfa_df = df[df['GroupDesc'] == 'BFA Cape']
            available_months = sorted(bfa_df['ArchiveDate'].dt.strftime('%Y-%m').unique(), reverse=True)
            default_month = available_months[1] if len(available_months) > 1 else (
                available_months[0] if available_months else None)
            selected_months = st.multiselect("Выберите месяц", available_months,
                                             default=[default_month] if default_month else [])
            if selected_months:
                month_dates = \
                df[(df['GroupDesc'] == 'BFA Cape') & (df['ArchiveDate'].dt.strftime('%Y-%m').isin(selected_months))][
                    'ArchiveDate'].unique()
                selected_dates = sorted(list(month_dates))
            else:
                selected_dates = []

        forecast_types = st.multiselect("**Выберите тип прогноза**",
                                        ['Monthly Contract (MON)', 'Quarterly Contract (Q)',
                                         'Calendar Year Contract (CAL)'],
                                        default=['Monthly Contract (MON)'])
        if not forecast_types:
            st.warning("⚠️ Пожалуйста, выберите хотя бы один тип прогноза.")
            st.stop()

    with col2:
        st.markdown("**Настройки индикаторов**")
        sma_90 = st.checkbox("90-дневная SMA", value=False)
        rolling_std_90 = st.checkbox("Std Dev (90 дней)", value=sma_90, disabled=not sma_90)
        sma_200 = st.checkbox("200-дневная SMA", value=False)
        rolling_std_200 = st.checkbox("Std Dev (200 дней)", value=sma_200, disabled=not sma_200)
        ewma_90 = st.checkbox("90-дневная EWMA", value=False)
        ewma_30 = st.checkbox("30-дневная EWMA", value=False)

        # --- НОВЫЙ БЛОК ДЛЯ ПОРОГОВ ---
        st.markdown("**Настройки сигналов для Ratio**")
        low_thresholds_input = st.text_input(
            "Нижние пороги (сигнал 'L')",
            "0.75, 0.5",
            help="Введите значения через запятую"
        )
        high_thresholds_input = st.text_input(
            "Верхние пороги (сигнал 'S')",
            "1.75, 2.0",
            help="Введите значения через запятую"
        )
        # -------------------------------

    with col3:
        st.markdown("**Доп. настройки**")
        average_forcast_mode = st.checkbox("Усреднить прогнозы", value=False)
        average_forcast_mode_group = st.selectbox(
            "Группировать по:",
            options=[False, "Месяцам", "Месяца до кварталов"],
            index=0,
            disabled=not average_forcast_mode
        )

    start_date, end_date = st.slider(
        "**Выберите диапазон дат**",
        min_value=min_date.date(),
        max_value=max_date.date(),
        value=(min_date.date(), max_date.date())
    )

    historical_data_types = st.multiselect("**Исторические данные**",
                                           ['C5TC FACT', 'P5TC FACT', 'Brent Oil', 'C5TC / P5TC'],
                                           default=['C5TC FACT', 'P5TC FACT',
                                                    'C5TC / P5TC'])  # Добавил P5TC по умолчанию

    if "Brent Oil" in historical_data_types and "C5TC / P5TC" in historical_data_types:
        st.warning("Нельзя выбрать 'Brent Oil' и 'C5TC / P5TC' одновременно. Оставьте только один вариант.")
        st.stop()

    if "C5TC / P5TC" in historical_data_types and (
            'C5TC FACT' not in historical_data_types or 'P5TC FACT' not in historical_data_types):
        st.warning("Для расчета 'C5TC / P5TC' необходимо выбрать 'C5TC FACT' и 'P5TC FACT'.")
        st.stop()

if uploaded_file:
    low_thresholds = parse_thresholds(low_thresholds_input, [0.75, 0.5])
    high_thresholds = parse_thresholds(high_thresholds_input, [1.75, 2.0])

    if low_thresholds is not None and high_thresholds is not None and selected_dates:
        plotter = FFAForecastPlotter(df, sma_90=sma_90,
                                     sma_200=sma_200,
                                     ewma_30=ewma_30,
                                     ewma_90=ewma_90,
                                     rolling_std_90=rolling_std_90,
                                     rolling_std_200=rolling_std_200)

        # --- ИЗМЕНЕНИЕ 1: Присваиваем результат вызова переменной ---
        final_signals = plotter.plot_forecast(historical_data_types, forecast_types, selected_dates, start_date,
                                              end_date,
                                              average_forcast_mode, average_forcast_mode_group,
                                              low_thresholds=low_thresholds,
                                              high_thresholds=high_thresholds)

        # --- ИЗМЕНЕНИЕ 2: Выводим таблицу с сигналами под графиком ---
        st.markdown("---")  # Горизонтальная линия для разделения
        st.subheader("Сработавшие сигналы")

        if not final_signals.empty:
            # Выбираем и переименовываем нужные колонки для красивого вывода
            display_df = final_signals[['ArchiveDate', 'Type', 'Threshold', 'Ratio']].copy()
            display_df.rename(columns={
                'ArchiveDate': 'Дата сигнала',
                'Type': 'Тип (L/S)',
                'Threshold': 'Пробитый порог',
                'Ratio': 'Значение Ratio'
            }, inplace=True)

            # Форматируем дату и число для лучшей читаемости
            display_df['Дата сигнала'] = display_df['Дата сигнала'].dt.strftime('%d-%m-%Y')
            display_df['Значение Ratio'] = display_df['Значение Ratio'].map('{:,.2f}'.format)

            st.dataframe(display_df, use_container_width=True)


        else:
            st.info("В выбранном диапазоне сигналов по заданным порогам не найдено.")
