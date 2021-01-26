from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from . import utils


class Schema(models.Model):
    _name = 'acct.schema'
    _description = 'Allow record accounting in other currency'

    name = fields.Char()
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency')
    is_default = fields.Boolean(default=False, copy=False)

    @api.constrains('is_default')
    def validate_transit(self):
        location = self.env['acct.schema'].search([('is_default', '=', True)])
        number = 0
        for record in location:
            number += 1
        if number > 1:
            raise ValidationError(_('No puede tener mas de un esquema contable por defecto'))


class GLJournal(models.Model):
    _name = 'gl.journal'
    _description = 'Accounting Fact Acct Entry'

    name = fields.Char()
    date = fields.Date()
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency')
    schema_id = fields.Many2one('acct.schema')
    debit = fields.Float(default=0, copy=False)
    credit = fields.Float(default=0, copy=False)
    journal_id = fields.Many2one('account.journal', string='Journal', required=True, readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 domain="[('company_id', '=', company_id)]")
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('edit', 'Edit')
    ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft')
    lines_ids = fields.One2many('fact.acct', 'gl_id', ondelete="cascade")

    @api.onchange('lines_ids')
    def get_debit_credit_lines(self):
        debit = 0
        credit = 0
        for lines in self.lines_ids:
            debit += lines.debit
            credit += lines.credit
        self.debit = debit
        self.credit = credit

    @api.onchange('schema_id')
    def set_currency(self):
        if self.schema_id:
            self.currency_id = self.schema_id.currency_id.id

    def action_confirm(self):
        if self.debit == self.credit:
            if self.lines_ids:
                self.state = 'posted'
                for lines in self.lines_ids:
                    lines.state = 'posted'
            else:
                raise ValidationError(
                    _('Cannot process a document without lines'))
        else:
            raise ValidationError(
                _('The debit and credit entries must be the same, it cannot generate an offset entry'))

    def action_edit(self):
        if self.debit == self.credit:
            if self.lines_ids:
                self.state = 'edit'
                for lines in self.lines_ids:
                    lines.state = 'draft'

    def unlink(self):
        for gl in self:
            if gl.state not in 'draft':
                raise UserError(_('You cannot delete a posted record'))
        return super(GLJournal, self).unlink()


class FactAcct(models.Model):
    _name = 'fact.acct'
    _description = 'Accounting Fact Acct Schema'

    name = fields.Char()
    date = fields.Date()
    schema_id = fields.Many2one('acct.schema')
    account_id = fields.Many2one('account.account')
    type = fields.Selection(selection=[
        ('entry', 'Journal Entry'),
        ('out_invoice', 'Customer Invoice'),
        ('out_refund', 'Customer Credit Note'),
        ('in_invoice', 'Vendor Bill'),
        ('in_refund', 'Vendor Credit Note'),
        ('out_receipt', 'Sales Receipt'),
        ('in_receipt', 'Purchase Receipt'),
    ], string='Type', required=True, store=True, index=True, readonly=True, tracking=True,
        default="entry", change_default=True)
    journal_id = fields.Many2one('account.journal', string='Journal', required=True, readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 domain="[('company_id', '=', company_id)]")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency')
    move_id = fields.Many2one('account.move', ondelete="cascade")
    asset_id = fields.Many2one('account.asset')
    currency_rate = fields.Float()
    debit = fields.Float()
    credit = fields.Float()
    product_id = fields.Many2one('product.product')
    partner_id = fields.Many2one('res.partner')
    quantity = fields.Float()
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled')
    ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft')
    line_id = fields.Many2one('account.move.line', ondelete="cascade")
    gl_id = fields.Many2one('gl.journal', ondelete="cascade")

    def unlink(self):
        for record in self:
            raise ValidationError(_('Error, you cannot delete this record'))
        return super(FactAcct, self).unlink()


class AccountMove(models.Model):
    _inherit = 'account.move'

    fact_acct_rate = fields.Float()
    fact_acct_ids = fields.One2many('fact.acct', 'move_id', copy=False, ondelete="cascade")
    fact_acct_count = fields.Float(compute='count_fact_acc', copy=False)
    currency_date = fields.Datetime()

    def count_fact_acc(self):
        fact = []
        number = 0
        for record in self.fact_acct_ids:
            fact += [record.id]
        if self.fact_acct_ids:
            query = 'select count(id) from fact_acct where id in'
            string_fact = (str(fact).replace('[', '(').replace(']', ')'))
            query_execute = query + string_fact
            self._cr.execute(query_execute)
            value = self._cr.fetchall()
            for count in value:
                number = count[0]
        self['fact_acct_count'] = number

    def call_fact_acct(self):
        action = self.env.ref('multi_schema.fact_acct_act_window').read()[0]
        fact_acct = []
        for record in self.fact_acct_ids:
            fact_acct += [record.id]
        (str(fact_acct).replace('[', '(').replace(']', ')'))
        action['domain'] = [('id', 'in', fact_acct)]
        return action

    @api.model
    def create(self, vals):
        result = super(AccountMove, self).create(vals)
        if result.asset_id.id > 0:
            asset = self.env['account.asset'].search([
                ('id', '=', result.asset_id.id)
            ])
            result.fact_acct_rate = asset.rate
        return result

    def default_currency(self):
        schema = self.env['acct.schema'].search([('is_default', '=', True)])
        currency = schema.currency_id.id
        return currency

    currency_from_id = fields.Many2one('res.currency', default=default_currency)
    exchange_rate = fields.Float()
    execute_line = fields.Boolean(default=False, copy=False)

    @api.onchange('currency_from_id')
    def _compute_rate(self):
        if self.currency_from_id:
            date, rate = utils.get_invoice_rate(self)
            self.exchange_rate = rate
            self.currency_date = date

    @api.constrains('state')
    def set_cost(self):
        if self.state == 'posted' and self.type == 'entry':
            t_product_id = self.env['product.template']
            for lines in self.invoice_line_ids:
                t_product_id.calc_current_cost(lines.product_id.product_tmpl_id.id)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    fact_acct_ids = fields.One2many('fact.acct', 'line_id', ondelete="cascade")
    price_om = fields.Float()
    view_price_om = fields.Boolean(default=False, copy=False)

    @api.constrains('parent_state', 'debit', 'credit')
    def create_fact_acct(self):
        for line in self:
            if line.debit > 0 or line.credit > 0:
                if line.move_id.asset_id and line.parent_state == 'posted':
                    for currencies_sch in line.move_id.asset_id.currencies_asset_ids:
                        rate = currencies_sch.rate
                        debit = round(line.debit / rate, 2)
                        credit = round(line.credit / rate, 2)
                        self._create_fact(line, currencies_sch.schema_id, rate, debit, credit)

                schemas = self.env['acct.schema'].search([
                    ('company_id', '=', self.company_id.id)
                ])
                for schema in schemas:
                    if line.parent_state == 'posted':
                        if not line.move_id.asset_id:
                            date_rate, rate = utils.get_schema_rate(schema, line.move_id.date)
                            debit = round(line.debit / rate, 2)
                            credit = round(line.credit / rate, 2)
                            self._create_fact(line, schema, rate, debit, credit)

    def _create_fact(self, line, schema, rate, debit, credit):
        self.env['fact.acct'].create({
            'name': line.name,
            'date': line.date,
            'journal_id': line.journal_id.id,
            'company_id': line.company_id.id,
            'currency_id': schema.currency_id.id,
            'move_id': line.move_id.id,
            'currency_rate': rate,
            'debit': debit,
            'credit': credit,
            'product_id': line.product_id.id,
            'partner_id': line.partner_id.id,
            'quantity': line.quantity,
            'asset_id': line.move_id.asset_id.id,
            'account_id': line.account_id.id,
            'schema_id': schema.id,
            'state': 'posted',
            'line_id': line.id
        })

    @api.onchange('price_om')
    def set_price(self):
        for record in self:
            if record.product_id:
                record.price_unit = record.price_om * record.move_id.exchange_rate

    '''
    @api.constrains('price_unit', 'price_om')
    def save_price(self):
        for record in self:
            if record.product_id and record.move_id.journal_id.company_id.currency_id.id != record.move_id.currency_from_id.id:
                record.price_om = record.price_unit / record.move_id.exchange_rate
                record.view_price_om = True

    @api.onchange('product_id')
    def display_price_om_line(self):
        for record in self:
            if record.move_id.journal_id.company_id.currency_id.id != record.move_id.currency_from_id.id:
                record.view_price_om = True
    '''


class MultiCurrencyRate(models.Model):
    _name = 'multi.currency.rate'

    name = fields.Char(required=True)
    currency_id = fields.Many2one('res.currency')
    rate_date = fields.Datetime()
    rate = fields.Float()
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)

    @api.constrains('rate')
    def validate_rate(self):
        if self.rate == 0:
            raise ValidationError(_('Error the amount of the rate cannot be zero'))

    @api.model
    def create(self, vals):
        result = super(MultiCurrencyRate, self).create(vals)
        self.core_currency(result)
        return result

    def write(self, vals):
        wr = super(MultiCurrencyRate, self).write(vals)
        self.core_currency(self)

        return wr

    def core_currency(self, result):
        date = result.rate_date.strftime('%Y-%m-%d')

        core_rate = self.env['res.currency.rate'].search([
            ('currency_id', '=', result.currency_id.id),
            ('name', '=', date)
        ])
        new_rate = 1 / result.rate
        if core_rate:
            core_rate.rate = new_rate
        else:
            new_rate = self.env['res.currency.rate'].create({
                'name': date,
                'rate': new_rate,
                'currency_id': result.currency_id.id
            })


class Currency(models.Model):
    _inherit = 'res.currency'

    def open_currency_rate(self):
        results = self.env['multi.currency.rate'].read_group([('currency_id', 'in', self.ids)], ['currency_id'],
                                                             ['currency_id'])
        dic = {}
        for x in results:
            dic[x['currency_id'][0]] = x['currency_id_count']
        for record in self:
            record['currency_rates'] = dic.get(record.id, 0)

    multi_currency_ids = fields.One2many('multi.currency.rate', 'currency_id')
    currency_rates = fields.Float(compute=open_currency_rate)


class CurrenciesAsset(models.Model):
    _name = 'currencies.asset'

    date_currency = fields.Date()
    rate = fields.Float()
    schema_id = fields.Many2one('acct.schema')
