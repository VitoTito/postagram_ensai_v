import json
from urllib.parse import unquote_plus
import boto3
import os
import logging

print("Loading function")
logger = logging.getLogger()
logger.setLevel("INFO")
s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
reckognition = boto3.client("rekognition")


table = dynamodb.Table(os.getenv("DYNAMO_TABLE"))


def lambda_handler(event, context):
    # Pour logger
    logger.info(json.dumps(event, indent=2))
    # Récupération du nom du bucket
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    # Récupération du nom de l'objet
    key = unquote_plus(event["Records"][0]["s3"]["object"]["key"])
    # extration de l'utilisateur et de l'id de la tâche
    user, task_id = key.split("/")[:2]
    #On ajoute les tag USER# et POST# car la webapp les enlève systématiquement
    user = "USER#" + user
    task_id = "POST#" + task_id

    # Appel au service, en passant l'image à analyser (bucket et key)
    # On souhaite au maximum 5 labels et uniquement les labels avec un taux de confiance > 0.75
    # Vous pouvez faire varier ces valeurs.
    label_data = reckognition.detect_labels(
        Image={"S3Object": {"Bucket": bucket, "Name": key}},
        MaxLabels=5,
        MinConfidence=0.75,
    )
    logger.info(f"Labels data : {label_data}")
    # On extrait les labels du résultat
    labels = [label["Name"] for label in label_data["Labels"]]
    logger.info(f"Labels detected : {labels}")

    table.update_item(
        Key={"user": user, "id": task_id},
        UpdateExpression="SET labels = :labels",
        ExpressionAttributeValues={":labels": labels},
    )

    url = s3.generate_presigned_url(
        Params={
            "Bucket": bucket,
            "Key": key,
        },
        ClientMethod="get_object",
    )

    table.update_item(
        Key={"user": user, "id": task_id},
        UpdateExpression="SET image = :url",
        ExpressionAttributeValues={":url": url},
    )
