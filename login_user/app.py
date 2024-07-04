import json
import boto3
from botocore.exceptions import ClientError
import os

def lambda_handler(event, context):
    client = boto3.client('cognito-idp', region_name=os.environ['REGION_NAME'])
    client_id = os.environ['CLIENT_ID']

    try:
        body_parameters = json.loads(event["body"])
        username = body_parameters.get('username')
        password = body_parameters.get('password')
        new_password = body_parameters.get('new_password')

        if not username or not password:
            return {
                'statusCode': 400,
                'body': json.dumps({"error_message": "Username and password are required"})
            }

        response = client.initiate_auth(
            ClientId=client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )

        # Manejar el desafío de cambio de contraseña
        if response.get('ChallengeName') == 'NEW_PASSWORD_REQUIRED':
            session = response['Session']
            response = client.respond_to_auth_challenge(
                ClientId=client_id,
                ChallengeName='NEW_PASSWORD_REQUIRED',
                Session=session,
                ChallengeResponses={
                    'USERNAME': username,
                    'NEW_PASSWORD': new_password
                }
            )

        id_token = response['AuthenticationResult']['IdToken']
        access_token = response['AuthenticationResult']['AccessToken']
        refresh_token = response['AuthenticationResult']['RefreshToken']

        return {
            'statusCode': 200,
            'body': json.dumps({
                'id_token': id_token,
                'access_token': access_token,
                'refresh_token': refresh_token
            })
        }

    except ClientError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({"error_message": e.response['Error']['Message']})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({"error_message": str(e)})
        }
