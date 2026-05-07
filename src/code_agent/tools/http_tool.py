#!/usr/bin/env python3
"""
HTTP 请求工具
使用 httpx 发送 HTTP 请求到特定地址
区别于网络搜索工具，此工具可直接请求指定的 API 或网页
"""

from typing import Any

import httpx
from pydantic import BaseModel, Field

from code_agent.tools._manager import tool
from code_agent.utils.tool_util import build_tool_response


class HttpRequestParams(BaseModel):
    """HTTP 请求工具参数模型"""

    url: str = Field(..., description="请求的目标 URL")
    method: str = Field("GET", description="HTTP 方法，支持 GET、POST、PUT、DELETE，默认为 GET")
    headers: dict[str, str] | None = Field(None, description="请求头字典，可选")
    params: dict[str, str] | None = Field(None, description="URL 查询参数，可选")
    data: dict[str, Any] | None = Field(None, description="POST 请求体数据，可选")
    json_data: dict[str, Any] | None = Field(None, description="JSON 请求体，可选")
    timeout: int = Field(30, description="请求超时时间（秒），默认为 30")
    allow_redirects: bool = Field(True, description="是否允许重定向，默认为 True")


@tool(
    name="send_http_request",
    description="发送 HTTP 请求到指定 URL。适用于调用 API 或获取网页源码。",
    param_type=HttpRequestParams,
    tags=["code", "plan"],
)
async def http_request(params: HttpRequestParams) -> str:
    """发送 HTTP 请求

    Args:
        params: 参数对象

    Returns:
        JSON 格式的结果字符串
    """
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(params.timeout),
        follow_redirects=params.allow_redirects,
    ) as client:
        method = params.method.upper()

        request_kwargs: dict[str, Any] = {
            "url": params.url,
        }

        if params.headers:
            request_kwargs["headers"] = params.headers

        if params.params:
            request_kwargs["params"] = params.params

        if params.json_data:
            request_kwargs["json"] = params.json_data
        elif params.data:
            request_kwargs["data"] = params.data

        response = await client.request(method, **request_kwargs)

        try:
            response_data = response.json()
        except ValueError:
            response_data = response.text

        return build_tool_response(
            True,
            f"请求成功，状态码: {response.status_code}",
            data={
                "url": params.url,
                "method": method,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": response_data,
                "encoding": response.encoding,
            },
        )
