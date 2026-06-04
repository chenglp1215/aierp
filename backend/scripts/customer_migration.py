"""客户管理 - 数据库迁移脚本"""
import asyncio
import sys
import os
from datetime import datetime
from urllib.parse import quote_plus

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tortoise import Tortoise
from config.settings import settings

encoded_password = quote_plus(settings.MYSQL_PASSWORD)
DB_URL = (
    f"mysql://{settings.MYSQL_USER}:{encoded_password}"
    f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
)


async def run_migration():
    await Tortoise.init(
        db_url=DB_URL,
        modules={"models": ["models_mysql.customer"]}
    )
    conn = Tortoise.get_connection("default")

    print(f"[{datetime.now()}] 开始客户模块数据库迁移...")

    # ===== 步骤1: Customer 表新增列 =====
    print(f"[{datetime.now()}] 步骤1: Customer 表新增列...")

    alter_columns = [
        "ADD COLUMN customer_status TINYINT NOT NULL DEFAULT 1 COMMENT '客户状态: 1=正常, 2=公共池'",
        "ADD COLUMN customer_name VARCHAR(200) NOT NULL DEFAULT '' COMMENT '客户名称'",
        "ADD COLUMN settlement_method TINYINT NOT NULL DEFAULT 1 COMMENT '结算方式: 1=月结, 2=现结, 3=预付'",
        "ADD COLUMN account_balance DECIMAL(18,2) NOT NULL DEFAULT 0.00 COMMENT '账户余额'",
        "ADD COLUMN debt_total DECIMAL(18,2) NOT NULL DEFAULT 0.00 COMMENT '欠款总额'",
        "ADD COLUMN last_order_time DATETIME NULL COMMENT '尾单时间'",
        "ADD COLUMN total_order_amount DECIMAL(18,2) NOT NULL DEFAULT 0.00 COMMENT '成单金额'",
        "ADD COLUMN member_account VARCHAR(100) NULL COMMENT '会员账号'",
        "ADD COLUMN is_overdue TINYINT NOT NULL DEFAULT 0 COMMENT '是否超账期: 0=否, 1=是'",
        "ADD COLUMN credit_limit DECIMAL(18,2) NOT NULL DEFAULT 0.00 COMMENT '信用额度'",
        "ADD COLUMN credit_days INT NOT NULL DEFAULT 0 COMMENT '账期天数'",
        "ADD COLUMN created_by INT NULL COMMENT '创建人ID'",
        "ADD COLUMN email VARCHAR(100) NULL COMMENT '邮箱地址'",
        "ADD COLUMN default_shipping_address_id INT NULL COMMENT '默认收货地址ID'",
        "ADD COLUMN default_invoice_info_id INT NULL COMMENT '默认开票信息ID'",
        "ADD COLUMN default_tax_rate DECIMAL(5,2) NULL COMMENT '默认税率'",
    ]

    for col_def in alter_columns:
        try:
            await conn.execute_query(f"ALTER TABLE customers {col_def}")
            print(f"  OK: {col_def[:60]}...")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print(f"  SKIP(已存在): {col_def[:50]}...")
            else:
                print(f"  ERROR: {col_def[:50]}... -> {e}")

    # ===== 步骤1b: 将 name 列数据复制到 customer_name =====
    print(f"[{datetime.now()}] 步骤1b: 映射 name -> customer_name...")
    try:
        result = await conn.execute_query(
            "UPDATE customers SET customer_name = name WHERE customer_name = '' OR customer_name IS NULL"
        )
        print(f"  OK: 更新了 {result[0]} 条记录")
    except Exception as e:
        print(f"  ERROR: {e}")

    # ===== 步骤2: 数据映射 - status -> customer_status =====
    print(f"[{datetime.now()}] 步骤2: 映射 status -> customer_status...")
    try:
        result = await conn.execute_query(
            "UPDATE customers SET customer_status = CASE WHEN status = 'normal' THEN 1 ELSE 2 END"
        )
        print(f"  OK: 更新了 {result[0]} 条记录")
    except Exception as e:
        print(f"  ERROR: {e}")

    # ===== 步骤3: 数据映射 - sales_user_id -> created_by =====
    print(f"[{datetime.now()}] 步骤3: 映射 sales_user_id -> created_by...")
    try:
        result = await conn.execute_query(
            "UPDATE customers SET created_by = sales_user_id WHERE created_by IS NULL"
        )
        print(f"  OK: 更新了 {result[0]} 条记录")
    except Exception as e:
        print(f"  ERROR: {e}")

    # ===== 步骤4: 新建 customer_research_group 表 =====
    print(f"[{datetime.now()}] 步骤4: 新建 customer_research_group 表...")
    try:
        await conn.execute_query("""
            CREATE TABLE IF NOT EXISTS customer_research_group (
                id INT AUTO_INCREMENT PRIMARY KEY,
                customer_id INT NOT NULL COMMENT '客户ID',
                research_group_name VARCHAR(100) NOT NULL COMMENT '课题组名称',
                research_leader VARCHAR(50) NULL COMMENT '课题组负责人',
                contact_phone VARCHAR(20) NULL COMMENT '联系电话',
                created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
                INDEX idx_customer_id (customer_id)
            ) COMMENT='客户课题组信息'
        """)
        print("  OK: customer_research_group 表创建成功")
    except Exception as e:
        print(f"  ERROR: {e}")

    # ===== 步骤5: 课题组数据迁移 =====
    print(f"[{datetime.now()}] 步骤5: 迁移课题组数据...")
    try:
        result = await conn.execute_query("""
            INSERT INTO customer_research_group (customer_id, research_group_name, research_leader, contact_phone)
            SELECT id, research_group, NULL, NULL
            FROM customers
            WHERE research_group IS NOT NULL AND research_group != ''
        """)
        print(f"  OK: 迁移了 {result[0]} 条课题组记录")
    except Exception as e:
        print(f"  ERROR: {e}")

    # ===== 步骤6: InvoiceInfo 表变更 =====
    print(f"[{datetime.now()}] 步骤6: InvoiceInfo 表变更...")
    try:
        await conn.execute_query(
            "ALTER TABLE invoice_infos ADD COLUMN address_phone VARCHAR(200) NULL COMMENT '地址、电话'"
        )
        print("  OK: 新增 address_phone 列")
    except Exception as e:
        if "Duplicate column name" in str(e):
            print("  SKIP(已存在): address_phone")
        else:
            print(f"  ERROR: {e}")

    try:
        await conn.execute_query("ALTER TABLE invoice_infos DROP COLUMN invoice_type")
        print("  OK: 删除 invoice_type 列")
    except Exception as e:
        if "check that column/key exists" in str(e) or "Can't DROP" in str(e):
            print("  SKIP(已删除): invoice_type")
        else:
            print(f"  ERROR: {e}")

    # ===== 步骤7: ShippingAddress 表字段重命名 =====
    print(f"[{datetime.now()}] 步骤7: ShippingAddress 表字段重命名...")
    try:
        await conn.execute_query(
            "ALTER TABLE shipping_addresses RENAME COLUMN recipient_name TO receiver"
        )
        print("  OK: recipient_name -> receiver")
    except Exception as e:
        if "check that column/key exists" in str(e):
            print("  SKIP(已重命名): recipient_name -> receiver")
        else:
            print(f"  ERROR: {e}")

    try:
        await conn.execute_query(
            "ALTER TABLE shipping_addresses RENAME COLUMN recipient_phone TO phone"
        )
        print("  OK: recipient_phone -> phone")
    except Exception as e:
        if "check that column/key exists" in str(e):
            print("  SKIP(已重命名): recipient_phone -> phone")
        else:
            print(f"  ERROR: {e}")

    # ===== 步骤8: Customer 表删除旧列 =====
    print(f"[{datetime.now()}] 步骤8: 删除 Customer 表旧列...")
    for col in ["status", "research_group", "contact_email", "name"]:
        try:
            await conn.execute_query(f"ALTER TABLE customers DROP COLUMN {col}")
            print(f"  OK: 删除 {col} 列")
        except Exception as e:
            if "check that column/key exists" in str(e) or "Can't DROP" in str(e):
                print(f"  SKIP(已删除): {col}")
            else:
                print(f"  ERROR: 删除 {col} -> {e}")

    print(f"[{datetime.now()}] 客户模块数据库迁移完成!")
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(run_migration())
