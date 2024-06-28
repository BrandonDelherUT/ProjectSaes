import json
import os
import boto3
import pymysql

def get_db_credentials():
    client = boto3.client('secretsmanager')
    secret_name = os.environ['RDS_SECRET_NAME']
    secret_value = client.get_secret_value(SecretId=secret_name)
    return json.loads(secret_value['SecretString'])

def lambda_handler(event, context):
    db_credentials = get_db_credentials()
    connection = pymysql.connect(
        host=os.environ['RDS_ENDPOINT'],
        user=db_credentials['username'],
        password=db_credentials['password'],
        db=os.environ['RDS_DB_NAME']
    )
    try:
        user_id = event['pathParameters']['id']

        with connection.cursor() as cursor:
            sql = "DELETE FROM users WHERE user_id = %s"
            cursor.execute(sql, (user_id,))
            connection.commit()

        return {
            'statusCode': 200,
            'body': json.dumps('User deleted successfully')
        }
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps('Internal server error')
        }
    finally:
        connection.close()
