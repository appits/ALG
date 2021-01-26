# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.


from odoo import api,fields,models,_
import datetime

class RefuseReasonWizard(models.TransientModel):
    _name="refuse.reason.wizard"
    _description="Refuse Reason Wizard"
 
    sh_refuse_reason_id = fields.Many2one("sh.so.refuse.reason",string="Refuse Reason",required=True,help="This field display a list of reasons for refusing sale order")
    sh_refuse_comment = fields.Text(string="Comment")

    def refuse_order(self):
        if self:
            for data in self:
                if data.env.context.get('active_model') == 'sale.order':
                    active_model_id = data.env.context.get('active_id')
                    sale_obj = data.env['sale.order'].search([('id','=',active_model_id)])
                    sale_obj.write({
                            'sh_refuse_by': data.env.user.id,
                            'sh_refuse_reason':data.sh_refuse_reason_id.name + "\n" + data.sh_refuse_comment,
                            'state':'refuse',
                            'sh_refuse_time': datetime.datetime.now()
                    })
