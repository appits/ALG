from odoo import fields, models, api


class ParametersReport(models.TransientModel):
    _name = 'parameters.report'
    _description = 'Parameters'

    schema_id = fields.Many2one('acct.schema')
    date = fields.Date()
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)
    report_type = fields.Selection(selection=[
        ('financial', 'Balance Sheet'),
        ('profit_loss', 'Profit and Loss'),
        ('receivable', 'Aged Receivable'),
        ('payable', 'Aged Payable'),
        ('payable', 'Aged Payable'),
        ('inventory', 'Inventory Valuation'),
    ], string='Type', required=True, store=True)

    def execute_report(self):
        if self.report_type == 'financial':
            report = self.env['fact.acct.report.financial']
            report_views = report.generate_report_financial(self.schema_id, self.company_id, self.date)
            views = report.call_report()
        elif self.report_type == 'profit_loss':
            report_p = self.env['fact.acct.report.profit.loss']
            report_views_p = report_p.generate_report_profit(self.schema_id, self.company_id, self.date)
            views = report_p.call_report()
        elif self.report_type == 'receivable':
            report_r = self.env['fact.acct.aged.receivable']
            report_views_r = report_r.generate_report_receivable(self.schema_id, self.company_id)
            views = report_r.call_report()
        elif self.report_type == 'payable':
            report_pa = self.env['fact.acct.aged.payable']
            report_views_pa = report_pa.generate_report_payable(self.schema_id, self.company_id)
            views = report_pa.call_report()
        elif self.report_type == 'inventory':
            report_i = self.env['fact.acct.inventory.valuation']
            report_views_i = report_i.generate_report_inventory(self.schema_id, self.company_id, self.date)
            views = report_i.call_report()
        return views


class FactAcctReportFinancial(models.TransientModel):
    _name = 'fact.acct.report.financial'
    _description = 'Storage Results fiscal'

    sequence = fields.Float()
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)
    schema_id = fields.Many2one('acct.schema')
    account_id = fields.Many2one('account.account')
    type = fields.Selection(selection=[
        ('asset', 'Asset'),
        ('liabilities', 'Liabilities'),
        ('equity', 'Equity'),
    ], string='Type', required=True, store=True, index=True, readonly=True)
    sub_type = fields.Selection(selection=[
        ('receivable', 'Receivable'),
        ('bank_and_cash', 'Bank and Cash'),
        ('credit_card', 'Credit Card'),
        ('current_assets', 'Current Assets'),
        ('non_current_assets', 'Non-current Assets'),
        ('prepayments', 'Prepayments'),
        ('fixed_assets', 'Fixed Assets'),
        ('payable', 'Payable'),
        ('current_liabilities', 'Current Liabilities'),
        ('non_current_liabilities', 'Non-current Liabilities'),
        ('equity', 'Equity'),
        ('current_year_earnings', 'Current Year Earnings'),
        ('total', 'Totals'),
    ], string='Type', store=True, index=True, readonly=True)
    currency_id = fields.Many2one('res.currency')
    move_id = fields.Many2one('account.move')
    debit = fields.Monetary()
    credit = fields.Monetary()
    balance = fields.Monetary()
    balance_total = fields.Monetary()

    def generate_report_financial(self, schema, company_id, date_end):

        data_report = self.env['fact.acct'].search(
            [('schema_id.id', '=', schema.id), ('company_id.id', '=', company_id.id), ('date', '<=', date_end),
             ('state', '=', 'posted')])

        self.env.cr.execute(
            'delete from fact_acct_report_financial where 1=1')

        asset = self.result_sql(schema, date_end, company_id, (1, 3, 4, 5, 6, 7, 8))
        asset_sum = 0
        for sqls in asset:
            asset_sum += sqls[0]
        self.create_record(0, company_id.id, schema.id, 0, 'asset', 'total', schema.currency_id.id, 0, 0, 0, 0,
                           asset_sum)

        liabilities = self.result_sql(schema, date_end, company_id, (2, 9, 10))
        liabilities_sum = 0
        for sqls_liabilities in liabilities:
            liabilities_sum += sqls_liabilities[0]
        self.create_record(8, company_id.id, schema.id, 0, 'liabilities', 'total', schema.currency_id.id, 0, 0, 0, 0,
                           liabilities_sum)

        equity = self.result_sql(schema, date_end, company_id, (11, 12))
        sum_equity = 0
        for sqls_equity in equity:
            sum_equity += sqls_equity[0]
        self.create_record(8, company_id.id, schema.id, 0, 'equity', 'total', schema.currency_id.id, 0, 0, 0, 0,
                           sum_equity)

        views = []
        for record in data_report:
            if record.account_id.user_type_id.id == 1:
                views += [
                    self.create_record(1, record.company_id.id, record.schema_id.id, record.account_id.id, 'asset',
                                       'receivable', record.currency_id.id, record.move_id.id, record.debit,
                                       record.credit, (record.debit - record.credit), 0)]

            if record.account_id.user_type_id.id == 3:
                views += [
                    self.create_record(2, record.company_id.id, record.schema_id.id, record.account_id.id, 'asset',
                                       'bank_and_cash', record.currency_id.id, record.move_id.id, record.debit,
                                       record.credit, (record.debit - record.credit), 0)]

            if record.account_id.user_type_id.id == 4:
                views += [
                    self.create_record(3, record.company_id.id, record.schema_id.id, record.account_id.id, 'asset',
                                       'credit_card', record.currency_id.id, record.move_id.id, record.debit,
                                       record.credit, (record.debit - record.credit), 0)]

            if record.account_id.user_type_id.id == 5:
                views += [
                    self.create_record(4, record.company_id.id, record.schema_id.id, record.account_id.id, 'asset',
                                       'current_assets', record.currency_id.id, record.move_id.id, record.debit,
                                       record.credit, (record.debit - record.credit), 0)]

            if record.account_id.user_type_id.id == 6:
                views += [
                    self.create_record(5, record.company_id.id, record.schema_id.id, record.account_id.id, 'asset',
                                       'non_current_assets', record.currency_id.id, record.move_id.id, record.debit,
                                       record.credit, (record.debit - record.credit), 0)]

            if record.account_id.user_type_id.id == 7:
                views += [
                    self.create_record(6, record.company_id.id, record.schema_id.id, record.account_id.id, 'asset',
                                       'prepayments', record.currency_id.id, record.move_id.id, record.debit,
                                       record.credit, (record.debit - record.credit), 0)]

            if record.account_id.user_type_id.id == 8:
                views += [
                    self.create_record(7, record.company_id.id, record.schema_id.id, record.account_id.id, 'asset',
                                       'fixed_assets', record.currency_id.id, record.move_id.id, record.debit,
                                       record.credit, (record.debit - record.credit), 0)]

            if record.account_id.user_type_id.id == 2:
                views += [self.create_record(8, record.company_id.id, record.schema_id.id, record.account_id.id,
                                             'liabilities', 'payable', record.currency_id.id, record.move_id.id,
                                             record.debit, record.credit, (record.debit - record.credit), 0)]

            if record.account_id.user_type_id.id == 9:
                views += [self.create_record(9, record.company_id.id, record.schema_id.id, record.account_id.id,
                                             'liabilities', 'current_liabilities', record.currency_id.id,
                                             record.move_id.id, record.debit, record.credit,
                                             (record.debit - record.credit), 0)]

            if record.account_id.user_type_id.id == 10:
                views += [self.create_record(10, record.company_id.id, record.schema_id.id, record.account_id.id,
                                             'liabilities', 'non_current_liabilities', record.currency_id.id,
                                             record.move_id.id, record.debit, record.credit,
                                             (record.debit - record.credit), 0)]

            if record.account_id.user_type_id.id == 12:
                views += [
                    self.create_record(11, record.company_id.id, record.schema_id.id, record.account_id.id, 'equity',
                                       'current_year_earnings', record.currency_id.id, record.move_id.id, record.debit,
                                       record.credit, (record.debit - record.credit), 0)]

            if record.account_id.user_type_id.id == 11:
                views += [
                    self.create_record(12, record.company_id.id, record.schema_id.id, record.account_id.id, 'equity',
                                       'equity', record.currency_id.id, record.move_id.id, record.debit, record.credit,
                                       (record.debit - record.credit), 0)]

        return views

    def create_record(self, sequence, company, schema_id, account_id, m_type, sub_type, currency, move_id, debit,
                      credit, balance, balance_total):
        self.env['fact.acct.report.financial'].create({'sequence': sequence,
                                                       'company_id': company,
                                                       'schema_id': schema_id,
                                                       'account_id': account_id,
                                                       'type': m_type,
                                                       'sub_type': sub_type,
                                                       'currency_id': currency,
                                                       'move_id': move_id,
                                                       'debit': debit,
                                                       'credit': credit,
                                                       'balance': balance,
                                                       'balance_total': balance_total,
                                                       })

    def result_sql(self, schema, date_end, company_id, ids):
        self._cr.execute(
            'select coalesce ((sum(fa.debit) - sum(fa.credit)),0) '
            ' from fact_acct fa  '
            '    join account_account aa on fa.account_id = aa.id '
            ' where fa.schema_id = %s '
            ' and fa."date" <= %s '
            ' and fa.company_id = %s '
            ' and aa.user_type_id in %s ',
            [schema.id, date_end, company_id.id, ids])
        sql = self._cr.fetchall()
        return sql

    def call_report(self):
        target_tree = self.env.ref('multi_schema.profit_financial_layer_action')
        target_search = self.env.ref('multi_schema.financial_report_layer_search')
        return {
            'name': 'Balance sheet',
            'type': 'ir.actions.act_window',
            'res_model': 'fact.acct.report.financial',
            'view_mode': 'tree,form',
            'view_id.id': target_tree.id,
            'search_view_id': target_search.id,
            'target': 'current',
            'context': {'search_default_group_by_type': 1, 'search_default_group_by_sub_type': 1,
                        'search_default_group_by_account_id': 1},
        }


class FactAcctReportProfitAndLoss(models.TransientModel):
    _name = 'fact.acct.report.profit.loss'
    _description = 'Storage Profit and loss'
    _order = "sequence_p"

    sequence_p = fields.Float()
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)
    schema_id = fields.Many2one('acct.schema')
    account_id = fields.Many2one('account.account')
    type = fields.Selection(selection=[
        ('income', 'Income'),
        ('cost_revenue', 'Cost of Revenue'),
        ('expenses', 'Expenses'),
    ], string='Type', required=True, store=True, index=True, readonly=True)
    sub_type = fields.Selection(selection=[
        ('income', 'Income'),
        ('other_income', 'Other Income'),
        ('cost_r', 'Cost of Revenue'),
        ('expenses', 'Expenses'),
        ('depreciation', 'Depreciation'),
        ('total', 'Totals'),
    ], string='Sub Type', store=True, index=True, readonly=True)
    currency_id = fields.Many2one('res.currency')
    move_id = fields.Many2one('account.move')
    debit = fields.Monetary()
    credit = fields.Monetary()
    balance = fields.Monetary()
    balance_total = fields.Monetary()

    def generate_report_profit(self, schema, company_id, date_end):

        data_report = self.env['fact.acct'].search(
            [('schema_id.id', '=', schema.id), ('company_id.id', '=', company_id.id), ('date', '<=', date_end),
             ('state', '=', 'posted')])

        self.env.cr.execute(
            'delete from fact_acct_report_profit_loss where 1=1')

        income = self.result_sql(schema.id, date_end, company_id, (13, 14))
        income_sum = 0
        for sqls in income:
            income_sum += sqls[0]
        self.create_record(0, company_id.id, schema.id, 0, 'income', 'total', schema.currency_id.id, 0, 0, 0, 0,
                           income_sum)

        cost = self.result_sql(schema.id, date_end, company_id, (17, 17))
        cost_sum = 0
        for sqls_cost in cost:
            cost_sum += sqls_cost[0]
        self.create_record(3, company_id.id, schema.id, 0, 'cost_revenue', 'total', schema.currency_id.id, 0, 0, 0, 0,
                           cost_sum)

        expense = self.result_sql(schema.id, date_end, company_id, (15, 16))
        sum_expense = 0
        for sqls_expense in expense:
            sum_expense += sqls_expense[0]
        self.create_record(5, company_id.id, schema.id, 0, 'expenses', 'total', schema.currency_id.id, 0, 0, 0, 0,
                           sum_expense)

        views = []
        for record in data_report:
            if record.account_id.user_type_id.id == 13:
                views += [
                    self.create_record(1, record.company_id.id, record.schema_id.id, record.account_id.id, 'income',
                                       'income', record.currency_id.id, record.move_id.id, record.debit, record.credit,
                                       (record.debit - record.credit), 0)]
            if record.account_id.user_type_id.id == 14:
                views += [
                    self.create_record(2, record.company_id.id, record.schema_id.id, record.account_id.id, 'income',
                                       'other_income', record.currency_id.id, record.move_id.id, record.debit,
                                       record.credit, (record.debit - record.credit), 0)]
            if record.account_id.user_type_id.id == 17:
                views += [self.create_record(3, record.company_id.id, record.schema_id.id, record.account_id.id,
                                             'cost_revenue', 'cost_r', record.currency_id.id, record.move_id.id,
                                             record.debit, record.credit, (record.debit - record.credit), 0)]
            if record.account_id.user_type_id.id == 15:
                views += [
                    self.create_record(4, record.company_id.id, record.schema_id.id, record.account_id.id, 'expenses',
                                       'expenses', record.currency_id.id, record.move_id.id, record.debit,
                                       record.credit, (record.debit - record.credit), 0)]
            if record.account_id.user_type_id.id == 16:
                views += [
                    self.create_record(5, record.company_id.id, record.schema_id.id, record.account_id.id, 'expenses',
                                       'depreciation', record.currency_id.id, record.move_id.id, record.debit,
                                       record.credit, (record.debit - record.credit), 0)]
        return views

    def create_record(self, sequence, company, schema_id, account_id, m_type, sub_type, currency, move_id, debit,
                      credit, balance, balance_total):
        self.env['fact.acct.report.profit.loss'].create({'sequence_p': sequence,
                                                         'company_id': company,
                                                         'schema_id': schema_id,
                                                         'account_id': account_id,
                                                         'type': m_type,
                                                         'sub_type': sub_type,
                                                         'currency_id': currency,
                                                         'move_id': move_id,
                                                         'debit': debit,
                                                         'credit': credit,
                                                         'balance': balance,
                                                         'balance_total': balance_total,
                                                         })

    def result_sql(self, schema, date_end, company_id, ids):
        self._cr.execute(
            'select coalesce ((sum(fa.debit) - sum(fa.credit)),0) '
            ' from fact_acct fa  '
            '    join account_account aa on fa.account_id = aa.id '
            ' where fa.schema_id = %s '
            ' and fa."date" <= %s '
            ' and fa.company_id = %s '
            ' and aa.user_type_id in %s ',
            [schema, date_end, company_id.id, ids])
        sql = self._cr.fetchall()
        return sql

    def call_report(self):
        target_tree = self.env.ref('multi_schema.profit_financial_layer_action')
        target_search = self.env.ref('multi_schema.profit_loss_report_layer_search')
        return {
            'name': 'Profit And Loss',
            'type': 'ir.actions.act_window',
            'res_model': 'fact.acct.report.profit.loss',
            'view_mode': 'tree,form',
            'view_id.id': target_tree.id,
            'search_view_id': target_search.id,
            'target': 'current',
            'context': {'search_default_group_by_type_loss': 1, 'search_default_group_by_sub_type_loss': 1,
                        'search_default_group_by_account_id_loss': 1},
        }


class AgedReceivable(models.TransientModel):
    _name = 'fact.acct.aged.receivable'
    _description = 'Storage Aged Receivable'
    _order = "date_trx, partner_id"

    date_trx = fields.Date()
    partner_id = fields.Many2one('res.partner')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)
    schema_id = fields.Many2one('acct.schema')
    currency_id = fields.Many2one('res.currency')
    move_id = fields.Many2one('account.move')
    balance_total = fields.Monetary()

    def generate_report_receivable(self, schema, company_id):

        data_report = self.env['fact.acct'].search(
            [('schema_id.id', '=', schema.id), ('company_id.id', '=', company_id.id), ('state', '=', 'posted')])

        self.env.cr.execute(
            'delete from fact_acct_aged_receivable where 1=1')

        for data in data_report:
            if data.account_id.user_type_id.id == 1 and data.move_id.type == 'out_invoice':
                amount_residual = (data.move_id.amount_residual / data.currency_rate)
                if amount_residual > 0:
                    self.create_record(data.partner_id.id, data.date, data.company_id.id, data.schema_id.id,
                                       data.currency_id.id, data.move_id.id, amount_residual)

        return

    def create_record(self, partner_id, date_trx, company, schema_id, currency, move_id,
                      balance_total):
        self.env['fact.acct.aged.receivable'].create({'partner_id': partner_id,
                                                      'date_trx': date_trx,
                                                      'company_id': company,
                                                      'schema_id': schema_id,
                                                      'currency_id': currency,
                                                      'move_id': move_id,
                                                      'balance_total': balance_total,
                                                      })

    def call_report(self):
        target_tree = self.env.ref('multi_schema.receivable_layer_action')
        target_search = self.env.ref('multi_schema.receivable_report_layer_search')
        return {
            'name': 'Aged Receivable',
            'type': 'ir.actions.act_window',
            'res_model': 'fact.acct.aged.receivable',
            'view_mode': 'tree,form',
            'view_id.id': target_tree.id,
            'search_view_id': target_search.id,
            'target': 'current',
            'context': {'search_default_group_by_partner_id': 1}

        }


class AgedPayable(models.TransientModel):
    _name = 'fact.acct.aged.payable'
    _description = 'Storage Aged Payable'
    _order = "date_trx, partner_id"

    date_trx = fields.Date()
    partner_id = fields.Many2one('res.partner')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)
    schema_id = fields.Many2one('acct.schema')
    currency_id = fields.Many2one('res.currency')
    move_id = fields.Many2one('account.move')
    balance_total = fields.Monetary()

    def generate_report_payable(self, schema, company_id):

        data_report = self.env['fact.acct'].search(
            [('schema_id.id', '=', schema.id), ('company_id.id', '=', company_id.id)])

        self.env.cr.execute(
            'delete from fact_acct_aged_payable where 1=1')

        for data in data_report:
            if data.account_id.user_type_id.id == 2 and data.move_id.type == 'in_invoice':
                amount_residual = (data.move_id.amount_residual / data.currency_rate)
                if amount_residual > 0:
                    self.create_record(data.partner_id.id, data.date, data.company_id.id, data.schema_id.id,
                                       data.currency_id.id, data.move_id.id, amount_residual)

        return

    def create_record(self, partner_id, date_trx, company, schema_id, currency, move_id,
                      balance_total):
        self.env['fact.acct.aged.payable'].create({'partner_id': partner_id,
                                                   'date_trx': date_trx,
                                                   'company_id': company,
                                                   'schema_id': schema_id,
                                                   'currency_id': currency,
                                                   'move_id': move_id,
                                                   'balance_total': balance_total,
                                                   })

    def call_report(self):
        target_tree = self.env.ref('multi_schema.payable_layer_action')
        target_search = self.env.ref('multi_schema.payable_report_layer_search')
        return {
            'name': 'Aged Payable',
            'type': 'ir.actions.act_window',
            'res_model': 'fact.acct.aged.payable',
            'view_mode': 'tree,form',
            'view_id.id': target_tree.id,
            'search_view_id': target_search.id,
            'target': 'current',
            'context': {'search_default_group_by_partner_id': 1}

        }


class InventoryValuation(models.TransientModel):
    _name = 'fact.acct.inventory.valuation'
    _description = 'Storage Inventory Valuation'
    _order = "date_trx, product_id"

    date_trx = fields.Datetime()
    product_id = fields.Many2one('product.product')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)
    schema_id = fields.Many2one('acct.schema')
    currency_id = fields.Many2one('res.currency')
    move_id = fields.Many2one('account.move')
    qty_movement = fields.Float()
    unit_cost = fields.Float()
    balance_total = fields.Monetary()

    def generate_report_inventory(self, schema, company_id, date):

        data_report = self.env['fact.acct'].search(
            [('schema_id.id', '=', schema.id), ('company_id.id', '=', company_id.id), ('date', '<=', date),
             ('type', '=', 'entry'), ('debit', '>', 0), ('state', '=', 'posted'), ('product_id', '!=', False)])

        self.env.cr.execute(
            'delete from fact_acct_inventory_valuation where 1=1')

        for data in data_report:
            amount = data.debit
            amount_cost = data.debit
            move_id = 0
            if amount != 0:
                qty_cost = data.quantity
                move_id = data.move_id.id
                if data.quantity < 0:
                    qty_cost = data.quantity * -1
                    amount = amount * -1
                if qty_cost != 0 and amount != 0:
                    cost_unit = (amount_cost / qty_cost)
                else:
                    cost_unit = 0

                self.create_record(data.product_id.id, data.create_date, data.company_id.id, data.schema_id.id,
                                   data.currency_id.id, move_id, data.quantity, cost_unit, amount)

        return

    def create_record(self, product_id, date_trx, company, schema_id, currency, move_id,
                      qty_movement, unit_cost, balance_total):
        self.env['fact.acct.inventory.valuation'].create({'product_id': product_id,
                                                          'date_trx': date_trx,
                                                          'company_id': company,
                                                          'schema_id': schema_id,
                                                          'currency_id': currency,
                                                          'move_id': move_id,
                                                          'qty_movement': qty_movement,
                                                          'unit_cost': unit_cost,
                                                          'balance_total': balance_total,
                                                          })

    def call_report(self):
        target_tree = self.env.ref('multi_schema.inventory_layer_action')
        target_search = self.env.ref('multi_schema.inventory_report_layer_search')
        return {
            'name': 'Inventory Valuation',
            'type': 'ir.actions.act_window',
            'res_model': 'fact.acct.inventory.valuation',
            'view_mode': 'tree,form',
            'view_id.id': target_tree.id,
            'search_view_id': target_search.id,
            'target': 'current',
            'context': {'search_default_group_by_product_id': 1}

        }
