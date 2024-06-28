import json
import boto3
from botocore.exceptions import ClientError
import os

def lambda_handler(event, __):
    client = boto3.client('cognito-idp', region_name=os.environ['REGION_NAME'])
    client_id = os.environ['CLIENT_ID']

    try:
        body_parameters = json.loads(event["body"])
        username = body_parameters.get('username')
        password = body_parameters.get('password')
        new_password = body_parameters.get('new_password')  # New password field

        response = client.initiate_auth(
            ClientId=client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )

        # Registrar la respuesta completa para depuración
        print("Response from Cognito:", json.dumps(response))

        if 'ChallengeName' in response and response['ChallengeName'] == 'NEW_PASSWORD_REQUIRED':
            if new_password:
                # Si se requiere una nueva contraseña y se proporciona
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

                if 'AuthenticationResult' in response:
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
                else:
                    return {
                        'statusCode': 400,
                        'body': json.dumps({"error_message": "Authentication failed after new password"})
                    }
            else:
                return {
                    'statusCode': 400,
                    'body': json.dumps({"error_message": "New password is required"})
                }
        elif 'AuthenticationResult' in response:
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
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({"error_message": "Authentication failed", "response": response})
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
