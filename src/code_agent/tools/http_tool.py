#!/usr/bin/env python3
"""
HTTP 请求工具
使用 httpx 发送 HTTP 请求到特定地址
区别于网络搜索工具，此工具可直接请求指定的 API 或网页
"""

from typing import Any, Dict, Optional

import httpx
from pydantic import BaseModel, Field

from code_agent.tools._manager import tool
from code_agent.utils.tool_util import (
    build_tool_response,
    validate_params,
)


class HttpRequestParams(BaseModel):
    """HTTP 请求工具参数模型"""

    url: str = Field(..., description="请求的目标 URL")
    method: str = Field("GET", description="HTTP 方法，支持 GET、POST、PUT、DELETE，默认为 GET")
    headers: Optional[Dict[str, str]] = Field(None, description="请求头字典，可选")
    params: Optional[Dict[str, str]] = Field(None, description="URL 查询参数，可选")
    data: Optional[Dict[str, Any]] = Field(None, description="POST 请求体数据，可选")
    json: Optional[Dict[str, Any]] = Field(None, description="JSON 请求体，可选")
    timeout: int = Field(30, description="请求超时时间（秒），默认为 30")
    allow_redirects: bool = Field(True, description="是否允许重定向，默认为 True")


@tool(
    name="send_http_request",
    description="发送 HTTP 请求到指定 URL。适用于调用 API 或获取网页源码。",
    param_type=HttpRequestParams,
    tags=["code", "plan"],
)
async def http_request(params: str) -> str:
    """发送 HTTP 请求

    Args:
        params: JSON 格式的参数字符串

    Returns:
        JSON 格式的结果字符串
    """
    # 使用统一工具函数校验参数
    validated_params = validate_params(params, HttpRequestParams)

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(validated_params.timeout),
        follow_redirects=validated_params.allow_redirects,
    ) as client:
        method = validated_params.method.upper()

        # 构建请求参数
        request_kwargs: Dict[str, Any] = {
            "url": validated_params.url,
        }

        if validated_params.headers:
            request_kwargs["headers"] = validated_params.headers

        if validated_params.params:
            request_kwargs["params"] = validated_params.params

        if validated_params.json:
            request_kwargs["json"] = validated_params.json
        elif validated_params.data:
            request_kwargs["data"] = validated_params.data

        # 根据方法发送请求
        response = await client.request(method, **request_kwargs)

        # 获取响应内容
        try:
            response_data = response.json()
        except ValueError:
            response_data = response.text

        return build_tool_response(
            True,
            f"请求成功，状态码: {response.status_code}",
            data={
                "url": validated_params.url,
                "method": method,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": response_data,
                "encoding": response.encoding,
            },
        )
