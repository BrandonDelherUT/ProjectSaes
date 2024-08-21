import json
import boto3
from botocore.exceptions import ClientError
import os
from jose import jwt

def lambda_handler(event, context):
    # Configurar el cliente para DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name=os.environ['REGION_NAME'])
    table = dynamodb.Table(os.environ['USER_PROFILES_TABLE_NAME'])

    cors_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
    }

    try:
        # Obtener el token de autorización del encabezado
        authorization_header = event['headers']['Authorization']
        token = authorization_header.split(' ')[1]

        # Decodificar el token para obtener el user_id (sub)
        user_info = jwt.get_unverified_claims(token)
        user_id = user_info['sub']

        # Obtener los datos del perfil del usuario desde DynamoDB
        response = table.get_item(
            Key={
                'user_id': user_id
            }
        )

        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({"error_message": "User profile not found"})
            }

        # Devolver la información del perfil del usuario
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps(response['Item'])
        }

    except ClientError as e:
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({"error_message": e.response['Error']['Message']})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({"error_message": str(e)})
        }
