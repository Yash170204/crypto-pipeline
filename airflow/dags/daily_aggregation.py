from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from aggregation import DailyAggregator


def run_daily_aggregation(**context):
    execution_date = context['execution_date']
    aggregator = DailyAggregator()
    aggregator.aggregate_for_date(execution_date)


default_args = {
    'owner': 'data-eng',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'crypto_daily_aggregation',
    default_args=default_args,
    description='Aggregate 24-hour crypto market data',
    schedule_interval='0 1 * * *',
    catchup=False,
    tags=['crypto', 'aggregation'],
)

aggregate_task = PythonOperator(
    task_id='aggregate_24h_data',
    python_callable=run_daily_aggregation,
    provide_context=True,
    dag=dag,
)
