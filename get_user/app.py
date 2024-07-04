import os
import boto3
from botocore.exceptions import ClientError
import json
from typing import Dict
from connection_bd import connect_to_db, execute_query, close_connection
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def lambda_handler(event, __):
    # Obtener el ID del usuario desde el evento
    user_id = event['pathParameters'].get('id')

    if user_id is None:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "User ID is required."})
        }

    # Obtener credenciales de la base de datos desde AWS Secrets Manager
    secret_name = os.environ['RDS_SECRET_NAME']
    region_name = os.environ['AWS_REGION']
    try:
        secret = get_secret(secret_name, region_name)
    except ClientError as e:
        return {
            'statusCode': 400,
            'body': json.dumps(
                {'error': "An error occurred while processing the request get_secret"})
        }

    # Parámetros de conexión a la base de datos
    host = secret['host']
    user = secret['username']
    password = secret['password']
    database = os.environ['RDS_DB_NAME']

    # Consulta para seleccionar el usuario por ID
    query = f"SELECT * FROM users WHERE user_id = {user_id}"

    # Establecer conexión con la base de datos
    connection = connect_to_db(host, user, password, database)

    if connection:
        try:
            # Ejecutar la consulta
            results = execute_query(connection, query)
            # Cerrar la conexión
            close_connection(connection)

            if results:
                # Si se obtienen resultados, registrarlos
                logging.info("Results:")
                for row in results:
                    logging.info(row)

                # Devolver respuesta exitosa con los datos
                return {
                    "statusCode": 200,
                    "body": json.dumps({"data": results})
                }
            else:
                # Devolver respuesta vacía si no se encuentran resultados
                return {
                    "statusCode": 204,
                    "body": json.dumps({"message": "No results found."})
                }
        except Exception as e:
            # Registrar y devolver respuesta de error
            logging.error("Error executing query: %s", e)
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "An error occurred while processing the request."})
            }
    else:
        # Devolver respuesta de error si la conexión falla
        logging.error("Connection to the database failed.")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Failed to connect to the database."})
        }

def get_secret(secret_name: str, region_name: str) -> Dict[str, str]:
    """
    Retrieves the secret value from AWS Secrets Manager.

    Args:
        secret_name (str): The name or ARN of the secret to retrieve.
        region_name (str): The AWS region where the secret is stored.

    Returns:
        dict: The secret value retrieved from AWS Secrets Manager.
    """
    # Crear cliente de Secrets Manager
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        logging.error("Failed to retrieve secret: %s", e)
        raise e

    return json.loads(get_secret_value_response['SecretString'])
