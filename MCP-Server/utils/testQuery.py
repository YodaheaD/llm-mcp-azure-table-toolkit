# app/utils/testQuery.py
from .azure_table import get_table_client
import asyncio

async def test_count(filter_str=None):
    table_client = get_table_client("mainData")
    count = 0
    print(f"Counting entities with filter: {filter_str}")

    async for _ in table_client.query_entities(query_filter=filter_str):
        count += 1

    print(f"Total count: {count}")


async def test_query(filter_str=None, top=10, select=None):
    table_client = get_table_client("mainData")
    results = []
    count = 0
    print(f"Querying with filter: {filter_str}, top={top}, select={select}")

    async for entity in table_client.query_entities(
        query_filter=filter_str,
        select=[s.strip() for s in select.split(",")] if select else None
    ):
        if count >= top:
            break
        results.append(entity)
        count += 1

    print(f"Returned {len(results)} entities")
    for e in results:
        print(e)


if __name__ == "__main__":
    filter_example = "city eq 'Atlanta'"
    asyncio.run(test_count(filter_example))
    asyncio.run(test_query(filter_example, top=5, select="RowKey,Name,city"))
