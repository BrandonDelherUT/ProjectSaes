import json
import boto3
from botocore.exceptions import ClientError
import os

def lambda_handler(event, context):
    # Inicializa el cliente de Cognito
    client = boto3.client('cognito-idp', region_name=os.environ['REGION_NAME'])
    user_pool_id = os.environ['USER_POOL_ID']

    try:
        # Obtiene los parámetros del cuerpo de la solicitud
        body_parameters = json.loads(event["body"])
        username = body_parameters.get('username')

        # Verifica que el parámetro username esté presente
        if not username:
            return {
                'statusCode': 400,
                'body': json.dumps({"error_message": "Username is required"})
            }

        # Obtiene la información del usuario de Cognito
        response = client.admin_get_user(
            UserPoolId=user_pool_id,
            Username=username
        )

        # Procesa la información del usuario
        user_attributes = {}
        for attr in response['UserAttributes']:
            user_attributes[attr['Name']] = attr['Value']

        # Verifica que el usuario sea un administrador
        groups_response = client.admin_list_groups_for_user(
            UserPoolId=user_pool_id,
            Username=username
        )
        groups = [group['GroupName'] for group in groups_response['Groups']]

        if 'admin' not in groups:
            return {
                'statusCode': 403,
                'body': json.dumps({"error_message": "User is not an admin"})
            }

        # Retorna la información del perfil del usuario administrador
        return {
            'statusCode': 200,
            'body': json.dumps({"message": "Profile Admin access successful", "user_attributes": user_attributes})
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
