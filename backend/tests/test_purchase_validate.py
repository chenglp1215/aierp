"""
采购单校验增强 - 单元测试

测试 _validate_receive_info 校验方法：
- 仓库采购时必须选择目标仓库
- 直运采购时必须填写收货地址和收货人
- 自动设置 receive_info.type 保持与采购类型一致
"""
import pytest
from services.purchase_order_service_mysql import PurchaseOrderService


class TestValidateReceiveInfo:
    """收货信息与采购类型一致性校验测试"""

    service = PurchaseOrderService()

    # ---- 仓库采购校验 ----

    def test_warehouse_with_warehouse_id_passes(self):
        """仓库采购 + 有仓库ID -> 校验通过"""
        data = {
            "purchase_type": "warehouse",
            "receive_info": {"warehouse_id": 1},
        }
        self.service._validate_receive_info(data)
        assert data["receive_info"]["type"] == "warehouse"

    def test_warehouse_without_warehouse_id_raises(self):
        """仓库采购 + 无仓库ID -> 抛出 ValueError"""
        data = {
            "purchase_type": "warehouse",
            "receive_info": {},
        }
        with pytest.raises(ValueError, match="仓库采购时必须选择目标仓库"):
            self.service._validate_receive_info(data)

    def test_warehouse_with_none_warehouse_id_raises(self):
        """仓库采购 + warehouse_id 为 None -> 抛出 ValueError"""
        data = {
            "purchase_type": "warehouse",
            "receive_info": {"warehouse_id": None},
        }
        with pytest.raises(ValueError, match="仓库采购时必须选择目标仓库"):
            self.service._validate_receive_info(data)

    def test_warehouse_with_zero_warehouse_id_raises(self):
        """仓库采购 + warehouse_id 为 0 -> 抛出 ValueError"""
        data = {
            "purchase_type": "warehouse",
            "receive_info": {"warehouse_id": 0},
        }
        with pytest.raises(ValueError, match="仓库采购时必须选择目标仓库"):
            self.service._validate_receive_info(data)

    # ---- 直运采购校验 ----

    def test_direct_with_all_fields_passes(self):
        """直运采购 + 有收货地址和收货人 -> 校验通过"""
        data = {
            "purchase_type": "direct",
            "receive_info": {
                "customer_addr": "北京市朝阳区xxx",
                "contact_person": "张三",
            },
        }
        self.service._validate_receive_info(data)
        assert data["receive_info"]["type"] == "customer"

    def test_direct_without_customer_addr_raises(self):
        """直运采购 + 无收货地址 -> 抛出 ValueError"""
        data = {
            "purchase_type": "direct",
            "receive_info": {"contact_person": "张三"},
        }
        with pytest.raises(ValueError, match="直运采购时必须填写收货地址"):
            self.service._validate_receive_info(data)

    def test_direct_without_contact_person_raises(self):
        """直运采购 + 无收货人 -> 抛出 ValueError"""
        data = {
            "purchase_type": "direct",
            "receive_info": {"customer_addr": "北京市朝阳区xxx"},
        }
        with pytest.raises(ValueError, match="直运采购时必须填写收货人"):
            self.service._validate_receive_info(data)

    def test_direct_with_empty_fields_raises(self):
        """直运采购 + 空字符串收货地址 -> 抛出 ValueError"""
        data = {
            "purchase_type": "direct",
            "receive_info": {
                "customer_addr": "",
                "contact_person": "张三",
            },
        }
        with pytest.raises(ValueError, match="直运采购时必须填写收货地址"):
            self.service._validate_receive_info(data)

    def test_direct_with_empty_contact_raises(self):
        """直运采购 + 空字符串收货人 -> 抛出 ValueError"""
        data = {
            "purchase_type": "direct",
            "receive_info": {
                "customer_addr": "北京市朝阳区xxx",
                "contact_person": "",
            },
        }
        with pytest.raises(ValueError, match="直运采购时必须填写收货人"):
            self.service._validate_receive_info(data)

    # ---- 边界情况 ----

    def test_no_purchase_type_skips_validation(self):
        """无采购类型 -> 跳过校验"""
        data = {"receive_info": {}}
        self.service._validate_receive_info(data)  # 不应抛出异常

    def test_empty_receive_info_defaults_to_empty_dict(self):
        """无 receive_info -> 默认空字典，仓库采购应报错"""
        data = {"purchase_type": "warehouse"}
        with pytest.raises(ValueError, match="仓库采购时必须选择目标仓库"):
            self.service._validate_receive_info(data)

    def test_unknown_purchase_type_skips_validation(self):
        """未知采购类型 -> 跳过校验"""
        data = {
            "purchase_type": "unknown_type",
            "receive_info": {},
        }
        self.service._validate_receive_info(data)  # 不应抛出异常

    # ---- receive_info.type 自动设置 ----

    def test_warehouse_type_auto_set(self):
        """仓库采购自动设置 receive_info.type = 'warehouse'"""
        data = {
            "purchase_type": "warehouse",
            "receive_info": {"warehouse_id": 5},
        }
        self.service._validate_receive_info(data)
        assert data["receive_info"]["type"] == "warehouse"

    def test_direct_type_auto_set(self):
        """直运采购自动设置 receive_info.type = 'customer'"""
        data = {
            "purchase_type": "direct",
            "receive_info": {
                "customer_addr": "上海市浦东新区xxx",
                "contact_person": "李四",
            },
        }
        self.service._validate_receive_info(data)
        assert data["receive_info"]["type"] == "customer"

    def test_warehouse_type_overrides_existing(self):
        """仓库采购覆盖已有的 receive_info.type"""
        data = {
            "purchase_type": "warehouse",
            "receive_info": {"warehouse_id": 3, "type": "customer"},
        }
        self.service._validate_receive_info(data)
        assert data["receive_info"]["type"] == "warehouse"
