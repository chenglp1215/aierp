from typing import Dict, Any
import logging

from app.agent.skills.base import BaseSkill, SkillContext, SkillResult

logger = logging.getLogger(__name__)


class OrderAssistantSkill(BaseSkill):
    name = "order_assistant"
    description = "订单助手技能，当用户询问新建订单、修改订单、查询订单等问题时激活"
    enabled = True
    priority = 10
    content = "我检测到您想咨询订单相关问题。我可以帮您：\n1. 新建销售订单\n2. 查询订单状态\n3. 修改订单信息\n4. 取消订单\n\n请问您具体需要什么帮助？"

    async def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        message = kwargs.get("message", "")

        try:
            logger.info(f"OrderAssistantSkill executed for user {context.user_id}")

            response = self.content

            return SkillResult(
                success=True,
                content=response,
                skill_name=self.name,
                metadata={"message": message}
            )

        except Exception as e:
            logger.error(f"OrderAssistantSkill execution failed: {e}")
            return SkillResult(
                success=False,
                content="",
                skill_name=self.name,
                error=str(e)
            )


class CustomerServiceSkill(BaseSkill):
    name = "customer_service"
    description = "客服技能，当用户询问产品信息、服务流程、退换货政策等问题时激活"
    enabled = True
    priority = 8
    content = "您好！我是您的客服助手。关于您咨询的问题，我来为您解答。\n\n（这里可以连接实际的知识库或 FAQ 系统获取答案）"

    async def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        message = kwargs.get("message", "")

        try:
            logger.info(f"CustomerServiceSkill executed for user {context.user_id}")

            response = self.content

            return SkillResult(
                success=True,
                content=response,
                skill_name=self.name,
                metadata={"message": message}
            )

        except Exception as e:
            logger.error(f"CustomerServiceSkill execution failed: {e}")
            return SkillResult(
                success=False,
                content="",
                skill_name=self.name,
                error=str(e)
            )
