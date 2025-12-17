# app/utils/azure_table.py
from azure.data.tables.aio import TableClient
import os
import logging

logging.basicConfig(level=logging.INFO)

FIXED_TABLE_NAME = "mainData"

async def get_table_client() -> TableClient:
    """
    Returns an async TableClient for the fixed table.
    Use 'async with' when calling this function to ensure the client is properly closed.
    """
    connection_string = ""
    if not connection_string:
        raise ValueError("AZURE_STORAGE_CONNECTION_STRING not set")

    client = TableClient.from_connection_string(connection_string, FIXED_TABLE_NAME)
    return client
