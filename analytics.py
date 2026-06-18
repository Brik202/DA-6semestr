import pandas as pd
import plotly.express as px


def read_dataset(uploaded_file):
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".csv"):
        return pd.read_csv(uploaded_file)

    if file_name.endswith(".xlsx") or file_name.endswith(".xls"):
        return pd.read_excel(uploaded_file)

    raise ValueError("Поддерживаются только CSV и Excel файлы.")


def get_dataset_info(df: pd.DataFrame) -> dict:
    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_names": list(df.columns),
        "missing_values": int(df.isna().sum().sum()),
        "duplicates": int(df.duplicated().sum()),
    }


def get_column_types(df: pd.DataFrame) -> pd.DataFrame:
    data = []

    for column in df.columns:
        data.append({
            "Столбец": column,
            "Тип данных": str(df[column].dtype),
            "Пропуски": int(df[column].isna().sum()),
            "Уникальные значения": int(df[column].nunique())
        })

    return pd.DataFrame(data)


def get_numeric_summary(df: pd.DataFrame) -> pd.DataFrame:
    numeric_df = df.select_dtypes(include="number")

    if numeric_df.empty:
        return pd.DataFrame()

    return numeric_df.describe().T


def get_categorical_summary(df: pd.DataFrame) -> dict:
    result = {}
    categorical_columns = df.select_dtypes(include=["object", "category"]).columns

    for column in categorical_columns:
        table = df[column].value_counts().head(10).reset_index()
        table.columns = [column, "Количество"]
        result[column] = table

    return result


def create_basic_charts(df: pd.DataFrame):
    charts = []

    if "category" in df.columns:
        category_counts = df["category"].value_counts().reset_index()
        category_counts.columns = ["Категория", "Количество"]
        charts.append(
            px.bar(
                category_counts,
                x="Категория",
                y="Количество",
                title="Количество товаров по категориям"
            )
        )

    if "brand" in df.columns:
        brand_counts = df["brand"].value_counts().head(10).reset_index()
        brand_counts.columns = ["Бренд", "Количество"]
        charts.append(
            px.bar(
                brand_counts,
                x="Бренд",
                y="Количество",
                title="Топ брендов по количеству товаров"
            )
        )

    if "price" in df.columns:
        charts.append(
            px.histogram(
                df,
                x="price",
                nbins=10,
                title="Распределение товаров по цене"
            )
        )

    if "price" in df.columns and "orders" in df.columns:
        color_column = "category" if "category" in df.columns else None
        charts.append(
            px.scatter(
                df,
                x="price",
                y="orders",
                color=color_column,
                hover_data=[c for c in ["brand", "description", "rating", "stock"] if c in df.columns],
                title="Связь цены и количества заказов"
            )
        )

    return charts


def get_product_metrics(df: pd.DataFrame) -> dict:
    metrics = {}

    if "price" in df.columns:
        metrics["avg_price"] = round(float(df["price"].mean()), 2)
        metrics["min_price"] = float(df["price"].min())
        metrics["max_price"] = float(df["price"].max())

    if "orders" in df.columns:
        metrics["total_orders"] = int(df["orders"].sum())
        metrics["avg_orders"] = round(float(df["orders"].mean()), 2)

    if "rating" in df.columns:
        metrics["avg_rating"] = round(float(df["rating"].mean()), 2)

    if "stock" in df.columns:
        metrics["total_stock"] = int(df["stock"].sum())

    return metrics


def prepare_summary_for_llm(df: pd.DataFrame) -> str:
    info = get_dataset_info(df)
    column_types = get_column_types(df)
    product_metrics = get_product_metrics(df)

    text = []
    text.append("Датасет содержит товары интернет-магазина.")
    text.append(f"Количество строк: {info['rows']}")
    text.append(f"Количество столбцов: {info['columns']}")
    text.append(f"Пропущенные значения: {info['missing_values']}")
    text.append(f"Дубликаты: {info['duplicates']}")
    text.append(f"Названия столбцов: {', '.join(info['column_names'])}")

    if product_metrics:
        text.append("\nКлючевые товарные метрики:")
        for key, value in product_metrics.items():
            text.append(f"{key}: {value}")

    text.append("\nТипы столбцов:")
    text.append(column_types.to_string(index=False))

    numeric_summary = get_numeric_summary(df)
    if not numeric_summary.empty:
        text.append("\nСтатистика по числовым столбцам:")
        text.append(numeric_summary.to_string())

    categorical_summary = get_categorical_summary(df)
    if categorical_summary:
        text.append("\nТоп значений по категориальным столбцам:")
        for column, table in categorical_summary.items():
            text.append(f"\nСтолбец: {column}")
            text.append(table.to_string(index=False))

    if "orders" in df.columns:
        cols = [c for c in ["description", "brand", "category", "price", "rating", "orders", "stock"] if c in df.columns]
        text.append("\nТоп товаров по заказам:")
        text.append(df.sort_values("orders", ascending=False)[cols].head(10).to_string(index=False))

    sample = df.head(10).to_string(index=False)
    text.append("\nПервые 10 строк датасета:")
    text.append(sample)

    return "\n".join(text)
