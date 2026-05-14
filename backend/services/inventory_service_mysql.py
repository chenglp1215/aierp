"""
仓库库存管理模块服务层 - MySQL 版本
"""
import random
import string
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from tortoise.expressions import Q

from models_mysql.warehouse import Warehouse, Stock, InboundBatch, OutboundBatch

logger = logging.getLogger(__name__)


def _generate_code(prefix: str) -> str:
    """生成编码"""
    date_str = datetime.now().strftime("%Y%m%d")
    random_str = ''.join(random.choices(string.digits, k=6))
    return f"{prefix}{date_str}{random_str}"


class WarehouseService:
    """仓库服务"""

    async def create_warehouse(self, warehouse_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建仓库"""
        name = warehouse_data.get("name")
        if not name:
            raise ValueError("仓库名称不能为空")

        address = warehouse_data.get("address")
        if not address:
            raise ValueError("仓库地址不能为空")

        # 生成仓库编码
        warehouse_code = warehouse_data.get("warehouse_code") or _generate_code("WH")

        # 检查编码唯一性
        existing = await Warehouse.filter(warehouse_code=warehouse_code).first()
        if existing:
            warehouse_code = _generate_code("WH")

        warehouse = await Warehouse.create(
            warehouse_code=warehouse_code,
            name=name,
            address=address,
            manager_id=warehouse_data.get("manager_id"),
            manager_name=warehouse_data.get("manager_name"),
            status=warehouse_data.get("status", "active"),
            description=warehouse_data.get("description"),
        )
        return warehouse.to_dict()

    async def update_warehouse(self, warehouse_id: int, warehouse_data: Dict[str, Any]) -> bool:
        """更新仓库"""
        warehouse = await Warehouse.get_or_none(id=warehouse_id)
        if not warehouse:
            raise ValueError("仓库不存在")

        if "name" in warehouse_data:
            warehouse.name = warehouse_data["name"]
        if "address" in warehouse_data:
            warehouse.address = warehouse_data["address"]
        if "manager_id" in warehouse_data:
            warehouse.manager_id = warehouse_data["manager_id"]
        if "manager_name" in warehouse_data:
            warehouse.manager_name = warehouse_data["manager_name"]
        if "status" in warehouse_data:
            warehouse.status = warehouse_data["status"]
        if "description" in warehouse_data:
            warehouse.description = warehouse_data["description"]

        await warehouse.save()
        return True

    async def get_warehouse_by_id(self, warehouse_id: int, is_formatted: bool = False) -> Optional[Dict[str, Any]]:
        """根据ID获取仓库"""
        warehouse = await Warehouse.get_or_none(id=warehouse_id)
        if not warehouse:
            return None
        return warehouse.to_dict()

    async def get_warehouse_by_code(self, warehouse_code: str, is_formatted: bool = False) -> Optional[Dict[str, Any]]:
        """根据编码获取仓库"""
        warehouse = await Warehouse.filter(warehouse_code=warehouse_code).first()
        if not warehouse:
            return None
        return warehouse.to_dict()

    async def get_warehouse_by_ids(self, warehouse_ids: List[int], is_formatted: bool = False) -> List[Dict[str, Any]]:
        """根据ID列表获取仓库"""
        warehouses = await Warehouse.filter(id__in=warehouse_ids).all()
        return [w.to_dict() for w in warehouses]

    async def list_warehouses(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
        is_formatted: bool = True
    ) -> tuple[List[Dict[str, Any]], int]:
        """获取仓库列表"""
        query = Warehouse.all()

        if status:
            query = query.filter(status=status)
        if keyword:
            query = query.filter(
                Q(warehouse_code__contains=keyword) | Q(name__contains=keyword)
            )

        total = await query.count()
        warehouses = await query.offset((page - 1) * page_size).limit(page_size)

        return [w.to_dict() for w in warehouses], total


class StockService:
    """库存服务"""

    def _calculate_status(self, quantity: float, min_stock: float, max_stock: float) -> str:
        """计算库存状态"""
        if quantity <= 0:
            return "out_of_stock"
        elif quantity <= min_stock:
            return "low_stock"
        elif max_stock > 0 and quantity > max_stock:
            return "overstock"
        return "normal"

    async def create_stock(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建库存"""
        warehouse_id = stock_data.get("warehouse_id")
        product_id = stock_data.get("product_id")
        spec_id = stock_data.get("spec_id")

        if not warehouse_id or not product_id or not spec_id:
            raise ValueError("仓库ID、商品ID和规格ID不能为空")

        quantity = stock_data.get("quantity", 0)
        min_stock = stock_data.get("min_stock", 0)
        max_stock = stock_data.get("max_stock", 0)

        status = self._calculate_status(quantity, min_stock, max_stock)

        stock = await Stock.create(
            warehouse_id=int(warehouse_id),
            product_id=int(product_id),
            product_code=stock_data.get("product_code", ""),
            product_name=stock_data.get("product_name", ""),
            spec_id=int(spec_id),
            spec_code=stock_data.get("spec_code", ""),
            quantity=quantity,
            min_stock=min_stock,
            max_stock=max_stock,
            status=status,
        )
        return stock.to_dict()

    async def update_stock(self, stock_id: int, stock_data: Dict[str, Any]) -> bool:
        """更新库存（手动盘库）"""
        stock = await Stock.get_or_none(id=stock_id)
        if not stock:
            raise ValueError("库存不存在")

        if "quantity" in stock_data:
            stock.quantity = float(stock_data["quantity"])
        if "min_stock" in stock_data:
            stock.min_stock = float(stock_data["min_stock"])
        if "max_stock" in stock_data:
            stock.max_stock = float(stock_data["max_stock"])

        # 重新计算状态
        stock.status = self._calculate_status(stock.quantity, stock.min_stock, stock.max_stock)

        await stock.save()
        return True

    async def get_stock_by_id(self, stock_id: int, is_formatted: bool = True) -> Optional[Dict[str, Any]]:
        """根据ID获取库存"""
        stock = await Stock.get_or_none(id=stock_id)
        if not stock:
            return None

        result = stock.to_dict()
        if is_formatted:
            result = await self._format_stock(result)
        return result

    async def _format_stock(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化库存数据，添加关联信息"""
        from services.product_service_mysql import product_service, product_spec_service

        product_id = stock_data.get("product_id")
        spec_id = stock_data.get("spec_id")
        warehouse_id = stock_data.get("warehouse_id")

        # 获取商品信息
        try:
            product = await product_service.get_product_by_id(int(product_id)) if product_id else None
            stock_data["product_info"] = product or {}
        except Exception:
            stock_data["product_info"] = {}

        # 获取规格信息
        try:
            spec = await product_spec_service.get_spec_by_id(int(spec_id)) if spec_id else None
            stock_data["spec_info"] = spec or {}
        except Exception:
            stock_data["spec_info"] = {}

        # 获取仓库信息
        try:
            warehouse = await warehouse_service.get_warehouse_by_id(int(warehouse_id)) if warehouse_id else None
            stock_data["warehouse_info"] = warehouse or {}
        except Exception:
            stock_data["warehouse_info"] = {}

        return stock_data

    async def list_stocks(
        self,
        page: int = 1,
        page_size: int = 20,
        warehouse_id: Optional[int] = None,
        product_id: Optional[int] = None,
        spec_id: Optional[int] = None,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
        is_formatted: bool = True
    ) -> tuple[List[Dict[str, Any]], int]:
        """获取库存列表"""
        query = Stock.all()

        if warehouse_id:
            query = query.filter(warehouse_id=int(warehouse_id))
        if product_id:
            query = query.filter(product_id=int(product_id))
        if spec_id:
            query = query.filter(spec_id=int(spec_id))
        if status:
            query = query.filter(status=status)
        if keyword:
            query = query.filter(
                Q(product_code__contains=keyword) |
                Q(product_name__contains=keyword) |
                Q(spec_code__contains=keyword)
            )

        total = await query.count()
        stocks = await query.offset((page - 1) * page_size).limit(page_size)

        result = [s.to_dict() for s in stocks]
        if is_formatted:
            result = await self._format_stock_list(result)
        return result, total

    async def _format_stock_list(self, stock_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量格式化库存列表"""
        from services.product_service_mysql import product_service, product_spec_service

        # 收集所有ID
        product_ids = list(set(s["product_id"] for s in stock_list if s.get("product_id")))
        spec_ids = list(set(s["spec_id"] for s in stock_list if s.get("spec_id")))
        warehouse_ids = list(set(s["warehouse_id"] for s in stock_list if s.get("warehouse_id")))

        # 批量获取关联信息
        products = {}
        if product_ids:
            try:
                product_list = await product_service.get_product_by_ids(product_ids)
                products = {p["id"]: p for p in product_list}
            except Exception:
                pass

        specs = {}
        if spec_ids:
            try:
                spec_list = await product_spec_service.get_spec_by_ids(spec_ids)
                specs = {s["id"]: s for s in spec_list}
            except Exception:
                pass

        warehouses = {}
        if warehouse_ids:
            try:
                warehouse_list = await warehouse_service.get_warehouse_by_ids(warehouse_ids)
                warehouses = {w["id"]: w for w in warehouse_list}
            except Exception:
                pass

        # 组装结果
        for stock in stock_list:
            stock["product_info"] = products.get(stock.get("product_id"), {})
            stock["spec_info"] = specs.get(stock.get("spec_id"), {})
            stock["warehouse_info"] = warehouses.get(stock.get("warehouse_id"), {})

        return stock_list

    async def get_or_create_stock_by_inbound(self, inbound: Dict[str, Any]) -> tuple[Dict[str, Any], bool]:
        """根据入库信息获取或创建库存"""
        product_id = int(inbound["product_id"])
        spec_id = int(inbound["spec_id"])
        warehouse_id = int(inbound["warehouse_id"])

        stock = await Stock.filter(
            product_id=product_id,
            spec_id=spec_id,
            warehouse_id=warehouse_id
        ).first()

        if not stock:
            stock_data = {
                "product_code": inbound.get("product_code", ""),
                "product_name": inbound.get("product_name", ""),
                "spec_code": inbound.get("spec_code", ""),
                "product_id": product_id,
                "spec_id": spec_id,
                "warehouse_id": warehouse_id,
                "quantity": inbound.get("quantity", 0),
                "min_stock": 0,
                "max_stock": 0,
            }
            new_stock = await self.create_stock(stock_data)
            return new_stock, False

        result = stock.to_dict()
        result = await self._format_stock(result)
        return result, True

    async def get_stock_status_by_spec_ids(self, spec_ids: List[int]) -> Dict[str, List[Dict[str, Any]]]:
        """获取指定规格的库存状态"""
        if not spec_ids:
            return {}

        stocks = await Stock.filter(spec_id__in=spec_ids).all()
        result: Dict[str, List[Dict[str, Any]]] = {}

        # 获取仓库信息
        warehouse_ids = list(set(s.warehouse_id for s in stocks))
        warehouses = {w["id"]: w for w in await warehouse_service.get_warehouse_by_ids(warehouse_ids)}

        for stock in stocks:
            spec_id = stock.spec_id
            warehouse_id = stock.warehouse_id
            warehouse_name = warehouses.get(warehouse_id, {}).get("name", "")

            if spec_id not in result:
                result[str(spec_id)] = []

            result[str(spec_id)].append({
                "warehouse_id": warehouse_id,
                "warehouse_name": warehouse_name,
                "quantity": stock.quantity
            })

        return result


class InboundBatchService:
    """入库批次服务"""

    async def create_inbound(self, inbound_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建入库批次"""
        warehouse_id = inbound_data.get("warehouse_id")
        product_id = inbound_data.get("product_id")
        spec_id = inbound_data.get("spec_id")
        quantity = inbound_data.get("quantity")

        if not warehouse_id or not product_id or not spec_id:
            raise ValueError("仓库ID、商品ID和规格ID不能为空")
        if not quantity or float(quantity) <= 0:
            raise ValueError("入库数量必须大于0")

        # 获取或创建库存
        stock, is_existing = await stock_service.get_or_create_stock_by_inbound(inbound_data)

        # 如果库存已存在，增加库存数量
        if is_existing:
            stock_obj = await Stock.get_or_none(id=stock["id"])
            if stock_obj:
                stock_obj.quantity += float(quantity)
                stock_obj.status = stock_service._calculate_status(
                    stock_obj.quantity, stock_obj.min_stock, stock_obj.max_stock
                )
                await stock_obj.save()

        # 创建入库批次记录
        inbound = await InboundBatch.create(
            warehouse_id=int(warehouse_id),
            product_id=int(product_id),
            product_code=inbound_data.get("product_code", ""),
            product_name=inbound_data.get("product_name", ""),
            spec_id=int(spec_id),
            spec_code=inbound_data.get("spec_code", ""),
            stock_id=stock["id"],
            quantity=float(quantity),
            user_id=int(inbound_data.get("user_id", 0)),
            user_name=inbound_data.get("user_name", ""),
            remarks=inbound_data.get("remarks"),
        )
        return inbound.to_dict()

    async def update_inbound(self, inbound_id: int, inbound_data: Dict[str, Any]) -> bool:
        """更新入库批次"""
        inbound = await InboundBatch.get_or_none(id=inbound_id)
        if not inbound:
            raise ValueError("入库批次不存在")

        if "remarks" in inbound_data:
            inbound.remarks = inbound_data["remarks"]

        await inbound.save()
        return True

    async def get_inbounds_by_stock_id(
        self, stock_id: Optional[int], page: int = 1, page_size: int = 20, is_formatted: bool = True
    ) -> tuple[List[Dict[str, Any]], int]:
        """根据库存ID获取入库批次列表"""
        query = InboundBatch.all()

        if stock_id:
            query = query.filter(stock_id=int(stock_id))

        total = await query.count()
        batches = await query.offset((page - 1) * page_size).limit(page_size)

        return [b.to_dict() for b in batches], total

    async def get_by_id(self, inbound_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取入库批次"""
        inbound = await InboundBatch.get_or_none(id=inbound_id)
        if not inbound:
            return None
        return inbound.to_dict()


class OutboundBatchService:
    """出库批次服务"""

    async def create_outbound(self, outbound_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建出库批次"""
        stock_id = outbound_data.get("stock_id")
        quantity = outbound_data.get("quantity")

        if not stock_id:
            raise ValueError("库存ID不能为空")
        if not quantity or float(quantity) <= 0:
            raise ValueError("出库数量必须大于0")

        # 获取库存
        stock = await Stock.get_or_none(id=int(stock_id))
        if not stock:
            raise ValueError(f"库存记录不存在: {stock_id}")

        # 检查库存是否充足
        if stock.quantity < float(quantity):
            raise ValueError(f"库存不足，当前库存: {stock.quantity}，出库数量: {quantity}")

        # 减少库存数量
        stock.quantity -= float(quantity)
        stock.status = stock_service._calculate_status(
            stock.quantity, stock.min_stock, stock.max_stock
        )
        await stock.save()

        # 创建出库批次记录
        outbound = await OutboundBatch.create(
            warehouse_id=int(outbound_data.get("warehouse_id", stock.warehouse_id)),
            product_id=int(outbound_data.get("product_id", stock.product_id)),
            product_code=outbound_data.get("product_code", stock.product_code),
            product_name=outbound_data.get("product_name", stock.product_name),
            spec_id=int(outbound_data.get("spec_id", stock.spec_id)),
            spec_code=outbound_data.get("spec_code", stock.spec_code),
            stock_id=int(stock_id),
            quantity=float(quantity),
            user_id=int(outbound_data.get("user_id", 0)),
            user_name=outbound_data.get("user_name", ""),
            remarks=outbound_data.get("remarks"),
        )
        return outbound.to_dict()

    async def update_outbound(self, outbound_id: int, outbound_data: Dict[str, Any]) -> bool:
        """更新出库批次"""
        outbound = await OutboundBatch.get_or_none(id=outbound_id)
        if not outbound:
            raise ValueError("出库批次不存在")

        if "remarks" in outbound_data:
            outbound.remarks = outbound_data["remarks"]

        await outbound.save()
        return True

    async def get_outbounds_by_stock_id(
        self, stock_id: Optional[int], page: int = 1, page_size: int = 20, is_formatted: bool = True
    ) -> tuple[List[Dict[str, Any]], int]:
        """根据库存ID获取出库批次列表"""
        query = OutboundBatch.all()

        if stock_id:
            query = query.filter(stock_id=int(stock_id))

        total = await query.count()
        batches = await query.offset((page - 1) * page_size).limit(page_size)

        return [b.to_dict() for b in batches], total

    async def get_by_id(self, outbound_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取出库批次"""
        outbound = await OutboundBatch.get_or_none(id=outbound_id)
        if not outbound:
            return None
        return outbound.to_dict()


# 创建服务实例
warehouse_service = WarehouseService()
stock_service = StockService()
inbound_batch_service = InboundBatchService()
outbound_batch_service = OutboundBatchService()