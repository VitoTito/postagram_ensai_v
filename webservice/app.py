import boto3
from boto3.dynamodb.conditions import Key
from botocore.config import Config
import os
from dotenv import load_dotenv
from typing import Union
import logging
from fastapi import FastAPI, Request, status, Header
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import uuid
import json

from getSignedUrl import getSignedUrl

load_dotenv()

app = FastAPI()
logger = logging.getLogger("uvicorn")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
    logger.error(f"{request}: {exc_str}")
    content = {"status_code": 10422, "message": exc_str, "data": None}
    return JSONResponse(
        content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


class Post(BaseModel):
    title: str
    body: str


my_config = Config(
    region_name="us-east-1",
    signature_version="v4",
)

dynamodb = boto3.resource("dynamodb", config=my_config)

table = dynamodb.Table(os.getenv("DYNAMO_TABLE"))
s3_client = boto3.client("s3", config=boto3.session.Config(signature_version="s3v4"))
bucket = os.getenv("BUCKET")


@app.get("/")
async def read_root():
    return "API is running"


@app.post("/posts")
async def post_a_post(post: Post, authorization: str | None = Header(default=None)):

    logger.info(f"title : {post.title}")
    logger.info(f"body : {post.body}")
    logger.info(f"user : {authorization}")

    postId = f"POST#{uuid.uuid4()}"

    # Doit retourner le résultat de la requête la table dynamodb
    data = table.put_item(
        Item={
            "user": "USER#" + authorization,
            "id": postId,
            "body": post.body,
            "image": "",
        }
    )

    logger.info("POST data:\n" + json.dumps(data, indent=2))
    return data


@app.get("/posts")
async def get_all_posts(user: Union[str, None] = None):

    if user is None:
        data = table.scan()
    else:
        data = table.query(KeyConditionExpression=Key("user").eq("USER#" + user))

    logger.info("GET data:\n" + json.dumps(data["Items"], indent=2))
    return data["Items"]


@app.delete("/posts/{post_id}")
async def delete_post(post_id: str):
    try:
        # Récupérer le post
        response = table.get_item(Key={"user": "user_placeholder", "id": post_id})
        item = response.get("Item")

        if not item:
            return JSONResponse(
                content={"message": "Post not found"},
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Supprimer l'image du bucket S3 si elle existe
        if "image" in item and item["image"]:
            s3_client.delete_object(Bucket=bucket, Key=item["image"])

        # Supprimer l'élément de la table DynamoDB
        delete_response = table.delete_item(Key={"user": "user_placeholder", "id": post_id})

        return JSONResponse(
            content={"message": "Post deleted successfully", "response": delete_response},
            status_code=status.HTTP_200_OK
        )

    except Exception as e:
        return JSONResponse(
            content={"message": "Error deleting post", "details": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@app.get("/signedUrlPut")
async def get_signed_url_put(
    filename: str,
    filetype: str,
    postId: str,
    authorization: str | None = Header(default=None),
):
    return getSignedUrl(filename, filetype, postId, authorization)


if __name__ == "__main__":
    logger.info("API is starting")
    uvicorn.run(app, host="0.0.0.0", port=80, log_level="debug")
