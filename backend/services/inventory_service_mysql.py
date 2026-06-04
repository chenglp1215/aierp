"""
仓库库存管理模块服务层 - MySQL 版本
"""
import random
import string
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from tortoise.expressions import Q

from models_mysql.warehouse import Warehouse, Stock, InboundBatch, OutboundBatch, WarehouseLocation
from models_mysql.product import ProductSpec

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
            val = warehouse_data["manager_id"]
            warehouse.manager_id = None if val == "" or val is None else val
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

    async def _calculate_batch_total(self, warehouse_id: int, spec_id: int) -> float:
        """计算指定库存的批次 current_quantity 之和"""
        batches = await InboundBatch.filter(
            warehouse_id=warehouse_id,
            spec_id=spec_id
        ).only("current_quantity").all()
        return sum(float(b.current_quantity) for b in batches)

    async def _calculate_locked_quantity(self, warehouse_id: int, spec_id: int) -> float:
        """计算指定仓库+规格的锁定量"""
        from models_mysql.pending_outbound import PendingOutboundOrder, PendingOutboundStatus
        from models_mysql.warehouse import OutboundBatch
        from tortoise.functions import Sum

        pendings = await PendingOutboundOrder.filter(
            warehouse_id=warehouse_id,
            spec_id=spec_id,
            status=PendingOutboundStatus.PENDING
        ).all()

        if not pendings:
            return 0

        pending_ids = [p.id for p in pendings]
        locked_map = dict()
        rows = await OutboundBatch.filter(
            pending_outbound_id__in=pending_ids
        ).group_by("pending_outbound_id").annotate(
            total=Sum("quantity")
        ).values_list("pending_outbound_id", "total")
        for pid, total in rows:
            locked_map[pid] = int(total) if total else 0

        locked_total = 0
        for p in pendings:
            out_qty = locked_map.get(p.id, 0)
            locked_total += (p.locked_qty - out_qty)
        return locked_total

    async def _batch_calculate_locked_quantities(
        self, stock_list: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """批量计算锁定量，避免 N+1 查询"""
        if not stock_list:
            return {}

        from models_mysql.pending_outbound import PendingOutboundOrder, PendingOutboundStatus
        from models_mysql.warehouse import OutboundBatch
        from tortoise.functions import Sum

        # 收集所有 (warehouse_id, spec_id) 组合
        pairs = set()
        for s in stock_list:
            wid = s.get("warehouse_id")
            sid = s.get("spec_id")
            if wid and sid:
                pairs.add((int(wid), int(sid)))

        if not pairs:
            return {}

        # 批量查询所有相关出库单（仅 pending 状态）
        warehouse_ids = list(set(p[0] for p in pairs))
        spec_ids = list(set(p[1] for p in pairs))

        pendings = await PendingOutboundOrder.filter(
            warehouse_id__in=warehouse_ids,
            spec_id__in=spec_ids,
            status=PendingOutboundStatus.PENDING
        ).all()

        if not pendings:
            return {}

        pending_ids = [p.id for p in pendings]

        # 批量查询出库批次的 out_qty
        out_qty_map: Dict[int, int] = {}
        rows = await OutboundBatch.filter(
            pending_outbound_id__in=pending_ids
        ).group_by("pending_outbound_id").annotate(
            total=Sum("quantity")
        ).values_list("pending_outbound_id", "total")
        for pid, total in rows:
            out_qty_map[pid] = int(total) if total else 0

        # 按 (warehouse_id, spec_id) 分组求和
        locked_map: Dict[str, float] = {}
        for p in pendings:
            key = f"{p.warehouse_id}_{p.spec_id}"
            out_qty = out_qty_map.get(p.id, 0)
            locked_map[key] = locked_map.get(key, 0) + (p.locked_qty - out_qty)

        return locked_map

    async def _batch_calculate_batch_totals(self, stock_list: list) -> dict:
        """批量计算各库存的批次 current_quantity 之和"""
        if not stock_list:
            return {}

        # 收集所有 (warehouse_id, spec_id) 组合
        pairs = set()
        for s in stock_list:
            wid = s.get("warehouse_id")
            sid = s.get("spec_id")
            if wid and sid:
                pairs.add((wid, sid))

        if not pairs:
            return {}

        # 批量查询所有相关入库批次的 current_quantity
        batch_map = {}
        for warehouse_id, spec_id in pairs:
            batches = await InboundBatch.filter(
                warehouse_id=warehouse_id,
                spec_id=spec_id
            ).only("current_quantity").all()
            total = sum(float(b.current_quantity) for b in batches)
            batch_map[f"{warehouse_id}_{spec_id}"] = total

        return batch_map

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
        """更新库存信息"""
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
        # 当前库存 = 批次 current_quantity 之和
        batch_total = await self._calculate_batch_total(stock.warehouse_id, stock.spec_id)
        result["quantity"] = batch_total
        # 计算锁定量
        locked_qty = await self._calculate_locked_quantity(stock.warehouse_id, stock.spec_id)
        result["locked_quantity"] = locked_qty
        result["available_quantity"] = batch_total - locked_qty
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

        # 批量计算批次总数量和锁定量
        locked_map = await self._batch_calculate_locked_quantities(result)
        batch_total_map = await self._batch_calculate_batch_totals(result)
        for stock_item in result:
            key = f"{stock_item.get('warehouse_id')}_{stock_item.get('spec_id')}"
            # 当前库存 = 批次 current_quantity 之和
            batch_total = batch_total_map.get(key, 0)
            stock_item["quantity"] = batch_total
            locked_qty = locked_map.get(key, 0)
            stock_item["locked_quantity"] = locked_qty
            stock_item["available_quantity"] = batch_total - locked_qty

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
        """获取指定规格的库存状态（批量查询，O(1) SQL）"""
        if not spec_ids:
            return {}

        # 1. 查询所有相关库存记录（1次SQL）
        stocks = await Stock.filter(spec_id__in=spec_ids).all()
        if not stocks:
            return {}

        # 2. 批量查询仓库信息（1次SQL）
        warehouse_ids = list(set(s.warehouse_id for s in stocks))
        warehouses = {w["id"]: w for w in await warehouse_service.get_warehouse_by_ids(warehouse_ids)}

        # 3. 批量查询所有相关入库批次的 current_quantity 之和（1次SQL，GROUP BY）
        from tortoise.functions import Sum
        batch_rows = await InboundBatch.filter(
            spec_id__in=spec_ids
        ).group_by("spec_id", "warehouse_id").annotate(
            total=Sum("current_quantity")
        ).values_list("spec_id", "warehouse_id", "total")

        batch_map: Dict[str, float] = {}
        for spec_id, warehouse_id, total in batch_rows:
            batch_map[f"{spec_id}_{warehouse_id}"] = float(total) if total else 0

        # 4. 批量查询锁定量（复用已有批量方法）
        stock_list = [{"warehouse_id": s.warehouse_id, "spec_id": s.spec_id} for s in stocks]
        locked_map = await self._batch_calculate_locked_quantities(stock_list)

        # 5. 组装结果
        result: Dict[str, List[Dict[str, Any]]] = {}
        for stock in stocks:
            spec_id = stock.spec_id
            warehouse_id = stock.warehouse_id
            key = f"{spec_id}_{warehouse_id}"
            batch_total = batch_map.get(key, 0)
            locked_qty = locked_map.get(key, 0)
            available_quantity = batch_total - locked_qty

            if str(spec_id) not in result:
                result[str(spec_id)] = []

            result[str(spec_id)].append({
                "warehouse_id": warehouse_id,
                "warehouse_name": warehouses.get(warehouse_id, {}).get("name", ""),
                "quantity": batch_total,
                "locked_quantity": locked_qty,
                "available_quantity": available_quantity
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

        # 如果提供了 location_id，校验库位存在性
        location_id = inbound_data.get("location_id")
        location_code = inbound_data.get("location_code")
        if location_id:
            location = await WarehouseLocation.get_or_none(id=int(location_id))
            if not location:
                raise ValueError("库位不存在")
            location_code = location.location_code

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

        # 处理有效期
        expiry_date = inbound_data.get("expiry_date")
        if expiry_date and isinstance(expiry_date, str):
            from datetime import datetime as dt
            try:
                expiry_date = dt.fromisoformat(expiry_date)
            except ValueError:
                expiry_date = None

        # 处理批次编号：手动指定或自动生成
        batch_no = inbound_data.get("batch_no")
        if not batch_no:
            batch_no = await self._generate_batch_no(int(warehouse_id), int(spec_id))

        # 处理成本价：未传入则从规格价格取默认值
        cost_price = inbound_data.get("cost_price")
        if cost_price is None or cost_price == "":
            spec = await ProductSpec.filter(id=int(spec_id)).first()
            cost_price = float(spec.price) if spec and spec.price else None
        else:
            cost_price = float(cost_price)

        # 创建入库批次记录，初始 current_quantity = quantity
        inbound = await InboundBatch.create(
            warehouse_id=int(warehouse_id),
            product_id=int(product_id),
            product_code=inbound_data.get("product_code", ""),
            product_name=inbound_data.get("product_name", ""),
            spec_id=int(spec_id),
            spec_code=inbound_data.get("spec_code", ""),
            stock_id=stock["id"],
            quantity=float(quantity),
            location_id=int(location_id) if location_id else None,
            location_code=location_code or None,
            expiry_date=expiry_date,
            current_quantity=float(quantity),
            cost_price=cost_price,
            batch_no=batch_no,
            user_id=int(inbound_data.get("user_id", 0)),
            user_name=inbound_data.get("user_name", ""),
            remarks=inbound_data.get("remarks"),
        )
        return inbound.to_dict()

    async def _generate_batch_no(self, warehouse_id: int, spec_id: int) -> str:
        """自动生成批次编号: 仓库编码-规格编码-日期-序号"""
        warehouse = await Warehouse.filter(id=warehouse_id).first()
        spec = await ProductSpec.filter(id=spec_id).first()

        wh_code = warehouse.warehouse_code if warehouse else f"WH{warehouse_id}"
        sp_code = spec.spec_code if spec else f"SPEC{spec_id}"
        date_str = datetime.now().strftime("%Y%m%d")

        prefix = f"{wh_code}-{sp_code}-{date_str}-"

        # 查询当天同前缀的最大序号
        last_batch = await InboundBatch.filter(batch_no__startswith=prefix).order_by("-batch_no").first()
        if last_batch and last_batch.batch_no:
            try:
                seq = int(last_batch.batch_no[len(prefix):]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1

        return f"{prefix}{seq:03d}"

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


class WarehouseLocationService:
    """库位管理服务"""

    async def create_location(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建库位，校验 warehouse_id + location_code 唯一性"""
        warehouse_id = data.get("warehouse_id")
        location_code = data.get("location_code")

        if not warehouse_id or not location_code:
            raise ValueError("仓库ID和库位编码不能为空")

        # 校验仓库是否存在
        warehouse = await Warehouse.get_or_none(id=int(warehouse_id))
        if not warehouse:
            raise ValueError("仓库不存在")

        # 校验同仓库下库位编码唯一性
        existing = await WarehouseLocation.filter(
            warehouse_id=int(warehouse_id),
            location_code=location_code
        ).first()
        if existing:
            raise ValueError(f"仓库下已存在库位编码: {location_code}")

        location = await WarehouseLocation.create(
            warehouse_id=int(warehouse_id),
            location_code=location_code,
            location_name=data.get("location_name"),
            status=data.get("status", "active"),
            description=data.get("description"),
        )
        return location.to_dict()

    async def update_location(self, location_id: int, data: Dict[str, Any]) -> bool:
        """更新库位"""
        location = await WarehouseLocation.get_or_none(id=location_id)
        if not location:
            raise ValueError("库位不存在")

        # 如果修改了 location_code，需校验唯一性
        if "location_code" in data and data["location_code"] != location.location_code:
            existing = await WarehouseLocation.filter(
                warehouse_id=location.warehouse_id,
                location_code=data["location_code"]
            ).first()
            if existing:
                raise ValueError(f"仓库下已存在库位编码: {data['location_code']}")
            location.location_code = data["location_code"]

        if "location_name" in data:
            location.location_name = data["location_name"]
        if "status" in data:
            location.status = data["status"]
        if "description" in data:
            location.description = data["description"]

        await location.save()
        return True

    async def delete_location(self, location_id: int) -> bool:
        """删除库位"""
        location = await WarehouseLocation.get_or_none(id=location_id)
        if not location:
            raise ValueError("库位不存在")

        await location.delete()
        return True

    async def get_location_by_id(self, location_id: int) -> Optional[Dict[str, Any]]:
        """获取库位详情"""
        location = await WarehouseLocation.get_or_none(id=location_id)
        if not location:
            return None
        return location.to_dict()

    async def list_locations(
        self,
        warehouse_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Dict[str, Any]], int]:
        """获取库位列表，支持 warehouse_id 筛选"""
        query = WarehouseLocation.all()

        if warehouse_id:
            query = query.filter(warehouse_id=int(warehouse_id))

        total = await query.count()
        locations = await query.offset((page - 1) * page_size).limit(page_size)

        return [loc.to_dict() for loc in locations], total


# 创建服务实例
warehouse_service = WarehouseService()
stock_service = StockService()
inbound_batch_service = InboundBatchService()
outbound_batch_service = OutboundBatchService()
warehouse_location_service = WarehouseLocationService()