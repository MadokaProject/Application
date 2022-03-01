from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, At
from loguru import logger

from app.core.settings import *
from app.entities.group import BotGroup
from app.entities.user import BotUser
from app.plugin.base import Plugin, InitDB
from app.util.control import Permission
from app.util.dao import MysqlDao
from app.util.decorator import permission_required
from app.util.tools import isstartswith


class Module(Plugin):
    entry = ['.perm', '.授权']
    brief_help = '授权'
    full_help = {
        '仅管理以上可用!': '',
        'au': {
            '激活用户(激活后用户可私聊使用)': '',
            '[@user]': '@群成员 或 私聊发送QQ号码'
        },
        'du': {
            '取消激活用户': '',
            '[@user]': '@群成员 或 私聊发送QQ号码'
        },
        'ab': {
            '加入黑名单': '',
            '[@user]': '@群成员 或 私聊发送QQ号码'
        },
        'db': {
            '移出黑名单': '',
            '[@user]': '@群成员 或 私聊发送QQ号码'
        },
        'ag': {
            '激活群组': '',
            '[group_id]': '群号码'
        },
        'dg': {
            '禁用群组': '',
            '[group_id]': '群号码'
        },
        'al': '查看用户白名单',
        'bl': '查看用户黑名单',
        'gl': '查看群组白名单',
        'grant': {
            '调整用户权限等级': '',
            '[@user]': '@群成员',
            '[1-3]': '权限等级',
            'level 1: 普通用户': '',
            'level 2: 管理员, 与群管理同级别, 能额外触发群管理命令': '',
            'level 3: 超级管理员, 能触发除机器人系统控制外所有命令': '',
            '群管理默认为 level 2,且无法降级为level 1': ''
        }
    }

    async def process(self):
        if not self.msg:
            await self.print_help()
            return
        try:
            if isstartswith(self.msg[0], ['au', 'du', 'ab', 'db', 'ag', 'dg', 'ul', 'bl', 'gl']):
                if isstartswith(self.msg[0], ['au', 'du', 'ab', 'db', 'ag', 'dg']):
                    if hasattr(self, 'group') and not self.message.has(At):
                        self.args_error()
                        return
                await self.master_grant()
            elif isstartswith(self.msg[0], ['grant']):
                if hasattr(self, 'group') and not self.message.has(At):
                    self.args_error()
                    return
                if Permission.require(self.member if hasattr(self, 'group') else self.friend, 3):
                    assert len(self.msg) == 3 and self.msg[2].isdigit()
                    user = self.member if hasattr(self, 'group') else self.friend
                    target = int(self.msg[1]) if hasattr(self, 'friend') else self.message.getFirst(At).target
                    level = int(self.msg[2])
                    if user.id == target and level != 4 and Permission.require(user, 4):
                        self.resp = MessageChain.create([Plain(f'怎么有master想给自己改权限呢？{Config().BOT_NAME}很担心你呢，快去脑科看看吧！')])
                        return
                    if await BotUser(target).get_level() == 0:
                        self.resp = MessageChain.create([Plain('在黑名单中的用户无法调整权限！若想调整其权限请先将其移出黑名单！')])
                        return
                    if 1 <= level <= 2:
                        if result := await BotUser(target).get_level():
                            if result == 4:
                                if Permission.require(user, 4):
                                    self.resp = MessageChain.create([Plain('就算是master也不能修改master哦！（怎么能有两个master呢')])
                                else:
                                    self.resp = MessageChain.create([Plain('master level 不可更改！若想进行修改请直接修改配置文件！')])
                            elif result == 3:
                                if Permission.require(user, 4):
                                    await self.grant_permission_process(target, level)
                                    ADMIN_USER.remove(target)
                                    if level == 2:
                                        GROUP_ADMIN_USER.append(target)
                                else:
                                    self.resp = MessageChain.create([Plain("权限不足，你必须达到等级4(master level)才可修改超级管理员权限！")])
                            elif result == 2:
                                await self.grant_permission_process(target, level)
                                if level == 1:
                                    GROUP_ADMIN_USER.remove(target)
                            else:
                                await self.grant_permission_process(target, level)
                                if level == 2:
                                    GROUP_ADMIN_USER.append(target)
                    elif level == 3:
                        if Permission.require(user, 4):
                            await self.grant_permission_process(target, level)
                            if target in GROUP_ADMIN_USER:
                                GROUP_ADMIN_USER.remove(target)
                            ADMIN_USER.append(target)
                        else:
                            self.resp = MessageChain.create([Plain('权限不足，你必须达到等级4(master level)才可对超级管理员进行授权！')])
                    else:
                        self.resp = MessageChain.create([
                            Plain('level值非法！level值范围: 1-3\r\n1: user\r\n2: admin\r\n3: super admin')
                        ])
                else:
                    self.resp = MessageChain.create([Plain('权限不足，爬!')])
            else:
                self.args_error()
                return
        except AssertionError:
            self.args_error()
        except Exception as e:
            logger.exception(e)
            self.unkown_error()

    @permission_required(level=Permission.SUPER_ADMIN)
    async def master_grant(self):
        if isstartswith(self.msg[0], 'au'):
            assert len(self.msg) == 2
            target = int(self.msg[1]) if hasattr(self, 'friend') else self.message.getFirst(At).target
            if Permission.compare(self.member if hasattr(self, 'group') else self.friend, target):
                BotUser(target, active=1)
                self.resp = MessageChain.create([Plain('激活成功！')])
                ACTIVE_USER.update({target: '*'})
            else:
                self.not_admin()
        elif isstartswith(self.msg[0], 'du'):
            assert len(self.msg) == 2
            target = int(self.msg[1]) if hasattr(self, 'friend') else self.message.getFirst(At).target
            if Permission.compare(self.member if hasattr(self, 'group') else self.friend, target):
                await BotUser(target, active=0).user_deactivate()
                self.resp = MessageChain.create([Plain('取消激活成功！')])
                if target in ACTIVE_USER:
                    ACTIVE_USER.pop(target)
            else:
                self.not_admin()
        elif isstartswith(self.msg[0], 'ab'):
            assert len(self.msg) == 2
            target = int(self.msg[1]) if hasattr(self, 'friend') else self.message.getFirst(At).target
            if Permission.compare(self.member if hasattr(self, 'group') else self.friend, target):
                await BotUser(target).grant_level(0)
                self.resp = MessageChain.create([Plain('禁用成功！')])
                BANNED_USER.append(target)
            else:
                self.not_admin()
        elif isstartswith(self.msg[0], 'db'):
            assert len(self.msg) == 2
            target = int(self.msg[1]) if hasattr(self, 'friend') else self.message.getFirst(At).target
            if Permission.compare(self.member if hasattr(self, 'group') else self.friend, target):
                await BotUser(target).grant_level(1)
                self.resp = MessageChain.create([Plain('解除禁用成功！')])
                if target in BANNED_USER:
                    BANNED_USER.remove(target)
            else:
                self.not_admin()
        elif isstartswith(self.msg[0], 'ag'):
            assert len(self.msg) == 2 and self.msg[1].isdigit()
            BotGroup(int(self.msg[1]), active=1)
            self.resp = MessageChain.create([Plain('激活成功！')])
            ACTIVE_GROUP.update({int(self.msg[1]): '*'})
        elif isstartswith(self.msg[0], 'dg'):
            assert len(self.msg) == 2 and self.msg[1].isdigit()
            await BotGroup(int(self.msg[1]), active=0).group_deactivate()
            self.resp = MessageChain.create([Plain('禁用成功！')])
            if int(self.msg[1]) in ACTIVE_GROUP:
                ACTIVE_GROUP.pop(int(self.msg[1]))
        elif isstartswith(self.msg[0], 'ul'):
            with MysqlDao() as db:
                res = db.query("SELECT uid FROM user WHERE active=1")
                self.resp = MessageChain.create([Plain('\r\n'.join([f'{qq[0]}' for qq in res]) if res else '无激活用户')])
        elif isstartswith(self.msg[0], 'bl'):
            with MysqlDao() as db:
                res = db.query("SELECT uid FROM user WHERE level=0")
            self.resp = MessageChain.create([Plain('\r\n'.join([f'{qq[0]}' for qq in res]) if res else '无黑名单用户')])
        elif isstartswith(self.msg[0], 'gl'):
            with MysqlDao() as db:
                res = db.query("SELECT uid FROM `group` WHERE active=1")
            self.resp = MessageChain.create(
                [Plain('\r\n'.join([f'{group_id[0]}' for group_id in res]) if res else '无激活群组')])

    async def grant_permission_process(self, user_id: int, new_level: int) -> None:
        """修改用户权限"""
        await BotUser(user_id).grant_level(new_level)
        self.resp = MessageChain.create([Plain(f'修改成功！\r\n{user_id} level: {new_level}')])


class DB(InitDB):

    async def process(self):
        with MysqlDao() as _db:
            _db.update(
                "create table if not exists user( \
                    id int auto_increment comment '序号' primary key, \
                    uid char(12) null comment 'QQ', \
                    permission varchar(512) default '*' not null comment '许可', \
                    active int not null comment '状态', \
                    level int default 1 not null comment '权限', \
                    points int default 0 null comment '货币', \
                    signin_points int default 0 null comment '签到货币', \
                    english_answer int default 0 null comment '英语答题榜', \
                    last_login date comment '最后登陆')"
            )
            _db.update(
                "create table if not exists `group`( \
                    id int auto_increment comment '序号' primary key, \
                    uid char(12) null comment '群号', \
                    permission varchar(512) not null comment '许可', \
                    active int not null comment '状态')"
            )
