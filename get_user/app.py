import os
import boto3
from botocore.exceptions import ClientError
import json
import logging
from connection_bd import connect_to_db, execute_query, close_connection

# Configurar logging
logging.basicConfig(level=logging.INFO)

def lambda_handler(event, context):
    logging.info("Lambda function 'get_user' has started")
    logging.info(f"Event received: {json.dumps(event)}")

    # Obtener el ID del usuario desde el evento
    user_id = event['pathParameters'].get('id')
    logging.info(f"User ID received: {user_id}")

    # Verificar que user_id sea un número entero
    if not user_id.isdigit():
        logging.error("User ID is not a valid integer")
        return {
            "statusCode": 400,
            "headers": {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization'
            },
            "body": json.dumps({"message": "User ID must be a valid integer."})
        }

    # Obtener credenciales de la base de datos desde AWS Secrets Manager
    secret_name = os.environ['RDS_SECRET_NAME']
    region_name = os.environ['REGION_NAME']

    try:
        logging.info(f"Retrieving secret '{secret_name}' from Secrets Manager")
        secret = get_secret(secret_name, region_name)
        logging.info("Secret retrieved successfully")
    except ClientError as e:
        logging.error(f"Failed to retrieve secret: {e}")
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization'
            },
            'body': json.dumps(
                {'error': "An error occurred while retrieving database credentials"})
        }

    # Parámetros de conexión a la base de datos
    host = secret['host']
    user = secret['username']
    password = secret['password']
    database = os.environ['RDS_DB_NAME']
    logging.info(f"Database connection parameters set: host={host}, database={database}")

    # Consulta para seleccionar el usuario por ID (usando parámetros)
    query = "SELECT * FROM users WHERE user_id = %s"
    logging.info(f"SQL query prepared")

    # Establecer conexión con la base de datos
    connection = None
    try:
        connection = connect_to_db(host, user, password, database)
        logging.info("Database connection established successfully")

        # Ejecutar la consulta
        logging.info(f"Executing query with user_id: {user_id}")
        results = execute_query(connection, query, (user_id,))
        logging.info(f"Query executed successfully, results: {results}")

        if results:
            logging.info("Returning successful response with user data")
            return {
                "statusCode": 200,
                "headers": {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization'
                },
                "body": json.dumps({"data": results})
            }
        else:
            logging.info("No results found for the provided User ID")
            return {
                "statusCode": 404,
                "headers": {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization'
                },
                "body": json.dumps({"message": "No results found."})
            }
    except Exception as e:
        logging.error(f"Error executing query or connecting to the database: {e}")
        return {
            "statusCode": 500,
            "headers": {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization'
            },
            "body": json.dumps({"error": "An error occurred while processing the request."})
        }
    finally:
        if connection:
            close_connection(connection)
            logging.info("Database connection closed successfully")

def get_secret(secret_name: str, region_name: str) -> dict:
    """
    Retrieves the secret value from AWS Secrets Manager.

    Args:
        secret_name (str): The name or ARN of the secret to retrieve.
        region_name (str): The AWS region where the secret is stored.

    Returns:
        dict: The secret value retrieved from AWS Secrets Manager.
    """
    logging.info(f"Creating a Secrets Manager client for region: {region_name}")

    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        logging.info(f"Requesting secret '{secret_name}' from Secrets Manager")
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        logging.info("Secret retrieved successfully from Secrets Manager")
    except ClientError as e:
        logging.error(f"Failed to retrieve secret: {e}")
        raise e

    return json.loads(get_secret_value_response['SecretString'])
