"""一个最小工具 Agent。天气结果是演示数据，不代表实时天气。"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

from openai import OpenAI, OpenAIError


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "读取演示天气数据。结果不是实时天气。",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "要查询的城市名称"}
                },
                "required": ["city"],
                "additionalProperties": False,
            },
        },
    }
]

DEMO_WEATHER = {
    "city": "台北",
    "issued_at": "演示资料，无真实发布时间",
    "forecast_for": "演示时段：今晚",
    "rain_probability": 0.70,
}


def get_weather(city: str) -> dict[str, Any]:
    """演示工具；真实项目应换成有来源和时间的天气服务。"""
    if city.strip() != "台北":
        return {
            "ok": False,
            "error": {
                "code": "CITY_NOT_IN_DEMO",
                "message": "演示数据只包含台北",
            },
        }
    return {"ok": True, "data": DEMO_WEATHER}


def dispatch_tool(name: str, raw_arguments: str) -> dict[str, Any]:
    """把模型输出当作不可信请求，先验证，再执行。"""
    if name != "get_weather":
        return {
            "ok": False,
            "error": {"code": "UNKNOWN_TOOL", "message": "不允许的工具"},
        }

    if not isinstance(raw_arguments, str):
        return {
            "ok": False,
            "error": {"code": "INVALID_ARGUMENTS", "message": "参数必须是 JSON 字符串"},
        }

    try:
        arguments = json.loads(raw_arguments)
    except json.JSONDecodeError:
        return {
            "ok": False,
            "error": {"code": "INVALID_JSON", "message": "参数不是合法 JSON"},
        }

    if (
        not isinstance(arguments, dict)
        or set(arguments) != {"city"}
        or not isinstance(arguments["city"], str)
        or not arguments["city"].strip()
    ):
        return {
            "ok": False,
            "error": {"code": "INVALID_ARGUMENTS", "message": "需要非空的 city 字符串"},
        }

    return get_weather(arguments["city"])


def run(question: str) -> str:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("请先设置 DEEPSEEK_API_KEY 环境变量")

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-flash")
    messages: list[Any] = [
        {
            "role": "system",
            "content": (
                "你是天气助手。工具只提供演示数据，不代表当前真实天气。"
                "需要天气数据时使用工具；回答时明确标出数据是演示。"
                "工具失败或资料不足时说明限制，不要编造实时天气。"
            ),
        },
        {"role": "user", "content": question},
    ]

    max_model_rounds = 4
    for _ in range(max_model_rounds):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )
        if not response.choices:
            raise RuntimeError("模型服务没有返回候选结果")
        choice = response.choices[0]
        if choice.finish_reason == "length":
            raise RuntimeError("模型输出被截断")
        message = choice.message
        calls = message.tool_calls or []

        if calls:
            messages.append(message)
            for call in calls:
                result = dispatch_tool(call.function.name, call.function.arguments)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )
            continue

        if message.content:
            return message.content

        raise RuntimeError("模型未返回可展示的文字或工具请求")

    raise RuntimeError("达到模型轮数上限，任务未完成")


def main() -> int:
    question = " ".join(sys.argv[1:]) or "台北今晚降雨概率是多少？"
    try:
        print(run(question))
    except OpenAIError as exc:
        print(f"模型服务失败：{exc.__class__.__name__}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"任务失败：{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
