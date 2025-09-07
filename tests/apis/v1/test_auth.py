# tests/apis/v1/test_auth.py (异步版)

from fastapi.testclient import TestClient
import pytest # 导入 pytest

# 关键改动 1：标记测试为异步
@pytest.mark.asyncio 
async def test_wechat_login_for_new_user(client: TestClient):
    test_code = "some-test-code"

    # 关键改动 2：因为 TestClient 现在会在异步模式下运行，但其调用仍然是同步风格
    # TestClient 内部会处理好同步和异步的转换
    response = client.post( 
        "/api/v1/auth/wechat",
        json={"code": test_code},
    )

    assert response.status_code == 200
    assert "access_token" in response.json()