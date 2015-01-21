# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright :
#        (c) 2014 Antiun Ingenieria, SL (Madrid, Spain, http://www.antiun.com)
#                 Endika Iglesias <endikaig@antiun.com>
#                 Antonio Espinosa <antonioea@antiun.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import orm, fields
import datetime
from openerp.tools.config import config
import mandrill
import datetime


class mandrill_outbound(orm.Model):
    _name = "mandrill.outbound"
    _description = "Mandrill Outbound"
    _columns = {
        'name': fields.char("Subject email", size=200, readonly=True,
                            required=True),
        'email_id': fields.char("Mandrill internal id", size=200,
                                readonly=True,
                                required=True),
        'opens': fields.integer("Opens", size=10, default=0, readonly=True,
                                required=True),
        'clicks': fields.integer("Clicks", size=10, default=0, readonly=True,
                                 required=True),
        'from': fields.char("From", size=200, readonly=True, required=False),
        'to': fields.char("To", size=1000, readonly=True, required=False),
        'state': fields.char("State", size=50, readonly=True, required=False),
        'date': fields.datetime('Register date', readonly=True, required=True),
        'content': fields.char("Content", size=5000, readonly=True,
                               required=False),
    }

    def _api_key(self, cr, uid, ids, context=None):
        config_pool = self.pool.get('ir.config_parameter')
        api_key = config_pool.get_param(cr,
                                        uid,
                                        'mandrill_integration.api_key',
                                        default=False,
                                        context=context)
        if api_key is False or len(api_key) <= 0:
            return False
        return api_key

    def call_cron_mandrill_outbound(self, cr, uid, context=None):
        api_key = self._api_key(cr, uid, [],
                                context=context)
        if api_key is False:
            return False

        mandrill_out = self.pool['mandrill.outbound']
        date_now = datetime.datetime.now().strftime("%Y-%m-%d")
        year_now = datetime.datetime.now().strftime("%Y")
        date_rest = datetime.datetime.now().strftime("-%m-%d")
        date_init = str(int(year_now)-1) + date_rest
        mandrill_client = mandrill.Mandrill(api_key)
        result = mandrill_client.messages.search(query='*',
                                                 date_from=date_init,
                                                 date_to=date_now)
        masc = "%Y-%m-%d %H:%M:%S"
        date_now = datetime.datetime.now().strftime(masc)

        for email in result:
            mandrill_ids = mandrill_out.search(cr, uid,
                                               [('email_id', '=', email['_id'])
                                                ], context=context)
            try:
                result_cont = mandrill_client.messages.content(id=email['_id'])
                content = result_cont['text']
            except mandrill.Error, e:
                content = "No available"

            opens = int(email['opens'])
            clicks = int(email['clicks'])
            mandrill_map = {"name": email['subject'],
                            "email_id": email['_id'],
                            "opens": opens if opens > 0 else 0,
                            "clicks": clicks if clicks > 0 else 0,
                            "from": email['sender'],
                            "to": email['email'],
                            "state": email['state'],
                            "date": date_now,
                            "content": content,
                            }

            if not mandrill_ids:
                mandrill_out.create(cr, uid,
                                    mandrill_map,
                                    context=context)
                continue

            del mandrill_map['date']
            mandrill_out.write(cr, uid, mandrill_ids,
                               mandrill_map,
                               context=context)
