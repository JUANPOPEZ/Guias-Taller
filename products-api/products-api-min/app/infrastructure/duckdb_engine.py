"""Análisis con DuckDB: los datos se pasan como JSON y se consultan con SQL."""
import json
import os
import tempfile
from dataclasses import asdict

import duckdb

from app.domain.errors import UpstreamFailure
from app.domain.market_data import AnalyticsEngine


def _query(rows, create_table_sql, query_sql):
    if not rows:
        raise UpstreamFailure("There is no data to analyze.")
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(rows, f, default=str, ensure_ascii=False)
        ruta = f.name
    con = duckdb.connect(":memory:")
    try:
        con.execute(create_table_sql, [ruta])      # carga el JSON con read_json_auto
        cursor = con.execute(query_sql)
        columnas = [c[0] for c in cursor.description]
        return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
    finally:
        con.close()
        os.remove(ruta)


class DuckDBAnalyticsEngine(AnalyticsEngine):
    def trm_statistics(self, rates):
        # Consulta 1: estadística descriptiva de la TRM
        return _query(
            [asdict(r) for r in rates],
            "CREATE TABLE trm AS SELECT CAST(fecha AS DATE) AS fecha, "
            "CAST(valor AS DOUBLE) AS valor FROM read_json_auto(?)",
            """SELECT COUNT(*) AS observations,
                      CAST(MIN(fecha) AS VARCHAR) AS from_date,
                      CAST(MAX(fecha) AS VARCHAR) AS to_date,
                      ROUND(AVG(valor), 2) AS mean,
                      ROUND(QUANTILE_CONT(valor, 0.5), 2) AS median,
                      ROUND(MIN(valor), 2) AS minimum,
                      ROUND(MAX(valor), 2) AS maximum,
                      ROUND(STDDEV_SAMP(valor), 2) AS std_deviation
               FROM trm""")[0]

    def municipalities_by_department(self, municipalities):
        # Consulta 2: municipios por departamento
        return _query(
            [asdict(m) for m in municipalities],
            "CREATE TABLE municipios AS SELECT municipio, departamento FROM read_json_auto(?)",
            """SELECT departamento AS department, COUNT(*) AS municipalities
               FROM municipios
               GROUP BY departamento
               ORDER BY municipalities DESC, department""")
