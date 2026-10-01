"""零依赖的下一 token 训练演示：每个当前 token 只记下一 token 的概率。

这是可微分的二元转移模型，不是 Transformer。它用于观察损失与参数更新，
不具备大语言模型的上下文理解或泛化能力。
"""

from math import exp, log


TOKENS = ["今晚", "可能", "下雨", "带伞"]
PAIRS = [("今晚", "可能"), ("可能", "下雨"), ("下雨", "带伞")]
INDEX = {token: i for i, token in enumerate(TOKENS)}
WEIGHTS = [[0.0 for _ in TOKENS] for _ in TOKENS]


def probabilities(current: str) -> list[float]:
    """将一个输入 token 对应的一行可训练分数转为概率。"""
    scores = WEIGHTS[INDEX[current]]
    offset = max(scores)
    values = [exp(score - offset) for score in scores]
    total = sum(values)
    return [value / total for value in values]


def average_loss() -> float:
    return sum(-log(probabilities(current)[INDEX[target]]) for current, target in PAIRS) / len(PAIRS)


def train(epochs: int = 200, learning_rate: float = 0.2) -> None:
    for _ in range(epochs):
        for current, target in PAIRS:
            row = WEIGHTS[INDEX[current]]
            prediction = probabilities(current)
            # softmax + 交叉熵对该行分数的梯度是“预测概率 - 目标指示值”。
            for index in range(len(TOKENS)):
                wanted = 1.0 if index == INDEX[target] else 0.0
                row[index] -= learning_rate * (prediction[index] - wanted)


def show(label: str) -> None:
    print(label, f"平均损失 = {average_loss():.3f}")
    for current, target in PAIRS:
        print(f"  看到 {current!r}，目标 {target!r} 的概率 = {probabilities(current)[INDEX[target]]:.3f}")


if __name__ == "__main__":
    show("训练前")
    train()
    show("训练后")
    print("注意：只看当前 token 的模型不能理解长上下文，也不知道今晚的真实天气。")
