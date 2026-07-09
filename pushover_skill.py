"""
PushoverSkill — 本地 Pushover 全功能工具
覆盖所有 Pushover API，带完整 docstring，无需查文档。
API 参考: https://pushover.net/api
"""

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://api.pushover.net/1"


class PushoverSkill:
    """Pushover 全功能封装，token 必填，user_key 可选（发消息时才需要）。"""

    def __init__(self, token: str, user_key: str = None):
        self.token = token
        self.user_key = user_key

    # =================================================================
    # 核心发送
    # =================================================================
    def send(
        self,
        message: str,
        title: str = "",
        url: str = "",
        url_title: str = "",
        priority: int = 0,
        sound: str = None,
        device: str = None,
        html: bool = False,
        ttl: int = None,
        retry: int = None,
        expire: int = None,
        attachment: str = None,
        monospace: bool = False,
        timestamp: int = None,
        callback_url: str = None,
    ) -> dict:
        """
        发送推送消息。

        priority:
          -2 — 静默（不弹通知）
          -1 — 仅通知栏（不响不亮）
           0 — 默认
           1 — 高优先级（绕过静音）
           2 — 紧急重复（必须配合 retry + expire，需用户确认）

        sound: pushover/bike/bugle/cashregister/classical/cosmic/...
               调用 get_sounds() 获取完整列表。

        html=True 时 message 支持 <b>/<i>/<u>/<font>/<a> 标签。

        ttl:      消息存活秒数（仅 priority=2）
        retry:    重试间隔秒数（仅 priority=2，最小 30）
        expire:   超时秒数（仅 priority=2，最大 10800）
        attachment: 图片文件路径（Base64），见 Pushover 文档
        monospace:  等宽字体显示
        timestamp:  Unix 时间戳，用于消息时间展示
        callback_url: priority=2 确认后回调地址
        """
        payload = {
            "token": self.token,
            "user": self.user_key,
            "message": message,
            "title": title,
            "priority": priority,
        }
        if url:
            payload["url"] = url
            payload["url_title"] = url_title or "View"
        if sound:
            payload["sound"] = sound
        if device:
            payload["device"] = device
        if html:
            payload["html"] = "1"
        if ttl is not None:
            payload["ttl"] = ttl
        if retry is not None:
            payload["retry"] = retry
        if expire is not None:
            payload["expire"] = expire
        if attachment:
            payload["attachment"] = attachment
        if monospace:
            payload["monospace"] = "1"
        if timestamp is not None:
            payload["timestamp"] = timestamp
        if callback_url:
            payload["callback_url"] = callback_url

        resp = requests.post(
            f"{BASE_URL}/messages.json", data=payload, timeout=15, verify=False
        )
        return resp.json()

    # =================================================================
    # 群组管理
    # =================================================================
    def add_user(self, group_key: str, user_key: str, memo: str = "") -> dict:
        """将用户加入群组。"""
        return requests.post(
            f"{BASE_URL}/groups/{group_key}/add_user.json",
            data={"token": self.token, "user": user_key, "memo": memo},
            timeout=10,
            verify=False,
        ).json()

    def remove_user(self, group_key: str, user_key: str) -> dict:
        """将用户移出群组。"""
        return requests.post(
            f"{BASE_URL}/groups/{group_key}/remove_user.json",
            data={"token": self.token, "user": user_key},
            timeout=10,
            verify=False,
        ).json()

    def disable_user(self, group_key: str, user_key: str) -> dict:
        """临时禁用群组内某用户的推送。"""
        return requests.post(
            f"{BASE_URL}/groups/{group_key}/disable_user.json",
            data={"token": self.token, "user": user_key},
            timeout=10,
            verify=False,
        ).json()

    def enable_user(self, group_key: str, user_key: str) -> dict:
        """重新启用群组内某用户的推送。"""
        return requests.post(
            f"{BASE_URL}/groups/{group_key}/enable_user.json",
            data={"token": self.token, "user": user_key},
            timeout=10,
            verify=False,
        ).json()

    # =================================================================
    # 验证
    # =================================================================
    def validate(self, token: str = None, user: str = None) -> dict:
        """
        验证 token 和/或 user key 是否有效。
        不传参则用实例默认值。
        """
        payload = {"token": token or self.token}
        if user or self.user_key:
            payload["user"] = user or self.user_key
        return requests.post(
            f"{BASE_URL}/users/validate.json",
            data=payload,
            timeout=10,
            verify=False,
        ).json()

    def validate_group(self, group_key: str) -> dict:
        """验证群组是否存在且有权限。"""
        return requests.post(
            f"{BASE_URL}/groups/{group_key}/validate.json",
            data={"token": self.token},
            timeout=10,
            verify=False,
        ).json()

    # =================================================================
    # 查询
    # =================================================================
    def get_limits(self) -> dict:
        """查询当前 app 的剩余/总数/下次重置时间。"""
        return requests.get(
            f"{BASE_URL}/apps/limits.json",
            params={"token": self.token},
            timeout=10,
            verify=False,
        ).json()

    def get_receipt(self, receipt: str) -> dict:
        """查询 priority=2 紧急消息的送达状态。"""
        return requests.get(
            f"{BASE_URL}/receipts/{receipt}.json",
            params={"token": self.token},
            timeout=10,
            verify=False,
        ).json()

    def cancel_emergency(self, receipt: str) -> dict:
        """取消尚未确认的紧急消息（priority=2）。"""
        return requests.post(
            f"{BASE_URL}/receipts/{receipt}/cancel.json",
            data={"token": self.token},
            timeout=10,
            verify=False,
        ).json()

    # =================================================================
    # 音效
    # =================================================================
    def get_sounds(self) -> dict:
        """获取所有可用音效列表。返回 {"sounds": {"pushover": "Pushover (default)", ...}}。"""
        return requests.get(
            f"{BASE_URL}/sounds.json",
            params={"token": self.token},
            timeout=10,
            verify=False,
        ).json()

    # =================================================================
    # Glances (智能手表)
    # =================================================================
    def update_glance(
        self,
        user_key: str,
        text: str,
        title: str = "",
        subtext: str = "",
        count: int = None,
        percent: int = None,
    ) -> dict:
        """更新 Apple Watch / Wear OS 的 Glance 数据。"""
        payload = {"token": self.token, "user": user_key, "text": text}
        if title:
            payload["title"] = title
        if subtext:
            payload["subtext"] = subtext
        if count is not None:
            payload["count"] = count
        if percent is not None:
            payload["percent"] = percent
        return requests.post(
            f"{BASE_URL}/glances.json", data=payload, timeout=10, verify=False
        ).json()

    # =================================================================
    # License
    # =================================================================
    def assign_license(self, email: str) -> dict:
        """为用户邮箱分配一个 Pushover 桌面版 License。"""
        return requests.post(
            f"{BASE_URL}/licenses/assign.json",
            data={"token": self.token, "email": email},
            timeout=10,
            verify=False,
        ).json()

    def revoke_license(self, license_id: str) -> dict:
        """吊销一个已分配的 License。"""
        return requests.post(
            f"{BASE_URL}/licenses/revoke.json",
            data={"token": self.token, "license": license_id},
            timeout=10,
            verify=False,
        ).json()
