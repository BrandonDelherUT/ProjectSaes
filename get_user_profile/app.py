import json
import os
import pymysql
import logging
from connection_bd import connect_to_db, close_connection

# Configurar logging
logging.basicConfig(level=logging.INFO)

def lambda_handler(event, context):
    headers = {
        'Access-Control-Allow-Origin': '*',  # Permite todas las fuentes
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Allow-Methods': 'OPTIONS,GET',  # Métodos permitidos
    }

    # Obtener el UUID del usuario desde el path
    user_id = event['pathParameters'].get('id')
    logging.info(f"User ID received: {user_id}")

    if user_id is None:
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({"message": "User ID is required."})
        }

    # Conectar a la base de datos
    connection = connect_to_db(
        host=os.environ['RDS_ENDPOINT'],
        user=os.environ['RDS_USERNAME'],
        password=os.environ['RDS_PASSWORD'],
        database=os.environ['RDS_DB_NAME']
    )

    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Cambiar el tipo de cursor a DictCursor para obtener resultados como un diccionario
            query = "SELECT * FROM user_profiles WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            user_profile = cursor.fetchone()

            if user_profile:
                return {
                    "statusCode": 200,
                    "headers": headers,
                    "body": json.dumps({
                        "user_id": user_profile['user_id'],
                        "first_name": user_profile.get('first_name', ''),
                        "last_name": user_profile.get('last_name', ''),
                        "phone": user_profile.get('phone', ''),
                        "address": user_profile.get('address', ''),
                    })
                }
            else:
                return {
                    "statusCode": 404,
                    "headers": headers,
                    "body": json.dumps({"message": "User profile not found."})
                }
    except pymysql.MySQLError as e:
        logging.error(f"MySQL error: {e}")
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"message": "Internal server error."})
        }
    finally:
        close_connection(connection)
