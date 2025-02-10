"""
Xenon 管理 https://github.com/McZoo/Xenon/blob/master/lib/control.py
"""

from functools import wraps
from typing import Union

from app.core.config import Config
from app.core.settings import ADMIN_USER, BANNED_USER, GROUP_ADMIN_USER
from app.util.graia import Friend, Group, Member, MemberPerm
from app.util.online_config import set_plugin_switch
from app.util.phrases import not_admin


class Permission:
    """
    用于管理权限的类，不应被实例化
    """

    MASTER = 4
    SUPER_ADMIN = 3
    GROUP_ADMIN = 2
    USER = 1
    BANNED = 0
    DEFAULT = USER

    @classmethod
    def get(cls, member: Union[Member, Friend, int]) -> int:
        """
        获取用户的权限
        :param member: 用户实例或QQ号
        :return: 等级，整数
        """

        if isinstance(member, Member):
            user = member.id
            user_permission = member.permission
        elif isinstance(member, Friend):
            user = member.id
            user_permission = cls.DEFAULT
        else:
            user = member
            user_permission = cls.DEFAULT

        if user == int(Config.master_qq):
            return cls.MASTER
        elif user in ADMIN_USER:
            return cls.SUPER_ADMIN
        elif user in BANNED_USER:
            return cls.BANNED
        elif user_permission in [MemberPerm.Administrator, MemberPerm.Owner] or user in GROUP_ADMIN_USER:
            return cls.GROUP_ADMIN
        else:
            return cls.DEFAULT

    @classmethod
    def require(cls, level: int = GROUP_ADMIN):
        """
        插件鉴权
        :param level: 允许的权限
        """

        def perm_check(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                sender = None
                target = None
                for arg in args:
                    if isinstance(arg, (Friend, Group)):
                        sender = arg
                    if isinstance(arg, (Friend, Member)):
                        target = arg
                    if sender and target:
                        break
                else:
                    raise TypeError("被装饰函数必须包含一个 Friend 或 Member 和 Group 参数")
                if cls.manual(target, level):
                    return await func(*args, **kwargs)
                else:
                    not_admin(sender)

            return wrapper

        return perm_check

    @classmethod
    def manual(cls, member: Union[Member, Friend, int], level: int = DEFAULT) -> bool:
        """
        指示需要 `level` 以上等级才能触发，默认为至少 USER 权限
        :param member: 用户实例或QQ号
        :param level: 限制等级
        """

        return cls.get(member) >= level

    @classmethod
    def compare(cls, src: Union[Member, Friend, int], dst: Union[Member, Friend, int]) -> bool:
        """
        比较 src 和 dst 的权限，src大于dst时返回true
        :param src: 比较用户
        :param dst: 被比较用户
        :return: src > dst = True (俩者权限相同时返回False)
        """

        return cls.get(src) > cls.get(dst)


class Switch:
    """用于开关功能的类，不应被实例化"""

    @classmethod
    async def plugin(cls, src: Union[Member, Friend, int], perm, dst: Union[Group, int]):
        if isinstance(src, Member):
            if not Permission.manual(src, Permission.GROUP_ADMIN):
                return "你的权限不足，无权操作此命令"
        elif not Permission.manual(src, Permission.SUPER_ADMIN) and not Permission.compare(src, dst):
            return "你的权限不足，无权操作此命令"
        return "操作成功" if await set_plugin_switch(dst, perm) else "操作失败"
