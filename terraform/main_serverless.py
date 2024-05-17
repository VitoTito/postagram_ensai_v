#!/usr/bin/env python
from constructs import Construct
from cdktf import App, TerraformStack, TerraformOutput, TerraformAsset, AssetType
from cdktf_cdktf_provider_aws.provider import AwsProvider
from cdktf_cdktf_provider_aws.default_vpc import DefaultVpc
from cdktf_cdktf_provider_aws.default_subnet import DefaultSubnet
from cdktf_cdktf_provider_aws.lambda_function import LambdaFunction
from cdktf_cdktf_provider_aws.lambda_permission import LambdaPermission
from cdktf_cdktf_provider_aws.data_aws_caller_identity import DataAwsCallerIdentity
from cdktf_cdktf_provider_aws.s3_bucket import S3Bucket
from cdktf_cdktf_provider_aws.s3_bucket_cors_configuration import S3BucketCorsConfiguration, S3BucketCorsConfigurationCorsRule
from cdktf_cdktf_provider_aws.s3_bucket_notification import S3BucketNotification, S3BucketNotificationLambdaFunction
from cdktf_cdktf_provider_aws.dynamodb_table import DynamodbTable, DynamodbTableAttribute


class ServerlessStack(TerraformStack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        AwsProvider(self, "AWS", region="us-east-1")
        account_id = DataAwsCallerIdentity(self, "acount_id").account_id
        
        bucket = S3Bucket(
            self, "postagram_s3_bucket",
            bucket_prefix = "store-image-postagram",
            acl = "private",
            force_destroy = True
        )

        S3BucketCorsConfiguration(
            self, "cors",
            bucket = bucket.id,
            cors_rule = [S3BucketCorsConfigurationCorsRule(
                allowed_headers = ["*"],
                allowed_methods = ["GET", "HEAD", "PUT"],
                allowed_origins = ["*"]
            )]
            )

        dynamo_table = DynamodbTable(
            self,
            "postagram_dynamodbtable",
            name="store-posts-postagram",
            hash_key="user",
            range_key="id",
            attribute=[
                DynamodbTableAttribute(name="user", type="S"),
                DynamodbTableAttribute(name="id", type="S")
            ],
            billing_mode="PROVISIONED",
            read_capacity=5,
            write_capacity=5,
            )

        code = TerraformAsset(self, "code", path="./lambda", type=AssetType.ARCHIVE)

        lambda_function = LambdaFunction(
            self,
            'lambda',
            function_name='lambda-rekognit-postagram',
            runtime='python3.9',
            memory_size=128,
            timeout=4,
            role=f"arn:aws:iam::{account_id}:role/LabRole",
            filename=code.path,
            handler='lambda_function.lambda_handler',
            environment={'variables': {
                'BUCKET': bucket.id,
                'DYNAMO_TABLE' : dynamo_table.id}
            }
            )

        permission = LambdaPermission(
            self, "lambda-permission",
            action="lambda:InvokeFunction",
            statement_id="AllowExecutionFromS3Bucket",
            function_name=lambda_function.arn,
            principal="s3.amazonaws.com",
            source_arn=bucket.arn,
            source_account=account_id,
            depends_on=[lambda_function, bucket]
        )

        notification = S3BucketNotification(
            self, "notification",
            lambda_function=[S3BucketNotificationLambdaFunction(
                lambda_function_arn=lambda_function.arn,
                events=["s3:ObjectCreated:*"]
            )],
            bucket=bucket.id,
            depends_on=[permission]
        )

        TerraformOutput(
            self, "dynamo_id",
            value = dynamo_table.id
        )

        TerraformOutput(
            self, "bucket_id",
            value = bucket.id
        )



app = App()
ServerlessStack(app, "serverless_postgram")
app.synth()