from fastapi import FastAPI
import pandas as pd
import base64

# from io import BytesIO
import pickle
from pipeline import preprocess_data, predict_with_model

app = FastAPI()


def encode_dataframe(df: pd.DataFrame):
    pickled = pickle.dumps(df)
    pickled_b64 = base64.b64encode(pickled)
    hug_pickled_str = pickled_b64.decode("utf-8")
    return hug_pickled_str


@app.post("/predict/")
async def predict(payload: dict):
    """
    Интерфейс предсказания.
    Получает данные, предобрабатывает их и вызывает модель для предсказания и доверительных интервалов.
    """
    target_name = payload["target_name"]
    date_name = payload["date_name"]
    segment_name = payload["segment_name"]
    data = payload["data"]
    data_future = payload["data_future"]
    columns_types = payload["columns_types"]
    target_segment_names = payload["target_segment_names"]
    horizon = payload["horizon"]
    granularity = payload["granularity"]
    model_name = payload["model"]
    metric = payload["metric"]
    top_k_percent_features = payload["top_k_percent_features"]
    is_template = payload["is_template"]

    df = pickle.loads(base64.b64decode(data.encode()))
    df_future = pickle.loads(base64.b64decode(data_future.encode()))

    df, df_future = preprocess_data(df, data_future, columns_types, target_name, date_name, segment_name, granularity, is_template)
    prediction_df, metrics_df = predict_with_model(
        df,
        df_future,
        target_segment_names,
        horizon,
        model_name,
        metric,
        top_k_percent_features=top_k_percent_features,
    )

    encoded_predictions = encode_dataframe(prediction_df)
    encoded_metrics = encode_dataframe(metrics_df)

    return {
        "encoded_predictions": encoded_predictions,
        "encoded_metrics": encoded_metrics,
    }
