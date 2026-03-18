"""
Script para ver todas las licencias disponibles en Office 365
"""

import asyncio
from app.graph_api import get_graph_client
import aiohttp
from loguru import logger


async def check_licenses():
    """Ver todas las licencias disponibles"""
    client = get_graph_client()
    token = client.get_token()

    headers = {"Authorization": f"Bearer {token}"}

    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://graph.microsoft.com/v1.0/subscribedSkus",
            headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                skus = data.get('value', [])

                print("\n" + "="*80)
                print("LICENCIAS DISPONIBLES EN OFFICE 365")
                print("="*80)

                for sku in skus:
                    sku_id = sku.get('skuId', 'N/A')
                    sku_part_number = sku.get('skuPartNumber', 'N/A')
                    display_name = sku.get('skuPartNumber', 'N/A')
                    consumed = sku.get('consumedUnits', 0)

                    print(f"\nCódigo Técnico: {sku_part_number}")
                    print(f"SKU ID: {sku_id}")
                    print(f"Unidades consumidas: {consumed}")
                    print("-" * 80)
            else:
                print("Error obteniendo licencias")


if __name__ == "__main__":
    asyncio.run(check_licenses())
