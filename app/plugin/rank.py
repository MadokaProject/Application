from prettytable import PrettyTable
from graia.application import MessageChain
from graia.application.message.elements.internal import Image_UnsafeBytes, Plain

from app.plugin.base import Plugin
from app.util.dao import MysqlDao
from app.util.text2image import create_image
from app.util.tools import isstartswith


class Rank(Plugin):
    entry = ['.rank', '.排行']
    brief_help = '\r\n▶排行：rank'
    full_help = \
        '.排行/.rank\t可以查询各类榜单。\r\n' \
        '.排行/.rank 发言榜/msg\t显示群内成员发言排行榜'

    async def process(self):
        if not self.msg:
            self.print_help()
            return
        if isstartswith(self.msg[0], ['发言榜', 'msg']):
            """发言榜"""
            try:
                with MysqlDao() as db:
                    res = db.query(
                        "SELECT qid, count(qid) FROM msg WHERE uid=%s GROUP BY qid ORDER BY count(qid) DESC", [self.group.id]
                    )
                    members = await self.app.memberList(self.group.id)
                    group_user = {item.id: item.name for item in members}
                    self.resp = MessageChain.create([Plain('群内发言排行：\r\n')])
                    msg = PrettyTable()
                    msg.field_names = ['序号', '群昵称', '发言条数']
                    for index, (qid, num) in enumerate(res):
                        if int(qid) not in group_user.keys():
                            continue
                        msg.add_row([index + 1, group_user[int(qid)], num])
                    msg.align = 'r'
                    msg.align['群昵称'] = 'l'
                    self.resp.plus(
                        MessageChain.create([
                            Image_UnsafeBytes((await create_image(msg.get_string())).getvalue())
                        ])
                    )
            except Exception as e:
                print(e)
                self.unkown_error()
        else:
            self.args_error()
