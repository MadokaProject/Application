from typing import Union

from app.core.config import Config
from app.core.settings import (
    ACTIVE_GROUP,
    ACTIVE_USER,
    ADMIN_USER,
    BANNED_USER,
    GROUP_ADMIN_USER,
    GROUP_PERM,
)
from app.entities.group import BotGroup
from app.entities.user import BotUser
from app.util.alconna import Args, Arpamar, Commander, Option, Subcommand
from app.util.control import Permission
from app.util.graia import Ariadne, At, Friend, Group, Member, message
from app.util.phrases import not_admin

from .database.database import Group as DBGroup
from .database.database import User as DBUser

command = Commander(
    "perm",
    "授权",
    Subcommand(
        "user",
        help_text="用户白名单",
        options=[
            Option("--add|-a", args=Args["qq", [At, int]], help_text="用户加入白名单"),
            Option("--delete|-d", args=Args["qq", [At, int]], help_text="用户移出白名单"),
            Option("--list|-l", help_text="查看用户白名单"),
        ],
    ),
    Subcommand(
        "blacklist",
        help_text="用户黑名单",
        options=[
            Option("--add|-a", args=Args["qq", [At, int]], help_text="用户加入黑名单"),
            Option("--delete|-d", args=Args["qq", [At, int]], help_text="用户移出黑名单"),
            Option("--list|-l", help_text="查看用户黑名单"),
        ],
    ),
    Subcommand(
        "group",
        help_text="群组白名单",
        options=[
            Option("--add|-a", args=Args["group", int], help_text="群组加入白名单"),
            Option("--delete|-d", args=Args["group", int], help_text="群组移出白名单"),
            Option("--list|-l", help_text="查看群组白名单"),
        ],
    ),
    Option(
        "grant",
        help_text="调整用户权限等级(该功能操作者权限高于操作对象即可",
        args=Args["qq", [At, int]]["level", int],
    ),
    help_text="授权, 仅管理可用!",
)


@command.parse("user", permission=Permission.SUPER_ADMIN)
async def user(app: Ariadne, target: Union[Friend, Member], sender: Union[Friend, Group], cmd: Arpamar):
    if cmd.find("user.add"):
        _target = cmd.query("qq").target if isinstance(cmd.query("qq"), At) else cmd.query("qq")
        if Permission.compare(target, _target):
            BotUser(target, active=1)
            ACTIVE_USER.update({_target: "*"})
            return message("激活成功!").target(sender).send()
        return not_admin(sender)
    elif cmd.find("user.delete"):
        _target = cmd.query("qq").target if isinstance(cmd.query("qq"), At) else cmd.query("qq")
        if Permission.compare(target, _target):
            await BotUser(target, active=0).user_deactivate()
            if target in ACTIVE_USER:
                ACTIVE_USER.pop(target)
            return message("取消激活成功!").target(sender).send()
        return not_admin(sender)
    elif cmd.find("user.list"):
        msg = "用户白名单"
        if res := DBUser.select().where(DBUser.active == 1):
            friends = {i.id: i.nickname for i in await app.get_friend_list()}
            for qq in res:
                qq = int(qq.uid)
                msg += f"\n{friends[qq]}: {qq}" if qq in friends else f"\n未知用户昵称: {qq}"
        else:
            msg = "无激活用户"
        return message(msg).target(sender).send()


@command.parse("blacklist", permission=Permission.SUPER_ADMIN)
async def blacklist(target: Union[Friend, Member], sender: Union[Friend, Group], cmd: Arpamar):
    if cmd.find("blacklist.add"):
        _target = cmd.query("qq").target if isinstance(cmd.query("qq"), At) else cmd.query("qq")
        if Permission.compare(target, _target):
            await BotUser(_target).grant_level(0)
            BANNED_USER.append(_target)
            return message("禁用成功!").target(sender).send()
        return not_admin(sender)
    elif cmd.find("blacklist.delete"):
        _target = cmd.query("qq").target if isinstance(cmd.query("qq"), At) else cmd.query("qq")
        if Permission.compare(target, _target):
            await BotUser(_target).grant_level(1)
            if _target in BANNED_USER:
                BANNED_USER.remove(_target)
            return message("解除禁用成功!").target(sender).send()
        return not_admin(sender)
    elif cmd.find("blacklist.list"):
        res = DBUser.select().where(DBUser.level == 0)
        return message("\r\n".join(qq.uid for qq in res) if res else "无黑名单用户").target(sender).send()


@command.parse("group", permission=Permission.SUPER_ADMIN)
async def group(app: Ariadne, sender: Union[Friend, Group], cmd: Arpamar):
    if cmd.find("group.add"):
        BotGroup(cmd.query("group"), active=1)
        ACTIVE_GROUP.update({cmd.query("group"): "*"})
        return message("激活成功!").target(sender).send()
    elif cmd.find("group.delete"):
        await BotGroup(cmd.query("group"), active=0).group_deactivate()
        if cmd.find("group") in ACTIVE_GROUP:
            ACTIVE_GROUP.pop(cmd.query("group"))
        return message("禁用成功!").target(sender).send()
    elif cmd.find("group.list"):
        msg = "群组白名单"
        if res := DBGroup.select().where(DBGroup.active == 1):
            groups = {i.id: {"name": i.name, "perm": i.account_perm.value} for i in await app.get_group_list()}
            for group_id in res:
                group_id = int(group_id.uid)
                if group_id in groups:
                    msg += f"\n{groups[group_id]['name']}: {group_id} - {GROUP_PERM[groups[group_id]['perm']]}"
                else:
                    msg += f"\n未知群: {group_id} - 未加入该群"
        else:
            msg = "无白名单群组"
        return message(msg).target(sender).send()


@command.parse("grant")
async def grant(target: Union[Friend, Member], sender: Union[Friend, Group], cmd: Arpamar):
    if not Permission.manual(target, 3):
        return message("权限不足，爬!").target(sender).send()
    _target = cmd.query("qq").target if isinstance(cmd.query("qq"), At) else cmd.query("qq")
    level = grant["level"]
    if target.id == target and level != 4 and Permission.manual(target, 4):
        return message(f"怎么有master想给自己改权限呢？{Config.name}很担心你呢，快去脑科看看吧！").target(sender).send()
    if await BotUser(_target).level == 0:
        return message("在黑名单中的用户无法调整权限！若想调整其权限请先将其移出黑名单！").target(sender).send()
    if 1 <= level <= 2:
        if result := await BotUser(_target).level:
            if result == 4:
                if Permission.manual(target, 4):
                    return message("就算是master也不能修改master哦！（怎么能有两个master呢").target(sender).send()
                else:
                    return message("master level 不可更改！若想进行修改请直接修改配置文件！").target(sender).send()
            elif result == 3:
                if not Permission.manual(target, 4):
                    return (
                        message("权限不足，你必须达到等级4(master level)才可修改超级管理员权限！").target(sender).send()
                    )  # noqa: E501
                ADMIN_USER.remove(target)
                if level == 2:
                    GROUP_ADMIN_USER.append(target)
                return await grant_permission_process(_target, level, sender)
            elif result == 2:
                if level == 1:
                    GROUP_ADMIN_USER.remove(target)
                return await grant_permission_process(_target, level, sender)
            else:
                if level == 2:
                    GROUP_ADMIN_USER.append(target)
                return await grant_permission_process(_target, level, sender)
    elif level == 3:
        if not Permission.manual(target, 4):
            return message("权限不足，你必须达到等级4(master level)才可对超级管理员进行授权！").target(sender).send()
        if target in GROUP_ADMIN_USER:
            GROUP_ADMIN_USER.remove(_target)
        ADMIN_USER.append(target)
        return await grant_permission_process(_target, level, sender)
    else:
        return message("level值非法！level值范围: 1-3\r\n1: user\r\n2: admin\r\n3: super admin").target(sender).send()


async def grant_permission_process(user_id: int, new_level: int, sender: Union[Friend, Group]):
    """修改用户权限"""
    await BotUser(user_id).grant_level(new_level)
    return message(f"修改成功！\r\n{user_id} level: {new_level}").target(sender).send()
