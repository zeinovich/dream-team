from typing import Dict

from fastapi import FastAPI
import hdbscan
from tslearn.metrics import cdist_dtw

import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from utils import decode_dataframe, encode_dataframe

app = FastAPI()


@app.post("/clusterize/")
async def clusterize(payload: Dict[str, str]) -> Dict[str, str]:
    """
    Эндпоинт кластеризации данных.
    Использует расстояния DTW и кластеризацию HDBSCAN.
    Пример ноутбука: https://github.com/zeinovich/dream-team/blob/romanov/notebooks/v0.3-romanov-clustering_ts.ipynb
    """
    # Декодируем данные из base64 в CSV
    data = payload["data"]

    df = decode_dataframe(data)

    items = df["segment"].unique()
    items_ts = {}

    for item in items:
        items_ts[item] = df[df["segment"] == item]["target"].to_list()

    items_ts = pd.DataFrame.from_dict(items_ts, orient="index").T
    items_ts.iloc[:, :] = MinMaxScaler().fit_transform(items_ts)
    items_ts = items_ts.T

    distance_matrix = cdist_dtw(items_ts)

    # Применяем HDBSCAN для кластеризации
    clusterer = hdbscan.HDBSCAN(metric="precomputed", min_cluster_size=2)
    labels = clusterer.fit_predict(distance_matrix)

    # Добавляем метки кластеров к DataFrame
    items_ts["cluster"] = labels
    items_ts.index.name = "segment"
    items_ts = items_ts.reset_index()

    # Кодируем результат обратно в base64
    encoded_result = encode_dataframe(items_ts[["segment", "cluster"]])

    return {"encoded_dataframe": encoded_result}
