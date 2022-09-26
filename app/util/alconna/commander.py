import traceback
from functools import wraps
from typing import Callable, Union

from arclet.alconna import Alconna, Args, Arpamar, CommandMeta, Option, Subcommand
from loguru import logger

from app.util.control import Permission
from app.util.decorator import ArgsAssigner
from app.util.graia import (
    Ariadne,
    Friend,
    FriendMessage,
    Group,
    GroupMessage,
    InterruptControl,
    Member,
    MessageChain,
    MessageEvent,
    Source,
    Stranger,
    StrangerMessage,
    TempMessage,
)
from app.util.phrases import print_help, unknown_error


class Commander:
    """对 Alconna 进行部分封装，简化命令的注册过程。

    Typical usage example:
    >>> from app.util.alconna import Commander, Subcommand, Arpamar
    >>> from app.util.graia import GroupMessage
    >>> command = Commander(
            "test",
            "测试",
            Subcommand("test1", help_text="test1"),
            Subcommand("test2", help_text="test2")
        )
    >>>
    >>> @command.parse("test1")
    >>> async def test1(result: Arpamar, *args, **kwargs):
    >>>    pass
    >>>
    >>> @command.parse("test2", events=[GroupMessage])
    >>> async def test2(result: Arpamar, *args, **kwargs):
    >>>    pass
    """

    TypeMessage = {
        FriendMessage: Friend,
        GroupMessage: Group,
        TempMessage: Member,
        StrangerMessage: Stranger,
    }

    def __init__(
        self,
        entry,
        brief_help: str,
        *args: Union[Args, Option, Subcommand],
        help_text: str = None,
        enable: bool = True,
        hidden: bool = False,
        **kwargs,
    ):
        """创建一个命令

        :param entry: 主命令
        :param brief_help: 简短帮助信息
        :param args: 命令选项
        :param help_text: 帮助信息，默认为 brief_help
        :param enable: 插件开关，默认开启
        :param hidden: 隐藏插件，默认不隐藏
        """
        self.entry = entry
        self.brief_help = brief_help
        self.help_text = help_text or brief_help
        self.enable = enable
        self.hidden = hidden
        self.alconna = Alconna(entry, *args, meta=CommandMeta(self.help_text), **kwargs)
        self.module_name = ".".join(traceback.extract_stack()[-2][0].strip(".py").split("/")[-5:])
        self.options: dict[str, Callable] = {}
        self.no_match_action: Callable = None
        from app.core.commander import CommandDelegateManager

        manager: CommandDelegateManager = CommandDelegateManager()

        @manager.register(self.entry, self.brief_help, self.alconna, self.enable, self.hidden, self.module_name)
        async def process(
            app: Ariadne,
            message: MessageChain,
            target: Union[Friend, Member],
            sender: Union[Friend, Group],
            source: Source,
            inc: InterruptControl,
            result: Arpamar,
        ):
            try:
                for name, func in self.options.items():
                    if result.find(name):
                        return await func(sender, app, message, target, sender, source, inc, result)
                if self.no_match_action:
                    return await self.no_match_action(sender, app, message, target, sender, source, inc, result)
                await print_help(sender, self.alconna.get_help())
            except Exception as e:
                logger.exception(e)
                return unknown_error(sender)

    def __filter(self, events: tuple):
        """事件过滤器"""

        def wrapper(func: Callable):
            @wraps(func)
            def inner(sender, *args, **kwargs):
                if isinstance(sender, events):
                    return func(*args, **kwargs)

            return inner

        return wrapper

    def no_match(self, /, events: list[MessageEvent] = [], permission: int = Permission.DEFAULT):
        """无匹配子命令时的回调函数

        :param events: 事件过滤器，默认不过滤
        :param permission: 鉴权，默认允许非黑名单外所有用户
        """

        def wrapper(func):
            @self.__filter(
                tuple(
                    [self.TypeMessage[event] for event in events if event in self.TypeMessage]
                    or self.TypeMessage.values()
                )
            )
            @Permission.require(permission)
            @ArgsAssigner
            @wraps(func)
            def inner(*args, **kwargs):
                return func(*args, **kwargs)

            self.no_match_action = inner
            return inner

        return wrapper

    def parse(
        self, name: Union[str, list[str]], /, events: list[MessageEvent] = [], permission: int = Permission.DEFAULT
    ):
        """子命令匹配器

        :param name: 需要匹配的子命令
        :param events: 事件过滤器，默认不过滤
        :param permission: 鉴权，默认允许非黑名单外所有用户
        """
        names = name if isinstance(name, list) else [name]

        def wrapper(func):
            @self.__filter(
                tuple(
                    [self.TypeMessage[event] for event in events if event in self.TypeMessage]
                    or self.TypeMessage.values()
                )
            )
            @Permission.require(permission)
            @ArgsAssigner
            @wraps(func)
            def inner(*args, **kwargs):
                return func(*args, **kwargs)

            for name in names:
                self.options[name] = inner
            return inner

        return wrapper
