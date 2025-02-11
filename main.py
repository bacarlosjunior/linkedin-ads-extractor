from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from datetime import datetime, timedelta
import sys
import json
import os
from readConfig import*
from refresh_tokens import*
import logging
logger = logging.getLogger()
import pandas as pd
import base64
from google.cloud import storage
from get_ln_campaign_data import get_LinkedIn_campaign, get_LinkedIn_campaigns_list

# credentials to get access google cloud storage
# write your key path in place of gcloud_private_key.json
storage_client = storage.Client()

# write your bucket name in place of bucket1go
bucket_name = 'extractors-ads'
BUCKET = storage_client.get_bucket(bucket_name)

def get_json(filename):
    '''
    this function will get the json object from
    google cloud storage bucket
    '''
    # get the blob
    blob = BUCKET.get_blob(filename)
    # load blob using json
    file_data = json.loads(blob.download_as_string())
    return file_data

client = bigquery.Client()


schema = [

    bigquery.SchemaField("campaign_id",  bigquery.enums.SqlTypeNames.STRING, mode="REQUIRED"),
    bigquery.SchemaField("creative_id",  bigquery.enums.SqlTypeNames.STRING, mode="REQUIRED"),
    bigquery.SchemaField("date",  bigquery.enums.SqlTypeNames.DATE, mode="REQUIRED"),
    bigquery.SchemaField("cost_in_brl", bigquery.enums.SqlTypeNames.FLOAT, mode="REQUIRED"),
    bigquery.SchemaField("impressions",  bigquery.enums.SqlTypeNames.INTEGER, mode="REQUIRED"),
    bigquery.SchemaField("clicks",  bigquery.enums.SqlTypeNames.INTEGER, mode="REQUIRED"),
    bigquery.SchemaField("campaign_name",  bigquery.enums.SqlTypeNames.STRING, mode="REQUIRED"),
    bigquery.SchemaField("campaign_account",  bigquery.enums.SqlTypeNames.STRING, mode="REQUIRED"),
    bigquery.SchemaField("website_conversions",  bigquery.enums.SqlTypeNames.INTEGER, mode="REQUIRED"),
    bigquery.SchemaField("total_engagements",  bigquery.enums.SqlTypeNames.INTEGER, mode="REQUIRED"),
    
]

clustering_fields_ln = ['campaign_name']


def exist_dataset_table(client, table_id, dataset_id, project_id, schema, clustering_fields=None):
    try:
        dataset_ref = "{}.{}".format(project_id, dataset_id)
        client.get_dataset(dataset_ref)  # Make an API request.

    except NotFound:
        dataset_ref = "{}.{}".format(project_id, dataset_id)
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = "US"
        dataset = client.create_dataset(dataset)  # Make an API request.
        logger.info("Created dataset {}.{}".format(
            client.project, dataset.dataset_id))

    try:
        table_ref = "{}.{}.{}".format(project_id, dataset_id, table_id)
        client.get_table(table_ref)  # Make an API request.

    except NotFound:

        table_ref = "{}.{}.{}".format(project_id, dataset_id, table_id)

        table = bigquery.Table(table_ref, schema=schema)

        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="date"
        )

        if clustering_fields is not None:
            table.clustering_fields = clustering_fields

        table = client.create_table(table)  # Make an API request.
        logger.info("Created table {}.{}.{}".format(
            table.project, table.dataset_id, table.table_id))

    return True


def insert_df_bq(schema,client, table_id, dataset_id, project_id, ads_analytics_data):

    table_ref = '{}.{}.{}'.format(project_id, dataset_id, table_id)
    table = client.get_table(table_ref)
    job_config = bigquery.LoadJobConfig(schema=schema)

    job = client.load_table_from_dataframe(ads_analytics_data,table, job_config = job_config)

    result = job.result()
    if  result == False:
        print('No results in insert_df_bq')
    else:
        print("Success uploaded to table {}".format(table.table_id))

def today_func():
    today = datetime.now()
    return today

today = today_func()
yesterday = (today - timedelta(1))

def interval_day(choice):
    if choice == 'yesterday':
        return yesterday.strftime("%Y-%m-%d")
    elif choice == 'past_90':
        lifetime =  (today - timedelta(90))
        return lifetime.strftime("%Y-%m-%d")

def main_linkedin(event,context):

    token_cred_json = get_json('ln_token_cred.json')
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')

    if pubsub_message == 'get_linkedin':
        table_id = event['attributes']['table_id']
        dataset_id = event['attributes']['dataset_id']
        project_id = event['attributes']['project_id']
        date_preset = event['attributes']['date_preset']
        account_id = event['attributes']['account_id']
        user_name = event['attributes']['username']

        for user in token_cred_json:
            if user_name == user['username']:
                access_token = user['access_token']

        #Setando as datas de inicio e fim
        s_date = interval_day(date_preset)
        e_date = yesterday.strftime("%Y-%m-%d")
        qry_type = "day"

        #reading campaign type reference json file
        campaign_type_file = "campaign_category.json"
        campaign_type_file = open(campaign_type_file, 'r')
        camapign_type_json = json.load(campaign_type_file)

        ln_campaign_df = get_LinkedIn_campaigns_list(access_token,account_id,camapign_type_json)

        try:            
            campaign_ids = ln_campaign_df["campaign_id"]
            ln_campaign_analytics = get_LinkedIn_campaign(access_token,campaign_ids,s_date,e_date,qry_type)
            merge_campaign_analytics = pd.merge(ln_campaign_analytics,ln_campaign_df, how = 'inner', on = 'campaign_id')
            bq_campaign_analytics = merge_campaign_analytics
            bq_campaign_analytics["campaign_id"] = merge_campaign_analytics["campaign_id"].astype(bytes)

            exist_dataset_table(client, table_id, dataset_id, project_id, schema, clustering_fields_ln)
            insert_df_bq(schema,client, table_id, dataset_id, project_id, bq_campaign_analytics[["campaign_id","date",
            "creative_id","cost_in_brl","impressions","clicks","campaign_name","campaign_account","website_conversions","total_engagements"]])

        except:

            ln_campaign_df = pd.DataFrame(columns=["campaign_name", "campaign_id", "campaign_account",
                                                    "daily_budget", "unit_cost", "objective_type", "campaign_status", "campaign_type"])

            exist_dataset_table(client, table_id, dataset_id, project_id, schema, clustering_fields_ln)
            insert_df_bq(schema,client, table_id, dataset_id, project_id, bq_campaign_analytics[["campaign_id","date",
            "creative_id","cost_in_brl","impressions","clicks","campaign_name","campaign_account","website_conversions","total_engagements"]])
            
            print("\n!!Dataframe (campaigns_df) is empty !!!")
            sys.exit()
            
