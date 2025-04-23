import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta
from bdi_plot_maker import FFAForecastPlotter


@st.cache_data
def load_and_process_data(uploaded_file):
    df = pd.read_excel(uploaded_file, parse_dates=['ArchiveDate', 'StartDate'])
    df['ArchiveDate'] = pd.to_datetime(df['ArchiveDate'], format='%Y-%m-%d', errors='coerce')  # Приводим к единому типу
    return df


st.markdown("""
    <style>
        .block-container {
            max-width: 1300px; /* Ограничение общей ширины */
        }
        .custom-column {
            width: 80%; /* Настроенная ширина */
        }
    </style>
""", unsafe_allow_html=True)


def empty_date_checker(df, selected_date):
    """Проверяет, есть ли данные для выбранной даты."""
    selected_date = pd.to_datetime(selected_date)  # Приводим к единому типу
    return not df[(df['GroupDesc'] == 'BFA Cape') & (df['ArchiveDate'] == selected_date)].empty


# Загрузка файла
uploaded_file = st.file_uploader("Загрузите Excel-файл", type=["xlsx"])

col1, col2, col3 = st.columns([1.7, 1, 0.5])
if uploaded_file:
    with col1:
        df = load_and_process_data(uploaded_file)
        df['ArchiveDate'] = pd.to_datetime(df['ArchiveDate'], format='%Y-%m-%d',
                                           errors='coerce')  # Убедимся, что тип datetime

        min_date = df.loc[df['GroupDesc'] == 'BFA Cape', 'ArchiveDate'].min()
        max_date = df.loc[df['GroupDesc'] == 'BFA Cape', 'ArchiveDate'].max()
        # Выбор режима
        mode = st.radio("**Выберите режим**", ["Одна дата", "Несколько дат", "Месяц целиком"])

        if mode == "Одна дата":
            selected_date = st.date_input("**Выберите дату**", min_value=min_date, max_value=max_date)
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

            available_dates = df[
                (df['GroupDesc'] == 'BFA Cape') &
                (df['ArchiveDate'].dt.strftime('%Y-%m').isin(selected_months))
                ]['ArchiveDate'].unique()
            selected_dates = st.multiselect("Выберите даты", sorted(available_dates),
                                            format_func=lambda x: x.strftime('%Y-%m-%d'))
            if not selected_dates:
                st.write("⚠️ Выберите хотя бы одну дату.")
                st.stop()




        elif mode == "Месяц целиком":
            # Доступные месяцы
            bfa_df = df[df['GroupDesc'] == 'BFA Cape']
            available_months = sorted(bfa_df['ArchiveDate'].dt.strftime('%Y-%m').unique(), reverse=True)
            default_month = available_months[1] if len(available_months) > 1 else available_months[
                0] if available_months else None
            selected_months = st.multiselect("Выберите месяц", available_months,
                                             default=[default_month] if default_month else [])
            if selected_months:
                selected_dates = []
                for selected_month in selected_months:
                    month_dates = df[
                        (df['GroupDesc'] == 'BFA Cape') &  # <-- добавили этот фильтр
                        (df['ArchiveDate'].dt.strftime('%Y-%m') == selected_month)
                        ]['ArchiveDate'].unique()
                    selected_dates.extend(month_dates)
                selected_dates = sorted(set(selected_dates))
            else:
                selected_dates = []

        forecast_types = st.multiselect("**Выберите тип прогноза**",
                                        ['Monthly Contract (MON)', 'Quarterly Contract (Q)',
                                         'Calendar Year Contract (CAL)'],
                                        default=['Monthly Contract (MON)'])
        if not forecast_types:
            st.warning("⚠️ Пожалуйста, выберите хотя бы один тип прогноза.")
            st.stop()  # Останавливает дальнейшее выполнение кода, если нет выбора

    with col2:
        # Заголовок
        st.markdown("**Настройки скользящих средних**")

        # Чекбоксы для скользящих средних
        sma_90 = st.checkbox("90-дневная скользящая средняя", value=False)
        sma_200 = st.checkbox("200-дневная скользящая средняя", value=False)

        # Инициализация состояния для среднеквадратичного отклонения (когда sma_90 выключено)
        if sma_90:
            rolling_std_90 = st.checkbox(
                "Среднеквадратическое отклонение (окно 90 дней)",
                value=True  # Если sma_90 выбрана, то можно установить значение True
            )
        else:
            rolling_std_90 = st.checkbox(
                "Среднеквадратическое отклонение (окно 90 дней)",
                value=False,  # Если sma_90 не выбрана, то сбрасываем галочку
                disabled=True  # И делаем недоступным
            )
        if sma_200:
            rolling_std_200 = st.checkbox(
                "Среднеквадратическое отклонение (окно 200 дней)",
                value=True  # Если sma_90 выбрана, то можно установить значение True
            )
        else:
            rolling_std_200 = st.checkbox(
                "Среднеквадратическое отклонение (окно 200 дней)",
                value=False,  # Если sma_90 не выбрана, то сбрасываем галочку
                disabled=True  # И делаем недоступным
            )  # Чекбоксы для экспоненциальных скользящих средних
        ewma_90 = st.checkbox("90-дневная экспоненциальная скользящая средняя", value=False)
        ewma_30 = st.checkbox("30-дневная экспоненциальная скользящая средняя", value=False)

    with col3:
        st.markdown("### Доп. настройки")
        average_forcast_mode = st.checkbox(
            "Усреднить прогнозы",
            value=False
        )

        group_options = {
            "Месяцам": "month",
            "Кварталам": "quarter"
        }

        average_forcast_mode_group = st.selectbox(
            "Группировать при усреднении по:",
            options=[False, "Месяцам","Месяца до кварталов"],
            index=0,
            disabled=not average_forcast_mode
        )


    start_date, end_date = st.slider(
        "**Выберите диапазон дат**",
        min_value=min_date.date(),
        max_value=max_date.date(),
        value=(min_date.date(), max_date.date(),
               ))
    historical_data_types = st.multiselect("**Исторические данные**",
                                           ['C5TC FACT', 'P5TC FACT',
                                            'Brent Oil', 'C5TC / P5TC'],
                                           default=['C5TC FACT'])
    if "Brent Oil" in historical_data_types and "C5TC / P5TC" in historical_data_types:
        st.warning(
            "Нельзя выбрать одновременно 'Brent Oil' и 'C5TC / P5TC'. Оставлена только первая выбранная метрика.")
        historical_data_types.remove("C5TC / P5TC")  # Убираем C5TC / P5TC
    if ("C5TC / P5TC" in historical_data_types) and (
            "C5TC FACT" not in historical_data_types or 'P5TC FACT' not in historical_data_types):
        st.warning("Для расчета C5TC / P5TC необходимо выбрать оба показателя: C5TC FACT и P5TC FACT.")
        st.stop()

    # Построение графика после выбора параметров
if uploaded_file:
    # if st.button("Построить график") and selected_dates:
    #     plot_ffa_forecast(df,historical_data_types, forecast_types, selected_dates, start_date, end_date, sma_90, sma_200, ewma_30, ewma_90,
    #                       rolling_std_90, rolling_std_200)
    plotter = FFAForecastPlotter(df, sma_90=sma_90,
                                 sma_200=sma_200,
                                 ewma_30=ewma_30,
                                 ewma_90=ewma_90,
                                 rolling_std_90=rolling_std_90,
                                 rolling_std_200=rolling_std_200)
    plotter.plot_forecast(historical_data_types, forecast_types, selected_dates, start_date, end_date,
                          average_forcast_mode,average_forcast_mode_group)
