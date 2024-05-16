import json
from urllib.parse import unquote_plus
import boto3
import os
import logging

# print('Loading function')

# logger = logging.getLogger()
# logger.setLevel("INFO")

# s3 = boto3.client('s3')
# dynamodb = boto3.resource('dynamodb')
# reckognition = boto3.client('rekognition')

# table = dynamodb.Table(os.getenv("table"))

# def lambda_handler(event, context):
#     # Log the received event
#     logger.info("Received event: " + json.dumps(event, indent=2))

#     # Loop through each record in the event
#     for record in event['Records']:
#         bucket = record['s3']['bucket']['name']
#         key = unquote_plus(record['s3']['object']['key'])
        
#         # Extract user and post_id from the key assuming key structure: user/post_id/image.jpg
#         user, post_id, _ = key.split('/')
        
#         try:
#             # Detect labels in the image using Amazon Rekognition
#             response = rekognition.detect_labels(
#                 Image={'S3Object': {'Bucket': bucket, 'Name': key}},
#                 MaxLabels=10,
#                 MinConfidence=80
#             )
            
#             labels = [label['Name'] for label in response['Labels']]
            
#             # Update the DynamoDB table with the detected labels
#             table.update_item(
#                 Key={
#                     'user': f'USER#{user}',
#                     'id': post_id
#                 },
#                 UpdateExpression="SET labels = :labels",
#                 ExpressionAttributeValues={':labels': labels}
#             )
            
#             logger.info(f"Successfully processed image {key} from bucket {bucket}")

#         except Exception as e:
#             logger.error(f"Error processing {key} from bucket {bucket}. Error: {str(e)}")

#     return {
#         'statusCode': 200,
#         'body': json.dumps('Processing complete.')
#     }