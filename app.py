import streamlit as st

from analytics import (
    read_dataset,
    get_dataset_info,
    get_column_types,
    get_numeric_summary,
    get_product_metrics,
    create_basic_charts,
    prepare_summary_for_llm,
)
from agent import generate_report


st.set_page_config(
    page_title="LLM-аналитика товаров",
    layout="wide"
)

st.title("LLM-аналитика товаров интернет-магазина")

st.write(
    "Приложение анализирует датасет с товарами. Пользователь загружает CSV или Excel-файл, "
    "после чего система показывает метрики, строит графики и формирует аналитический отчет через LLM-агента."
)

uploaded_file = st.file_uploader(
    "Загрузите файл с товарами",
    type=["csv", "xlsx", "xls"]
)

user_instruction = st.text_area(
    "Инструкция для анализа",
    value="""Проанализируй товары интернет-магазина.
Определи:
- ключевые метрики по цене, рейтингу, заказам и складу;
- самые популярные категории и бренды;
- товары с высоким спросом;
- связь цены и количества заказов;
- рекомендации для маркетинга, ассортимента и управления складом.
Сформируй аналитический отчет.""",
    height=220
)

if uploaded_file is not None:
    try:
        df = read_dataset(uploaded_file)

        st.subheader("Предпросмотр данных")
        st.dataframe(df.head(30), use_container_width=True)

        expected_columns = ["id", "description", "brand", "category", "price"]
        missing_expected = [column for column in expected_columns if column not in df.columns]

        if missing_expected:
            st.warning(
                "В датасете отсутствуют ожидаемые столбцы: "
                + ", ".join(missing_expected)
            )
        else:
            st.success("Файл соответствует ожидаемой структуре датасета товаров.")

        info = get_dataset_info(df)
        metrics = get_product_metrics(df)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Количество строк", info["rows"])
        col2.metric("Количество столбцов", info["columns"])
        col3.metric("Пропущенные значения", info["missing_values"])
        col4.metric("Дубликаты", info["duplicates"])

        if metrics:
            st.subheader("Ключевые метрики")
            metric_cols = st.columns(min(len(metrics), 4))
            for index, (name, value) in enumerate(metrics.items()):
                label = {
                    "avg_price": "Средняя цена",
                    "min_price": "Минимальная цена",
                    "max_price": "Максимальная цена",
                    "total_orders": "Всего заказов",
                    "avg_orders": "Среднее число заказов",
                    "avg_rating": "Средний рейтинг",
                    "total_stock": "Остаток на складе"
                }.get(name, name)
                metric_cols[index % len(metric_cols)].metric(label, value)

        with st.expander("Типы столбцов"):
            st.dataframe(get_column_types(df), use_container_width=True)

        numeric_summary = get_numeric_summary(df)
        if not numeric_summary.empty:
            with st.expander("Описательная статистика"):
                st.dataframe(numeric_summary, use_container_width=True)

        st.subheader("Графики")
        charts = create_basic_charts(df)

        if charts:
            for start in range(0, len(charts), 2):
                cols = st.columns(2)
                for offset, fig in enumerate(charts[start:start + 2]):
                    fig.update_layout(height=380, margin=dict(l=10, r=10, t=55, b=35))
                    with cols[offset]:
                        st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Для данного датасета не удалось автоматически построить графики.")

        st.subheader("LLM-отчет агента")
        st.write(
            "После нажатия кнопки Python-инструменты подготовят сводку по данным, "
            "а LLM-агент через OpenRouter сформирует аналитический отчет."
        )

        if st.button("Сгенерировать отчет"):
            with st.spinner("Агент анализирует данные и формирует отчет..."):
                dataset_summary = prepare_summary_for_llm(df)
                report = generate_report(dataset_summary, user_instruction)
                st.markdown(report)

    except Exception as e:
        st.error(f"Ошибка при обработке файла: {e}")
else:
    st.info("Загрузите файл `products.csv`, чтобы начать анализ.")
