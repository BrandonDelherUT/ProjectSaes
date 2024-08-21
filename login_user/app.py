import json
import boto3
from botocore.exceptions import ClientError
import os

def lambda_handler(event, context):
    client = boto3.client('cognito-idp', region_name=os.environ['REGION_NAME'])
    client_id = os.environ['CLIENT_ID']

    cors_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
    }

    try:
        body_parameters = json.loads(event["body"])
        username = body_parameters.get('username')
        password = body_parameters.get('password')
        new_password = body_parameters.get('newPassword')  # Asegúrate de que el campo coincida con lo que se envía desde el cliente

        if not username or not password:
            return {
                'statusCode': 400,
                'headers': cors_headers,
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

        if response.get('ChallengeName') == 'NEW_PASSWORD_REQUIRED':
            if not new_password:
                return {
                    'statusCode': 400,
                    'headers': cors_headers,
                    'body': json.dumps({"error_message": "New password is required to complete the challenge"})
                }

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

        # Obtener el rol del usuario
        user = client.admin_get_user(UserPoolId=os.environ['USER_POOL_ID'], Username=username)
        role = None
        cognito_username = None  # Almacenar el user_id de cognito
        for attr in user['UserAttributes']:
            if attr['Name'] == 'custom:role':
                role = attr['Value']
            if attr['Name'] == 'sub':  # sub es el cognito:username (user_id)
                cognito_username = attr['Value']

        if not cognito_username:
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({"error_message": "User ID (cognito:username) not found."})
            }

        id_token = response['AuthenticationResult']['IdToken']
        access_token = response['AuthenticationResult']['AccessToken']
        refresh_token = response['AuthenticationResult']['RefreshToken']

        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'id_token': id_token,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'role': role,  # Incluir el rol en la respuesta
                'user_id': cognito_username  # Incluir el cognito:username (user_id) en la respuesta
            })
        }

    except ClientError as e:
        return {
            'statusCode': 400,
            'headers': cors_headers,
            'body': json.dumps({"error_message": e.response['Error']['Message']})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({"error_message": str(e)})
        }
