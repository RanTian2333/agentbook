"""纯文本模型输出怎样变成受控工具请求；不连接模型或真实天气服务。"""

import json
from typing import Any


class InvalidReply(ValueError):
    """模型响应不符合本示例的文本协议。"""


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InvalidReply(f"重复字段：{key}")
        result[key] = value
    return result


def parse_reply(raw: str) -> dict[str, Any]:
    """只接收一个完整 JSON 对象，并验证本例允许的两种输出形状。"""
    if len(raw.encode("utf-8")) > 4096:
        raise InvalidReply("响应过长")
    try:
        reply = json.loads(raw, object_pairs_hook=_unique_pairs)
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise InvalidReply("响应不是完整 JSON") from exc

    if not isinstance(reply, dict):
        raise InvalidReply("顶层必须是对象")
    if reply.get("kind") == "final":
        if set(reply) != {"kind", "answer"} or not isinstance(reply["answer"], str):
            raise InvalidReply("最终回答字段不符合协议")
        return reply
    if reply.get("kind") == "tool_call":
        if set(reply) != {"kind", "name", "arguments"}:
            raise InvalidReply("工具请求字段不符合协议")
        if reply["name"] != "get_weather":
            raise InvalidReply("未知工具")
        args = reply["arguments"]
        if not isinstance(args, dict) or set(args) != {"city"}:
            raise InvalidReply("工具参数字段不符合协议")
        if not isinstance(args["city"], str) or not args["city"].strip():
            raise InvalidReply("city 必须是非空字符串")
        return reply
    raise InvalidReply("未知响应类型")


def dispatch_demo(reply: dict[str, Any]) -> dict[str, Any]:
    """演示程序边界：只允许查询示例城市，返回显式的模拟资料。"""
    if reply["kind"] != "tool_call":
        raise InvalidReply("最终回答不能当工具请求执行")
    city = reply["arguments"]["city"].strip()
    if city not in {"台北", "新北"}:
        raise InvalidReply("本次演示没有这个城市的授权数据")
    return {
        "ok": True,
        "city": city,
        "source": "演示数据，非实时天气",
        "issued_at": "演示资料，无真实发布时间",
        "forecast_for": "演示时段：今晚",
        "rain_probability": 0.70 if city == "台北" else 0.40,
    }


if __name__ == "__main__":
    examples = [
        '{"kind":"tool_call","name":"get_weather","arguments":{"city":"台北"}}',
        '{"kind":"final","answer":"目前缺少实时天气资料。"}',
        '我来调用 get_weather(city="台北")',
    ]
    for raw in examples:
        try:
            parsed = parse_reply(raw)
            if parsed["kind"] == "tool_call":
                print("工具结果：", dispatch_demo(parsed))
            else:
                print("最终回答：", parsed["answer"])
        except InvalidReply as exc:
            print("拒绝输出：", exc)
