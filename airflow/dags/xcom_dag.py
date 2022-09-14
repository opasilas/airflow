from airflow.models import DAG
from airflow.providers.sqlite.operators.sqlite import SqliteOperator
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator
from airflow.utils.task_group import TaskGroup

from datetime import datetime
from random import uniform

default_args = {
    'start_date': datetime(2022, 1, 1)
}

def _training_models(ti):
    accuracy = uniform(0.1, 10.0)
    ti.xcom_push(key='model_accuracy', value= accuracy)

def _choose_best_model(ti):
    accuracies = ti.xcom_pull(key='model_accuracy', task_ids=[
        'processing_data.training_model_a',
        'processing_data.training_model_b',
        'processing_data.training_model_c'
    ])
    print(f'these are your accuracies {accuracies}')
    for accuracy in accuracies:
        if accuracy > 5:
            return 'accurate'
    return 'inaccurate'

with DAG('xcom_dag', schedule_interval= '@daily', 
        default_args= default_args, catchup= False) as dag:
    
    downloading_data = BashOperator(
        task_id= 'downloading_data',
        bash_command= 'sleep 3',
        do_xcom_push= False
    )

    with TaskGroup('processing_data') as processing_data:
        training_model_a = PythonOperator(
            task_id= 'training_model_a',
            python_callable= _training_models
        )

        training_model_b = PythonOperator(
            task_id= 'training_model_b',
            python_callable= _training_models
        )

        training_model_c = PythonOperator(
            task_id= 'training_model_c',
            python_callable= _training_models
        )

    choose_model= BranchPythonOperator(
        task_id= 'choose_model',
        python_callable= _choose_best_model
    )

    accurate = DummyOperator(
        task_id= 'accurate'
    )

    inaccurate = DummyOperator(
        task_id= 'inaccurate'
    )    

    storing_user= DummyOperator(
        task_id='storing_user',
        trigger_rule= 'none_failed_or_skipped' #one_success works but this is best practice
    )

    downloading_data >> processing_data >> choose_model
    choose_model >> [accurate, inaccurate] >> storing_user
