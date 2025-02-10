"""对Ariadne 相关功能进行封装"""

from graia.ariadne import Ariadne as Ariadne
from graia.ariadne.event.message import ActiveFriendMessage as ActiveFriendMessage
from graia.ariadne.event.message import ActiveGroupMessage as ActiveGroupMessage
from graia.ariadne.event.message import ActiveMessage as ActiveMessage
from graia.ariadne.event.message import ActiveStrangerMessage as ActiveStrangerMessage
from graia.ariadne.event.message import ActiveTempMessage as ActiveTempMessage
from graia.ariadne.event.message import FriendMessage as FriendMessage
from graia.ariadne.event.message import GroupMessage as GroupMessage
from graia.ariadne.event.message import MessageEvent as MessageEvent
from graia.ariadne.event.message import StrangerMessage as StrangerMessage
from graia.ariadne.event.message import TempMessage as TempMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import App as App
from graia.ariadne.message.element import At as At
from graia.ariadne.message.element import AtAll as AtAll
from graia.ariadne.message.element import Dice as Dice
from graia.ariadne.message.element import Face as Face
from graia.ariadne.message.element import File as File
from graia.ariadne.message.element import FlashImage as FlashImage
from graia.ariadne.message.element import Forward as Forward
from graia.ariadne.message.element import ForwardNode as ForwardNode
from graia.ariadne.message.element import Image as Image
from graia.ariadne.message.element import ImageType as ImageType
from graia.ariadne.message.element import Json as Json
from graia.ariadne.message.element import MarketFace as MarketFace
from graia.ariadne.message.element import MusicShare as MusicShare
from graia.ariadne.message.element import MusicShareKind as MusicShareKind
from graia.ariadne.message.element import Plain as Plain
from graia.ariadne.message.element import Poke as Poke
from graia.ariadne.message.element import PokeMethods as PokeMethods
from graia.ariadne.message.element import Quote as Quote
from graia.ariadne.message.element import Source as Source
from graia.ariadne.message.element import Voice as Voice
from graia.ariadne.message.element import Xml as Xml
from graia.ariadne.model import Announcement as Announcement
from graia.ariadne.model import DownloadInfo as DownloadInfo
from graia.ariadne.model import FileInfo as FileInfo
from graia.ariadne.model import Friend as Friend
from graia.ariadne.model import Group as Group
from graia.ariadne.model import GroupConfig as GroupConfig
from graia.ariadne.model import Member as Member
from graia.ariadne.model import MemberInfo as MemberInfo
from graia.ariadne.model import MemberPerm as MemberPerm
from graia.ariadne.model import Profile as Profile
from graia.ariadne.model import Stranger as Stranger
from graia.ariadne.util.interrupt import FunctionWaiter as DefaultFunctionWaiter
from graia.broadcast.interrupt import InterruptControl as InterruptControl
from graia.broadcast.interrupt.waiter import Waiter as Waiter
from graia.scheduler import GraiaScheduler as GraiaScheduler
from graia.scheduler import timers as timers

from .message import Message
from .tools import MadokaFunctionWaiter as FunctionWaiter

message = Message
__all__ = [
    "message",
    "FunctionWaiter",
    "Ariadne",
    "ActiveFriendMessage",
    "ActiveGroupMessage",
    "ActiveMessage",
    "ActiveStrangerMessage",
    "ActiveTempMessage",
    "FriendMessage",
    "GroupMessage",
    "MessageEvent",
    "StrangerMessage",
    "TempMessage",
    "MessageChain",
    "App",
    "At",
    "AtAll",
    "Dice",
    "Face",
    "File",
    "FlashImage",
    "Forward",
    "ForwardNode",
    "Image",
    "ImageType",
    "Json",
    "MarketFace",
    "MusicShare",
    "MusicShareKind",
    "Plain",
    "Poke",
    "PokeMethods",
    "Quote",
    "Source",
    "Voice",
    "Xml",
    "Announcement",
    "DownloadInfo",
    "FileInfo",
    "Friend",
    "Group",
    "GroupConfig",
    "Member",
    "MemberInfo",
    "MemberPerm",
    "Profile",
    "Stranger",
    "DefaultFunctionWaiter",
    "InterruptControl",
    "Waiter",
    "GraiaScheduler",
    "timers",
]
