"""
交互式 Python Shell
加载项目环境，可直接操作数据库

使用方法：
    cd /root/aierp/backend
    /root/aierp/venv/bin/python scripts/shell.py

示例：
    # 查询所有角色
    roles = run(role_service.find_many({}))
    print(roles)

    # 删除指定角色
    run(role_service.delete_one({"code": "purchaser_group"}))
"""
import sys
import os
import asyncio
import code

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db, close_db

_loop = None


def run(coro):
    """执行异步协程并返回结果"""
    return _loop.run_until_complete(coro)


async def main():
    global _loop
    _loop = asyncio.get_event_loop()

    print("正在初始化数据库连接...")
    await init_db()
    print("数据库连接成功！")
    print()
    print("可用的导入：")
    print("  from services.auth_service import role_service, permission_service, auth_service")
    print("  from services.customer_service import customer_service")
    print("  from services.product_service import product_service")
    print("  from services.sales_order_service import sales_order_service")
    print()
    print("示例：")
    print("  roles = run(role_service.find_many({}))")
    print("  run(role_service.delete_one({'code': 'purchaser_group'}))")
    print()
    print("输入 quit() 或 exit() 退出")
    print("-" * 50)

    try:
        import readline
        import rlcompleter
        readline.set_completer(rlcompleter.Completer(locals()).complete)
        readline.parse_and_bind("tab: complete")
    except ImportError:
        pass

    def cleanup():
        print("\n正在关闭数据库连接...")
        _loop.run_until_complete(close_db())
        print("已退出")

    try:
        code.interact(local=locals(), exitmsg="")
    except SystemExit:
        cleanup()
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    asyncio.run(main())
