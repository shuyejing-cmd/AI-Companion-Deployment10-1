# tests/apis/v1/test_companions.py

import pytest
from fastapi.testclient import TestClient

# --- 场景一：测试成功创建伙伴 ---
@pytest.mark.asyncio
async def test_create_companion_success(authenticated_client: TestClient):
    """
    测试一个已认证的用户能否成功创建一个新的AI伙伴。
    """
    # 准备要发送的数据
    companion_data = {
        "name": "导师Alex",
        "description": "一位资深的Python架构师",
        "instructions": "你的目标是“授人以渔”，通过提问引导我思考。",
        "seed": "你好，我是Alex，你的专属技术导师。"
    }

    # 使用“已登录”的客户端发起请求
    response = authenticated_client.post(
        "/api/v1/companions/",
        json=companion_data
    )

    # 断言结果是否符合预期
    assert response.status_code == 201 # 201 Created 是RESTful API的最佳实践
    response_data = response.json()
    assert response_data["name"] == companion_data["name"]
    assert "id" in response_data
    assert "user_id" in response_data

# --- 场景二：测试未登录时创建伙伴 ---
@pytest.mark.asyncio
async def test_create_companion_unauthenticated(client: TestClient):
    """
    测试一个未登录的客户端尝试创建伙伴时，是否会被拒绝。
    """
    companion_data = {
        "name": "游客伙伴",
        "description": "一段描述",
        "instructions": "一些指令",
        "seed": "一段对话"
    }

    # 使用“未登录”的普通客户端发起请求
    response = client.post(
        "/api/v1/companions/",
        json=companion_data
    )

    # 断言结果是否符合预期
    assert response.status_code == 401 # 401 Unauthorized