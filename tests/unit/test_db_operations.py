import pytest
from unittest.mock import patch, MagicMock
from create_user.connection_bd import connect_to_db, execute_query, close_connection

@patch('create_user.connection_bd.pymysql.connect')
def test_connect_to_db_success(mock_connect):
    mock_connection = MagicMock()
    mock_connect.return_value = mock_connection

    connection = connect_to_db('localhost', 'user', 'password', 'database')

    mock_connect.assert_called_once_with(
        host='localhost',
        user='user',
        password='password',
        database='database'
    )
    assert connection == mock_connection

@patch('create_user.connection_bd.pymysql.connect')
def test_connect_to_db_failure(mock_connect):
    mock_connect.side_effect = Exception("Connection failed")

    with pytest.raises(Exception, match="Connection failed"):
        connect_to_db('localhost', 'user', 'password', 'database')

@patch('create_user.connection_bd.pymysql.connect')
def test_execute_query_success(mock_connect):
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [('result1',), ('result2',)]
    mock_connect.return_value = mock_connection

    query = "SELECT * FROM test_table"
    result = execute_query(mock_connection, query)

    mock_cursor.execute.assert_called_once_with(query)
    mock_connection.commit.assert_called_once()
    assert result == [('result1',), ('result2',)]

@patch('create_user.connection_bd.pymysql.connect')
def test_execute_query_failure(mock_connect):
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Query failed")
    mock_connect.return_value = mock_connection

    with pytest.raises(Exception, match="Query failed"):
        execute_query(mock_connection, "SELECT * FROM test_table")

@patch('create_user.connection_bd.pymysql.connect')
def test_close_connection_success(mock_connect):
    mock_connection = MagicMock()
    close_connection(mock_connection)
    mock_connection.close.assert_called_once()

@patch('create_user.connection_bd.pymysql.connect')
def test_close_connection_failure(mock_connect):
    mock_connection = MagicMock()
    mock_connection.close.side_effect = Exception("Close failed")

    with pytest.raises(Exception, match="Close failed"):
        close_connection(mock_connection)
