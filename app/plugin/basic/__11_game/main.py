import random
from textwrap import fill
from typing import Union

from loguru import logger
from prettytable import PrettyTable

from app.core.app import AppCore
from app.core.config import Config
from app.entities.game import BotGame
from app.util.alconna import Args, Arpamar, Commander, Option
from app.util.graia import (
    Ariadne,
    At,
    Friend,
    GraiaScheduler,
    Group,
    Image,
    Member,
    MessageChain,
    Plain,
    message,
    timers,
)
from app.util.phrases import args_error, point_not_enough
from app.util.text2image import create_image
from app.util.tools import to_thread

from .database.database import Game as DBGame
from .sign_image_generator import get_sign_image

core: AppCore = AppCore()
app: Ariadne = core.get_app()
sche: GraiaScheduler = core.get_scheduler()


command = Commander(
    "gp",
    "经济系统",
    Option("signin", help_text="每日签到"),
    Option("get", help_text="获取今日签到图"),
    Option("tf", help_text="转账", args=Args["at", At]["money", int]),
    Option("rank", help_text="显示群内已注册成员资金排行榜"),
    Option("auto", args=Args["status", bool], help_text="每天消耗10%金币自动签到"),
)


@command.no_match()
async def no_match(target: Union[Friend, Member], sender: Union[Friend, Group]):
    """查询资金"""
    user = BotGame(target.id)
    coin = await user.coins
    if isinstance(sender, Group):
        return message([At(target), Plain(f" 你的{Config.coin_settings.name}为%d!" % int(coin))]).target(sender).send()
    else:
        return message([Plain(f" 你的{Config.coin_settings.name}为%d!" % int(coin))]).target(sender).send()


@command.parse("signin")
async def signin(target: Union[Friend, Member], sender: Union[Friend, Group]):
    """签到"""
    coin = random.randint(1, 101)
    qq = target.id
    name = target.name if isinstance(target, Member) else target.nickname
    user = BotGame(qq, coin)
    if await user.is_signin:
        return (
            message([At(target), Plain(" 你今天已经签到过了！")]).target(sender).send()
            if isinstance(sender, Group)
            else message([Plain(" 你今天已经签到过了！")]).target(sender).send()
        )

    await user.sign_in()
    sign_image = await to_thread(
        get_sign_image,
        await user.uuid,
        qq,
        name,
        coin,
        await user.intimacy,
        await user.intimacy_level,
        await user.consecutive_days,
        await user.total_days,
    )
    return message([Image(data_bytes=sign_image)]).target(sender).send()


@command.parse("get")
async def get(target: Union[Friend, Member], sender: Union[Friend, Group]):
    """获取今日签到图"""
    qq = target.id
    name = target.name if isinstance(target, Member) else target.nickname
    user = BotGame(qq)
    if not await user.is_signin:
        if isinstance(sender, Group):
            return message([At(target), Plain(" 你今天还没有签到哦！")]).target(sender).send()
        else:
            return message("你今天还没有签到哦！").target(sender).send()
    sign_image = await to_thread(
        get_sign_image,
        await user.uuid,
        qq,
        name,
        await user.today_coin,
        await user.intimacy,
        await user.intimacy_level,
        await user.consecutive_days,
        await user.total_days,
    )
    return message([Image(data_bytes=sign_image)]).target(sender).send()


@command.parse("tf")
async def tf(target: Union[Friend, Member], sender: Union[Friend, Group], cmd: Arpamar):
    tf_target = cmd.query("at").target
    coin = cmd.query("money")
    if coin <= 0:
        return args_error(sender)
    user = BotGame(target.id)
    if await user.coins < coin:
        return point_not_enough(sender)
    await user.update_coin(-coin)
    user = BotGame(tf_target, coin)
    await user.update_coin(coin)
    return (
        message(
            [
                At(target),
                Plain(" 已转赠给"),
                At(tf_target),
                Plain(f" %d{Config.coin_settings.name}!" % coin),
            ]
        )
        .target(sender)
        .send()
    )


@command.parse("rank")
async def rank(target: Union[Friend, Member], sender: Union[Friend, Group]):
    group_user = {item.id: item.name for item in await app.get_member_list(sender)}
    resp = MessageChain([Plain(f"群内{Config.coin_settings.name}排行:\n")])
    user = target.id
    index = 1
    msg = PrettyTable()
    msg.field_names = ["序号", "群昵称", f"{Config.coin_settings.name}"]
    _user_rank = []
    for res in DBGame.select().order_by(DBGame.coins.desc()):
        if user == int(res.qid):
            _user_rank = [
                index,
                fill(group_user[int(res.qid)], width=20),
                res.coins,
            ]
        if res.coins == 0 or int(res.qid) not in group_user.keys():
            continue
        if index <= 30:
            msg.add_row([index, fill(group_user[int(res.qid)], width=20), res.coins])
        if index > 30 and _user_rank:
            msg.add_row(["====", "".join("=" for _ in range(40)), "====="])
            msg.add_row(_user_rank)
            break
        index += 1
    msg.align = "r"
    msg.align["群昵称"] = "l"
    resp.extend(MessageChain([Image(data_bytes=await create_image(msg.get_string()))]))
    return message(resp).target(sender).send()


@command.parse("auto")
async def auto(target: Union[Friend, Member], sender: Union[Friend, Group], cmd: Arpamar):
    await BotGame(target.id).auto_signin(cmd.query("status"))
    return (
        message("开启成功，将于每日 8 点为您自动签到！" if cmd.query("status") else "关闭成功！").target(sender).send()
    )  # noqa: E501


@sche.schedule(timers.crontabify("0 7 * * * 0"))
async def auto_sing():
    logger.info("auto signin is running...")
    for res in DBGame.select().where(DBGame.auto_signin == 1):
        user = BotGame(res.qid, coin := random.randint(1, 101))
        if not await user.is_signin:
            consume = random.randint(0, int(coin * 0.3))
            if await user.reduce_coin(consume):
                await user.sign_in()
                logger.success(f"账号: {res.qid} 自动签到完成~")
                message(f"今日份签到完成，消耗{consume}金币\n请发送.gp get查收").target(res.qid).send()
            else:
                message("您的金币不足，无法完成自动签到").target(res.qid).send()


@sche.schedule(timers.crontabify("59 23 * * * 50"))
async def tasks():
    sign_info = await BotGame.count()
    total_rent = await BotGame.ladder_rent_collection()
    message(
        [
            Plain(f"签到统计成功，昨日共有 {sign_info[0]} / {sign_info[1]} 人完成了签到，"),
            Plain(f"签到率为 {f'{sign_info[0] / sign_info[1]:.2%}'}\n"),
            Plain(f"今日收取了 {total_rent} {Config.coin_settings.name}"),
        ]
    ).target(Config.master_qq).send()
