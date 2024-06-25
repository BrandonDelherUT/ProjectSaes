import boto3
import json
import os

def get_db_credentials():
    try:
        client = boto3.client('secretsmanager')
        secret_name = os.environ['RDS_SECRET_NAME']
        secret_value = client.get_secret_value(SecretId=secret_name)
        return json.loads(secret_value['SecretString'])
    except Exception as e:
        print(f"Error fetching secret: {e}")
        raise e

def lambda_handler(event, context):
    try:
        # Obtener credenciales de la base de datos desde Secrets Manager
        db_credentials = get_db_credentials()

        # Usar las credenciales para conectarse a la base de datos o cualquier otra lógica
        db_username = db_credentials['username']
        db_password = db_credentials['password']
        db_endpoint = os.environ['RDS_ENDPOINT']
        db_name = os.environ['RDS_DB_NAME']

        # Aquí puedes añadir la lógica para conectar a la base de datos o cualquier otra funcionalidad
        # Ejemplo:
        # connection = create_db_connection(db_endpoint, db_name, db_username, db_password)

        return {
            'statusCode': 200,
            'body': json.dumps('Hello from Lambda!'),
            'db_username': db_username,
            'db_endpoint': db_endpoint
        }
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps('Internal server error FROM LAMBDA')
        }
