"""
迁移脚本：添加采购单物流字段
"""
import asyncio
import aiomysql
import os
from dotenv import load_dotenv

load_dotenv()


async def migrate():
    conn = await aiomysql.connect(
        host=os.getenv('MYSQL_HOST', '132.232.212.151'),
        port=int(os.getenv('MYSQL_PORT', 58901)),
        user=os.getenv('MYSQL_USER', 'admin'),
        password=os.getenv('MYSQL_PASSWORD', 'Chenglp1215!@#'),
        db=os.getenv('MYSQL_DATABASE', 'erp_test')
    )

    async with conn.cursor() as cursor:
        # 检查表结构
        await cursor.execute('DESCRIBE purchase_orders')
        columns = await cursor.fetchall()
        existing_cols = [col[0] for col in columns]
        print('现有字段:', existing_cols)

        # 需要添加的字段
        new_fields = [
            ('logistics_company', "VARCHAR(100) NULL COMMENT '物流公司'"),
            ('logistics_no', "VARCHAR(100) NULL COMMENT '物流单号'"),
            ('source_purchase_order_id', "VARCHAR(100) NULL COMMENT '采购源订单ID'"),
        ]

        for field_name, field_def in new_fields:
            if field_name not in existing_cols:
                sql = f'ALTER TABLE purchase_orders ADD COLUMN {field_name} {field_def}'
                print(f'执行: {sql}')
                await cursor.execute(sql)
                print(f'已添加字段: {field_name}')
            else:
                print(f'字段已存在: {field_name}')

        await conn.commit()

    conn.close()
    print('迁移完成')


if __name__ == '__main__':
    asyncio.run(migrate())
