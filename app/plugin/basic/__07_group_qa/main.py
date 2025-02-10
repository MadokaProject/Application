import json

from loguru import logger

from app.core.app import AppCore
from app.plugin.basic.__01_sys.database.database import Config as DBConfig
from app.util.alconna import Arpamar, Commander, Option, Subcommand
from app.util.control import Permission
from app.util.graia import (
    DefaultFunctionWaiter,
    Group,
    GroupMessage,
    Member,
    MessageChain,
    Source,
    message,
)
from app.util.online_config import get_config, save_config

mode = {"startswith": "头匹配", "endswith": "尾匹配", "arbitrary": "任意匹配", "regex": "正则匹配", "full": "完全匹配"}
command = Commander(
    "qa",
    "群问答",
    Subcommand("add", help_text="添加或修改"),
    Subcommand("remove", help_text="删除"),
    Subcommand("list", help_text="列出本群问答库"),
    Option("--startswith|-S", help_text="头匹配"),
    Option("--endswith|-E", help_text="尾匹配"),
    Option("--arbitrary|-A", help_text="任意匹配"),
    Option("--regex|-R", help_text="正则匹配"),
    Option("--fullmatch|-F", help_text="完全匹配（默认）"),
    help_text="群问答: 仅管理可用!",
)


@command.parse("add", events=[GroupMessage], permission=Permission.GROUP_ADMIN)
async def add_reply(target: Member, sender: Group, source: Source, cmd: Arpamar):
    async def answer(user: Member, group: Group, msg: MessageChain):
        if user.id == target.id and group.id == sender.id:
            return msg.display

    qa = await get_config("group_qa", sender) or []
    message("请在180秒内输入关键词, 若关键词一致则修改相关回答内容, 发送 #取消# 取消添加/修改").target(sender).quote(
        source
    ).send()
    keyword = await DefaultFunctionWaiter(answer, [GroupMessage]).wait(180, "TimeoutError")
    if keyword == "TimeoutError":
        return message("等待超时！").target(sender).send()
    elif keyword == "#取消#":
        return message("已取消！").target(sender).send()
    message("很好! 接下来请在180秒内输入回答消息, 发送 #取消# 取消添加/修改").target(sender).send()
    msg = await DefaultFunctionWaiter(answer, [GroupMessage]).wait(180, "TimeoutError")
    if msg == "TimeoutError":
        return message("等待超时！").target(sender).send()
    elif msg == "#取消#":
        return message("已取消！").target(sender).send()
    if cmd.find("startswith"):
        pattern = "head"
    elif cmd.find("endswith"):
        pattern = "tail"
    elif cmd.find("arbitrary"):
        pattern = "arbitrary"
    elif cmd.find("regex"):
        pattern = "regex"
    else:
        pattern = "full"
    for i in qa:
        if i["keyword"] == keyword:
            i["message"] = msg
            i["pattern"] = pattern
            await save_config("group_qa", sender, qa)
            return message("修改成功！").target(sender).send()
    qa.append({"keyword": keyword, "pattern": pattern, "message": msg})
    await save_config("group_qa", sender, qa)
    return message("添加成功！").target(sender).send()


@command.parse("remove", events=[GroupMessage], permission=Permission.GROUP_ADMIN)
async def remove_reply(target: Member, sender: Group, cmd: Arpamar):
    async def select_qa(user: Member, group: Group, msg: MessageChain):
        if user.id == target.id and group.id == sender.id:
            try:
                index = int(msg.display)
                return index - 1
            except ValueError:
                message("请输入对应序号！").target(sender).send()

    if res := await get_config("group_qa", sender):
        msg = "\n\n".join(
            f"序号：{index}\n关键词: {i['keyword']}\n匹配模式: {mode[i['pattern']]}" for index, i in enumerate(res, 1)
        )
    else:
        return message("该群组暂未配置！").target(sender).send()
    message(msg).target(sender).send()
    message("请在30秒内输入要删除的序号").target(sender).send()
    index = await DefaultFunctionWaiter(select_qa, [GroupMessage]).wait(30, "TimeoutError")
    if index == "TimeoutError":
        msg = "等待超时！"
    else:
        res.pop(index)
        await save_config("group_qa", sender, res)
        msg = "删除成功！"
    return message(msg).target(sender).send()


@command.parse("list", events=[GroupMessage], permission=Permission.GROUP_ADMIN)
async def list_reply(sender: Group):
    if res := await get_config("group_qa", sender):
        msg = "\n\n".join(
            f"序号：{index}\n关键词: {i['keyword']}\n匹配模式: {mode[i['pattern']]}" for index, i in enumerate(res, 1)
        )
    else:
        msg = "该群组暂未配置！"
    return message(msg).target(sender).send()


if DBConfig.select().where(DBConfig.name == "group_reply"):
    logger.info("检测到旧版群问答库，正在转换...")
    for _ in DBConfig.select().where(DBConfig.name == "group_reply"):
        group_qa = [{"keyword": k, "pattern": "full", "message": v} for k, v in json.loads(_.value).items()]
        DBConfig.replace(name="group_qa", uid=_.uid, value=json.dumps(group_qa, ensure_ascii=False)).execute()
    DBConfig.delete().where(DBConfig.name == "group_reply").execute()
    logger.success("转换成功！将重启以应用更改！")
    AppCore().restart("-r")
