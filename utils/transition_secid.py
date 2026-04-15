def convert_to_secid(code: str) -> str:
    """
    股票代码转换成东方财富 secid 格式
    """
    code = code.strip()
    if code.startswith(("0", "3")):
        return f"0.{code}"
    elif code.startswith(("6", "5", "9")):
        return f"1.{code}"
    else:
        raise ValueError(f"不支持的股票代码: {code}")


def to_eastmoney_secid(code: str) -> str:
    """
    股票代码转换成东方财富 secid 格式
    """
    code = code.strip()
    if code.startswith(("0", "3")):
        return f"sz.{code}"
    elif code.startswith(("6", "5", "9")):
        return f"sh.{code}"
    else:
        raise ValueError(f"不支持的股票代码: {code}")


