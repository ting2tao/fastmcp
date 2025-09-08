import requests
import json
from typing import Dict, Optional, Any

secret_key = "RQmzGVrkngFBZqxemftkhwiufeuuQVyf"
appid = "68009ed2e4b048c100e0ee69"


def get_token(input_secret_key: Optional[str] = None, input_appid: Optional[str] = None) -> Dict[str, Any]:
    """
    向指定的API发送POST请求获取认证令牌

    Args:
        input_secret_key: API认证所需的密钥，默认为模块级变量中定义的值
        input_appid: 应用ID，默认为模块级变量中定义的值

    Returns:
        Dict[str, Any]: 包含token的响应数据，通常包含token和其他相关信息

    Raises:
        requests.RequestException: 当请求失败时抛出
        json.JSONDecodeError: 当响应不是有效的JSON格式时抛出
    """
    # 引用模块级变量
    global secret_key, appid

    url = "https://galley-la-test.4009515151.com/aics/auth/getToken"

    # 如果没有提供参数，则使用模块级别的默认值
    _secret_key = input_secret_key if input_secret_key is not None else secret_key
    _appid = input_appid if input_appid is not None else appid

    # 准备请求体
    payload = {
        "secretKey": _secret_key,
        "appid": _appid
    }

    # 发送POST请求
    response = requests.post(url, json=payload)

    # 确保请求成功
    response.raise_for_status()

    # 解析并返回响应数据
    return response.json()


def get_token_string(input_secret_key: Optional[str] = None, input_appid: Optional[str] = None) -> str:
    """
    获取认证令牌并直接返回token字符串

    Args:
        input_secret_key: API认证所需的密钥，默认为模块级变量中定义的值
        input_appid: 应用ID，默认为模块级变量中定义的值

    Returns:
        str: 认证令牌字符串

    Raises:
        requests.RequestException: 当请求失败时抛出
        json.JSONDecodeError: 当响应不是有效的JSON格式时抛出
        KeyError: 当响应中不包含预期的字段结构时抛出
    """
    response_data = get_token(input_secret_key=input_secret_key, input_appid=input_appid)

    # 从响应中提取token
    # 根据API返回的实际结构，token位于response_data["data"]["token"]路径下
    # 示例响应结构：
    # {
    #  "data":
    #  {
    #  "expiresTime":1710841668000,
    #  "token":"eyJ0eXAiOiJKV1QiLCJhbGcQ5YnEM....1AwrYM0U"
    #  }
    #  ,
    #  "errorCode":"0",
    #  "errorMsg":""
    # }
    if "data" in response_data and "token" in response_data.get("data", {}):
        return response_data["data"]["token"]
    else:
        # 如果找不到预期的结构，返回空字符串
        return ""


def login_message(
    bot_id: str,
    user_id: str,
    user_name: str,
    email: Optional[str] = None,
    photo_url: Optional[str] = None,
    mobile: Optional[str] = None
) -> Dict[str, Any]:
    """
    消息对话登录接口

    Args:
        bot_id: AI角色ID
        user_id: 用户ID
        user_name: 用户名称
        email: 邮箱（可选）
        photo_url: 头像地址（可选）
        mobile: 手机号码（可选）

    Returns:
        Dict[str, Any]: 登录响应数据，包含以下字段：
            - data: 包含用户信息的字典
                - botId: AI角色ID
                - userId: 用户ID
                - userName: 用户名称
                - email: 邮箱（如果提供）
                - photoUrl: 头像地址（如果提供）
                - mobile: 手机号码（如果提供）
            - success: 布尔值，表示是否成功
            - errorCode: 错误码
            - errorMsg: 错误信息

    Raises:
        requests.RequestException: 当请求失败时抛出
        json.JSONDecodeError: 当响应不是有效的JSON格式时抛出
        ValueError: 当无法获取有效的认证token时抛出
    """
    # 获取认证token
    token = get_token_string()
    if not token:
        raise ValueError("无法获取有效的认证token")

    # 准备请求URL和头部
    url = "https://galley-la-test.4009515151.com/aics/message/login"
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }

    # 准备请求体
    payload = {
        "botId": bot_id,
        "userId": user_id,
        "userName": user_name
    }

    # 添加可选参数
    if email is not None:
        payload["email"] = email
    if photo_url is not None:
        payload["photoUrl"] = photo_url
    if mobile is not None:
        payload["mobile"] = mobile

    # 发送POST请求
    response = requests.post(url, headers=headers, json=payload)

    # 确保请求成功
    response.raise_for_status()

    # 解析并返回响应数据
    return response.json()


def send_message(
    bot_id: str,
    user_id: str,
    content: str,
    message_id: str,
    custom_parameters: Optional[str] = None
) -> Dict[str, Any]:
    """
    发送消息接口

    Args:
        bot_id: AI角色ID（必填）
        user_id: 用户ID（必填）
        content: 消息内容（必填）
        message_id: 会话ID（必填）
        custom_parameters: 自定义参数，JSON字符串（可选）

    Returns:
        Dict[str, Any]: 发送消息的响应数据，包含以下字段：
            - data: 包含响应信息的字典
                - id: 消息记录ID
                - responseType: 响应类型
                - responseContent: 响应内容
                - reasoningContent: 推理过程
                - messageId: 会话ID
                - questionSuggestions: 问题建议列表
                - knowledge: 知识ID集合
            - success: 布尔值，表示是否成功
            - errorCode: 错误码
            - errorMsg: 错误信息

    Raises:
        requests.RequestException: 当请求失败时抛出
        json.JSONDecodeError: 当响应不是有效的JSON格式时抛出
        ValueError: 当无法获取有效的认证token时抛出
    """
    # 获取认证token
    token = get_token_string()
    if not token:
        raise ValueError("无法获取有效的认证token")

    # 准备请求URL和头部
    url = "https://galley-la-test.4009515151.com/aics/message/sendMessage"
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }

    # 准备请求体
    payload = {
        "botId": bot_id,
        "userId": user_id,
        "content": content,
        "messageId": message_id
    }

    if custom_parameters is not None:
        payload["customParameters"] = custom_parameters

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    # 示例用法
    try:
        # 使用默认参数获取完整响应
        token_response = get_token()
        print("使用默认参数的完整响应:", token_response)

        # 使用默认参数仅获取token字符串
        token = get_token_string()
        print("默认参数Token:", token)

        # 测试消息对话登录
        login_response = login_message(
            bot_id="68009ed2e4b048c100e0ee69",
            user_id="shict01",
            user_name="shict",
            email="shict01@onewo.com"
        )
        print("登录响应:", login_response)

        # 测试发送消息
        message_response = send_message(
            bot_id="68009ed2e4b048c100e0ee69",
            user_id="shict01",
            content="""
在哪里拿货呀
小勺子和筷子图还要吗？8双筷子8勺子8碗8盘
多少钱，怎么付？
临港新天地
[破涕为笑]这么远
自提可35
16号线，可以不出站，送到滴水湖地铁站
也可以周末到滴水湖玩，约个时间地点
""",
            message_id="test_message_001"
        )
        print("消息发送响应:", message_response)

    except Exception as e:
        print(f"操作出错: {e}")
