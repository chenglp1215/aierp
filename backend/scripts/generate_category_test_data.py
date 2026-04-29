import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


MONGODB_URL = "mongodb://10.5.5.66:20001"
MONGODB_DB_NAME = "oai_erp"


async def generate_category_test_data():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_DB_NAME]
    collection = db["categories"]

    await collection.delete_many({})
    print("已清空分类数据")

    categories = [
        {
            "name": "电子产品",
            "parent_id": None,
            "tax_code": "TAX001",
            "sort_order": 1,
            "is_shop_display": True,
            "level": 1,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "name": "食品饮料",
            "parent_id": None,
            "tax_code": "TAX002",
            "sort_order": 2,
            "is_shop_display": True,
            "level": 1,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "name": "服装鞋帽",
            "parent_id": None,
            "tax_code": "TAX003",
            "sort_order": 3,
            "is_shop_display": True,
            "level": 1,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "name": "家用电器",
            "parent_id": None,
            "tax_code": "TAX004",
            "sort_order": 4,
            "is_shop_display": True,
            "level": 1,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "name": "办公用品",
            "parent_id": None,
            "tax_code": "TAX005",
            "sort_order": 5,
            "is_shop_display": True,
            "level": 1,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "name": "医学化学试剂",
            "parent_id": None,
            "tax_code": "TAX006",
            "sort_order": 6,
            "is_shop_display": True,
            "level": 1,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
    ]

    result = await collection.insert_many(categories)
    level1_ids = [str(id) for id in result.inserted_ids]
    print(f"插入 {len(level1_ids)} 个一级分类")

    level2_categories = []
    level2_names = {
        level1_ids[0]: ["手机通讯", "电脑整机", "数码配件", "智能设备"],
        level1_ids[1]: ["休闲零食", "粮油调味", "饮料冲调", "生鲜水果"],
        level1_ids[2]: ["男装", "女装", "童装", "鞋靴"],
        level1_ids[3]: ["厨房电器", "生活电器", "个护电器", "空调冰箱"],
        level1_ids[4]: ["文具", "纸张本册", "办公设备", "办公家具"],
        level1_ids[5]: ["化学试剂", "生物试剂", "医学诊断试剂", "实验耗材", "标准品对照品"]
    }

    for pid, names in level2_names.items():
        for i, name in enumerate(names):
            level2_categories.append({
                "name": name,
                "parent_id": pid,
                "tax_code": f"TAX{pid[-4:]}{i+1}",
                "sort_order": i + 1,
                "is_shop_display": True,
                "level": 2,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            })

    result = await collection.insert_many(level2_categories)
    level2_ids = [str(id) for id in result.inserted_ids]
    print(f"插入 {len(level2_ids)} 个二级分类")

    level3_categories = []
    level3_names = {
        level2_ids[0]: ["智能手机", "功能手机", "对讲机"],
        level2_ids[1]: ["笔记本电脑", "台式机", "平板电脑", "服务器"],
        level2_ids[2]: ["鼠标键盘", "散热器", "移动硬盘", "U盘"],
        level2_ids[3]: ["智能手表", "智能手环", "智能眼镜"],
        level2_ids[4]: ["薯片零食", "巧克力零食", "坚果零食"],
        level2_ids[5]: ["酱油", "醋", "盐", "糖"],
        level2_ids[6]: ["咖啡", "奶茶", "果汁", "碳酸饮料"],
        level2_ids[7]: ["苹果", "香蕉", "橙子", "葡萄"],
        level2_ids[8]: ["T恤", "衬衫", "西装", "外套"],
        level2_ids[9]: ["连衣裙", "半身裙", "上衣", "外套"],
        level2_ids[10]: ["童鞋", "儿童服装", "玩具"],
        level2_ids[11]: ["运动鞋", "皮鞋", "拖鞋", "凉鞋"],
        level2_ids[12]: ["电饭煲", "电磁炉", "微波炉", "豆浆机"],
        level2_ids[13]: ["电风扇", "加湿器", "除湿器", "空气净化器"],
        level2_ids[14]: ["电动牙刷", "吹风机", "剃须刀", "按摩仪"],
        level2_ids[15]: ["空调", "冰箱", "冷柜", "酒柜"],
        level2_ids[16]: ["中性笔", "圆珠笔", "铅笔", "马克笔"],
        level2_ids[17]: ["复印纸", "打印纸", "记事本", "文件夹"],
        level2_ids[18]: ["打印机", "复印机", "扫描仪", "投影仪"],
        level2_ids[19]: ["办公桌", "办公椅", "文件柜", "会议桌"],
        level2_ids[20]: ["有机试剂", "无机试剂", "分析试剂", "合成试剂", "溶剂"],
        level2_ids[21]: ["细胞培养试剂", "分子生物学试剂", "免疫学试剂", "病理学试剂", "微生物学试剂"],
        level2_ids[22]: ["生化诊断试剂", "免疫诊断试剂", "分子诊断试剂", "血液学试剂", "尿液分析试剂"],
        level2_ids[23]: ["实验室塑料耗材", "实验室玻璃耗材", "过滤耗材", "采样耗材", "防护耗材"],
        level2_ids[24]: ["标准品", "对照品", "参考物质", "校准品", "质控品"]
    }

    for pid, names in level3_names.items():
        for i, name in enumerate(names):
            level3_categories.append({
                "name": name,
                "parent_id": pid,
                "tax_code": f"TAX{pid[-4:]}{i+1}",
                "sort_order": i + 1,
                "is_shop_display": True,
                "level": 3,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            })

    result = await collection.insert_many(level3_categories)
    print(f"插入 {len(result.inserted_ids)} 个三级分类")

    total = await collection.count_documents({})
    print(f"\n分类数据生成完成，总计 {total} 条分类记录")

    client.close()


if __name__ == "__main__":
    asyncio.run(generate_category_test_data())
