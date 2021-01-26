from odoo import fields, models, api


class product_product(models.Model):
    _inherit = 'product.product'

    p_cost_ids = fields.One2many('product.cost', 'product_id')


class product_template(models.Model):
    _inherit = 'product.template'

    p_cost_ids = fields.One2many('product.cost', 'product_tmp_id')

    @api.model
    def calc_current_cost(self, product_id):
        schema = self.env['acct.schema'].search([('company_id', '=', self.env.user.company_id.id)])
        for schema_conf in schema:
            data_report = schema_conf.env['fact.acct'].search(
                [('product_id.product_tmpl_id.id', '=', product_id), ('type', '=', 'entry'),
                 ('schema_id', '=', schema_conf.id), ('debit', '>', 0), ('state', '=', 'posted')])
            amount = 0
            qty = 0
            for data in data_report:
                if data.quantity < 0:
                    amount_journal = data.debit * -1
                else:
                    amount_journal = data.debit

                amount += amount_journal
                qty += data.quantity

            if amount != 0 and qty != 0:
                current_cost = (amount / qty)
            else:
                current_cost = 0

            if current_cost != 0:
                data_cost = schema_conf.env['product.cost'].search(
                    [('product_tmp_id.id', '=', product_id), ('schema_id.id', '=', schema_conf.id)])
                if data_cost:
                    data_cost.accumulated_amount = amount
                    data_cost.accumulated_qty = qty
                    data_cost.current_cost = current_cost
                else:
                    product = self.env['product.product'].search([('product_tmpl_id.id', '=', product_id)])

                    self.env['product.cost'].create({'product_tmp_id': product_id,
                                                     'product_id': product.id,
                                                     'schema_id': schema_conf.id,
                                                     'accumulated_amount': amount,
                                                     'accumulated_qty': qty,
                                                     'current_cost': current_cost,
                                                     })


class ProductCost(models.Model):
    _name = 'product.cost'
    _description = 'Storage Product Cost'

    product_id = fields.Many2one('product.product')
    product_tmp_id = fields.Many2one('product.template')
    schema_id = fields.Many2one('acct.schema')
    accumulated_amount = fields.Float()
    accumulated_qty = fields.Float()
    current_cost = fields.Float()
