import boto3
import json
import logging
import os
from urllib.parse import unquote_plus

logger = logging.getLogger()
logger.setLevel("INFO")

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

reckognition = boto3.client("rekognition")
table = dynamodb.Table(os.getenv("DYNAMO_TABLE"))

def lambda_handler(event):
    # Log
    logger.info(json.dumps(event, indent=2))

    # Récupérations
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = unquote_plus(event["Records"][0]["s3"]["object"]["key"])

    user, task_id = key.split("/")[:2]

    # Ajout de USER# et POST# 
    user, task_id = "USER#" + user, "POST#" + task_id

    # Rekognition
    label_data = reckognition.detect_labels(
        Image={"S3Object": {"Bucket": bucket, "Name": key}},
        MaxLabels=5,
        MinConfidence=0.75)

    logger.info(f"Labels data : {label_data}")
    labels = [label["Name"] for label in label_data["Labels"]]
    logger.info(f"Labels detected : {labels}")

    table.update_item(
        Key={"user": user, "id": task_id},
        UpdateExpression="SET labels = :labels",
        ExpressionAttributeValues={":labels": labels})

    url = s3.generate_presigned_url(
        Params={
            "Bucket": bucket,
            "Key": key,
        },
        ClientMethod="get_object")

    table.update_item(
        Key={"user": user, "id": task_id},
        UpdateExpression="SET image = :url",
        ExpressionAttributeValues={":url": url}
    )
