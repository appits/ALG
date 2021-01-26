from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    quotation_ids = fields.One2many('quotation', 'sale_order_id', ondelete="cascade")
    rate_bcv = fields.Float()
    date_bcv = fields.Datetime()
    rate = fields.Float()
    date_rate = fields.Datetime()
    difference = fields.Float()
    variation_percent = fields.Float()
    percent_company = fields.Float()
    percent_partner = fields.Float()

    @api.onchange('partner_id')
    def set_values_of_currency(self):
        if self.company_id.currency_from_id and self.company_id.currency_to_id and self.partner_id:
            date_from, rate_from = self.company_id.get_rate(self.company_id.currency_from_id.id)
            date_to, rate_to = self.company_id.get_rate(self.company_id.currency_to_id.id)
            if date_from and rate_from > 0 and date_to and rate_to > 0:
                self.rate_bcv = rate_from
                self.date_bcv = date_from
                self.rate = rate_to
                self.date_rate = date_to
                self.difference = rate_to - rate_from
                self.variation_percent = ((rate_to - rate_from) / rate_to) * 100
                self.percent_company = self.company_id.percent_max_variation
                self.percent_partner = self.partner_id.percent_additional

        if self.variation_percent > self.percent_company:
            message = _(
                'El porcentaje de variacion entre tasas en mayor al establecido por la empresa, el sistema no te permitira cotizar, el porcentaje del dia es: %s y el porcentaje permitido es: %s' % (
                    str(self.variation_percent), str(self.percent_company)))
            mess = {'title': _('Advertencia de Tasas!'),
                    'message': message
                    }
            return {'warning': mess}

    @api.constrains('partner_id')
    def return_save_order(self):
        if self.variation_percent > self.percent_company and self.state:
            raise ValidationError(_(
                'El porcentaje de variacion entre tasas en mayor al establecido por la empresa, el sistema no te permitira cotizar, el porcentaje del dia es: %s y el porcentaje permitido es: %s' % (
                    str(self.variation_percent), str(self.percent_company))))

    def action_confirm(self):
        for lines in self.quotation_ids:
            lines.processed = True
        res = super(SaleOrder, self).action_confirm()
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    quotation_ids = fields.One2many('quotation', 'sale_order_line_id', ondelete="cascade")
    is_bom = fields.Boolean(default=False)

    @api.onchange('product_id')
    def set_bom(self):
        for lines in self:
            if lines.product_id and lines.product_id.bom_ids:
                lines.is_bom = True

    @api.constrains('product_id')
    def set_values_of_boms(self):
        for lines in self:
            if lines.product_id and lines.product_id.bom_ids:
                bom = lines.env['mrp.bom'].search(
                    [('product_tmpl_id', '=', lines.product_id.product_tmpl_id.id), ('list_for_quotation', '=', True)])
                if not bom:
                    raise ValidationError(_(
                        'The selected product does not contain a list of materials for quotation, please set up a list to follow the process, the product is: %s' % str(
                            lines.product_id.name)))
                if bom.product_qty == 0:
                    raise ValidationError(_(
                        'The quantity to be produced from the bill of materials cannot be equal to zero, the product is: %s' + lines.product_id.name))

                quotation = lines.env['quotation'].create({'sale_order_id': lines.order_id.id,
                                                           'sale_order_line_id': lines.id,
                                                           'product_id': lines.product_id.id,
                                                           'percent_gain': lines.order_id.partner_id.percent_margin,
                                                           'dollar_k': lines.order_id.partner_id.margin_amount,
                                                           'qty_bom': bom.product_qty,
                                                           'percent_partner_additional': lines.order_id.partner_id.percent_additional,
                                                           'base_calculation': lines.order_id.partner_id.base_calculation,
                                                           })

                price_quo = lines.create_and_update_lines_quotation(bom, quotation)
                lines.price_unit = price_quo

    def call_wizard(self):
        if self.product_id and self.product_id.bom_ids:
            target_product_form = self.env.ref('quotation_lanta.action_quotation_calc')
            new = self.env['quotation'].search(
                [('sale_order_line_id', '=', self.id), ('sale_order_id', '=', self.order_id.id)])
            if new:
                return {
                    'name': 'Quotation Calc',
                    'type': 'ir.actions.act_window',
                    'res_model': 'quotation',
                    'res_id': new.id,
                    'view_id.id': target_product_form.id,
                    'view_mode': 'form',
                    'target': 'new'
                }
            return

    def create_and_update_lines_quotation(self, bom_id, quotation_id):

        self.env.cr.execute(
            'delete from quotation_line where quotation_id = %s',
            [quotation_id.id])

        for bom_record in bom_id.bom_line_ids:
            if not bom_record.product_id.product_tmpl_id.is_operating_cost:
                max_value, min_value, p_market = self.get_min_max_cost(bom_record.product_id.product_tmpl_id.id)
                lines_created = self.env['quotation.line'].create({'name': str(bom_record.product_id.name),
                                                                   'quotation_id': quotation_id.id,
                                                                   'product_id': bom_record.product_id.id,
                                                                   'price_min': min_value,
                                                                   'price_max': max_value,
                                                                   'price_market': p_market,
                                                                   'qty_component': bom_record.product_qty,
                                                                   'percentage_of_loss': bom_id.percentage_of_loss})

        op_cost = self.env['product.template'].search([('is_operating_cost', '=', True)])
        op_p = 0
        if op_cost.price_market > 0:
            op_p = op_cost.price_market

        qty_bom = quotation_id.qty_bom
        cost_raw = 0
        cost_input = 0
        quotation_ids_lines = self.env['quotation.line'].search([('quotation_id', '=', quotation_id.id)])

        for line_q in quotation_ids_lines:
            if line_q.quotation_id.base_calculation == 'mp':
                calc = (line_q.price_market * line_q.qty_component) / qty_bom
                if line_q.product_id.categ_id.send_sicbatch:
                    cost_raw += calc
                else:
                    cost_input += calc
            elif line_q.quotation_id.base_calculation == 'min':
                calc = (line_q.price_min * line_q.qty_component) / qty_bom
                if line_q.product_id.categ_id.send_sicbatch:
                    cost_raw += calc
                else:
                    cost_input += calc
            elif line_q.quotation_id.base_calculation == 'max':
                calc = (line_q.price_max * line_q.qty_component) / qty_bom
                if line_q.product_id.categ_id.send_sicbatch:
                    cost_raw += calc
                else:
                    cost_input += calc

        cost_input_raw = cost_raw
        cost_input_input = cost_input
        cost_lost = (cost_input_raw * bom_id.percentage_of_loss) / 100
        primary_cost = cost_input_raw + cost_input_input + cost_lost
        cost_operating = op_p
        total_cost = primary_cost + op_p
        result_a = ((total_cost * quotation_id.percent_gain) / 100)
        result_b = (quotation_id.dollar_k)

        if result_a > result_b:
            result_base = result_a
        else:
            result_base = result_b

        result_total = total_cost + result_base

        if quotation_id.percent_partner_additional > 0:
            cost_additional = ((result_total * quotation_id.percent_partner_additional) / 100)
        else:
            cost_additional = 0

        price_quotation = total_cost + result_base + cost_additional
        cost_kg = total_cost * quotation_id.sale_order_line_id.dose_kgton
        price_kg = price_quotation * quotation_id.sale_order_line_id.dose_kgton
        profit_kg = (price_quotation * quotation_id.sale_order_line_id.dose_kgton) - (
                total_cost * quotation_id.sale_order_line_id.dose_kgton)

        percent_profit_kg = 0
        if profit_kg > 0 and price_kg > 0:
            percent_profit_kg = (profit_kg / price_kg) * 100
        percent_cost_profit_kg = 0
        if profit_kg > 0 and cost_kg > 0:
            percent_cost_profit_kg = (profit_kg / cost_kg) * 100

        quotation_id.cost_raw_input = cost_input_raw
        quotation_id.cost_input = cost_input_input
        quotation_id.total_percent_lost = cost_lost
        quotation_id.primary_cost = primary_cost
        quotation_id.cost_operating = cost_operating
        quotation_id.total_cost = total_cost
        quotation_id.result_percent_gain = result_a
        quotation_id.dollar_k = result_b
        quotation_id.result_total = result_total
        quotation_id.total_percent_partner_additional = cost_additional
        quotation_id.price_quotation = price_quotation
        quotation_id.cost_kg = cost_kg
        quotation_id.price_kg = price_kg
        quotation_id.profit_kg = profit_kg
        quotation_id.percent_profit_kg = percent_profit_kg
        quotation_id.percent_cost_profit_kg = percent_cost_profit_kg
        return price_quotation

    def get_min_max_cost(self, product_tmpl_id):
        self._cr.execute('''select coalesce(max(price_rate_convert),0) max_cost, 
                                        coalesce(min(price_rate_convert),0) min_cost
                             from product_supplierinfo ps 
                             where ps.date_end >= now()::date
                               and ps.product_tmpl_id = %s''',
                         [product_tmpl_id])
        value = self._cr.fetchone()
        max_value = value[0]
        min_value = value[1]
        product_tmpl = self.env['product.template'].search([('id', '=', product_tmpl_id)])
        p_market = product_tmpl.price_market
        return max_value, min_value, p_market
