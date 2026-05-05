"""
公共数据模型 - 提供销售订单和采购单共享的枚举和工具函数
"""
from datetime import datetime
from enum import Enum


def parse_datetime(value):
    """解析日期时间，支持空字符串、ISO格式、常见日期格式"""
    if value == "" or value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        if value.strip() == "":
            return None
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            try:
                return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                try:
                    return datetime.strptime(value, "%Y-%m-%d")
                except ValueError:
                    return None
    return None


class SettleType(str, Enum):
    """结算方式枚举（销售订单和采购单共用）"""
    MONTHLY = "月结"
    CASH_ON_DELIVERY = "货到付款"
    PAYMENT_BEFORE_DELIVERY = "款到发货"


class ShippingMethod(str, Enum):
    """发货方式枚举（销售订单和采购单共用）"""
    DIRECT = "直运"
    LOGISTICS = "物流"
    SELF_PICKUP = "自提"
    DELIVERY = "送货"
