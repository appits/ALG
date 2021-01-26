# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields,models,api
import datetime

class ResCompany(models.Model):
    _inherit = 'res.company'

    double_approval = fields.Boolean(string="Double Approval",default=True)
    double_approval_type = fields.Selection([('individual','Individual'),('global','Global')],default='global',string="Double Approval Type")
    double_approval_amount = fields.Float(string="Double Approval Maximum Amount")
    double_email_alerts_approve = fields.Selection([('no_alerts','No Alerts'),('all_approval','To All Approval (Who have approval limit more than total amount of order)'),('by_team','By Team (Sales Channels)'),('specific_users','Specific User')],
            default='no_alerts',string="Email Alert For Approval Orders")
    double_email_specific_user_id = fields.Many2one("res.users","Email Alert User")

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    double_approval = fields.Boolean(string="Double Approval",related="company_id.double_approval",readonly=False)
    double_approval_type = fields.Selection([('individual','Individual'),('global','Global')],default='global',related="company_id.double_approval_type",string="Double Approval Type" ,readonly=False)
    double_approval_amount = fields.Float(string="Double Approval Maximum Amount",related="company_id.double_approval_amount",help="This amount will be consider when approval type is global." ,readonly=False)
    
    double_email_alerts_approve = fields.Selection([('no_alerts','No Alerts'),('all_approval','To All Approval (Who have approval limit more than total amount of order)'),('by_team','By Team (Sales Channels)'),('specific_users','Specific User')],
            default='no_alerts',related="company_id.double_email_alerts_approve",string="Email Alert For Approval Orders",readonly=False)
    double_email_specific_user_id = fields.Many2one("res.users","Email Alert User",related="company_id.double_email_specific_user_id",readonly=False)
    
class ResUser(models.Model):
    _inherit = 'res.users'
    
    double_max_limit = fields.Float("Maximum Sales Limit(For Sales User)",help="This amount will be consider when approval type is individual and user not given 'Sales Order Double Approval' group.")
    double_approval_limit = fields.Float("Maximum Sales Approval Limit (For Approver)",help="This amount will be consider when approval type is individual and user(sales manager) has given 'Sales Order Double Approval' group.")
    
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    hide_approve_btn = fields.Boolean("Hide Approve button",compute="hide_approve_btn_conditionally",default = True)
    state = fields.Selection(selection_add=[('draft','Quotation'),('sent','Quotation Sent'),('approve','To Approve'),('refuse','Refused'),('sale','Sales Order'),('done','Locked'),('cancel','Cancelled'),],
                               string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
    so_refuse_reason_id = fields.Many2one("sh.so.refuse.reason",string= "Sale Order Refuse Reason",help="This field display reason of quatation cancellation")
    
    sh_approve_by = fields.Many2one("res.users",string="Approved By", copy=False, index=True, track_visibility='onchange')
    sh_approve_time = fields.Datetime(string="Approve Date", copy=False, index=True, track_visibility='onchange')
    sh_refuse_by = fields.Many2one("res.users",string="Refused By", copy=False, index=True, track_visibility='onchange')
    sh_refuse_reason = fields.Text(string="Refuse Reason", copy=False, index=True, track_visibility='onchange')
    sh_refuse_time = fields.Datetime(string="Refuse Date", copy=False, index=True, track_visibility='onchange')
    
    
    @api.depends('state')
    def hide_approve_btn_conditionally(self):
        if self.user_has_groups('sh_sale_order_double_approval.sh_group_sale_order_double_approval'): # If Double Approval Permission
            
            if self.env.user.double_approval_limit > self.amount_total and self.state =='approve':                
                self.hide_approve_btn =  False
            else:    
                self.hide_approve_btn =  True
        else:    
            self.hide_approve_btn =  True
            
    def action_approve(self):
        if self:
            for data in self:
                sale_obj = data.env['sale.order'].search([('id','=',data.id)])
                sale_obj.write({
                        'sh_approve_by': data.env.user.id,
                        'sh_approve_time': datetime.datetime.now()
                })
                data.action_confirm()
        
    
    def action_refuse(self,context=None):
        return {
        'name': ('Add Refuse Reason'),
        'view_type': 'form',
        'view_mode': 'form',
        'res_model': 'refuse.reason.wizard',
        'view_id': False,
        'type': 'ir.actions.act_window',
        'target':'new'
        }            
    
    def send_email_alert_noritification(self):
        dbl_email = self.env.user.company_id.double_email_alerts_approve
        if dbl_email:

            send_email_to  = ''
            users_ids = []
            template = self.env.ref('sh_sale_order_double_approval.sh_sale_order_double_approval_mail_template')
                            
            grp_id = self.env.ref('sh_sale_order_double_approval.sh_group_sale_order_double_approval').id
               
            if grp_id :
                res_grps = self.env['res.groups'].search([('id','=',grp_id)],limit=1)
                                
                if res_grps:                                    
                    for rec in res_grps.users:
                        users_ids.append(rec.id)
                                        
            if dbl_email == 'all_approval':       
                if template and users_ids:           
                    res_users = self.env['res.users'].search([('double_approval_limit','>=',self.amount_total),('id','in',users_ids)]) 
                                            
                    if res_users:                                         
                        for record in res_users:
                            if record.email:
                                mail_res = template.send_mail(self.id,force_send=True,email_values={'email_to':record.email})          
                                                
            elif dbl_email == 'by_team':       
                if template and users_ids:           

                    if self.team_id and self.team_id.member_ids:
                        for record in self.team_id.member_ids:

                            if (record.double_approval_limit >= self.amount_total and record.email):
                                mail_res = template.send_mail(self.id,force_send=True,email_values={'email_to':record.email })
                                                 
            elif dbl_email == 'specific_users': # Must Send without checking any condition        
                if template:     

                    if self.env.user.company_id.double_email_specific_user_id and self.env.user.company_id.double_email_specific_user_id.email:
                        send_email_to = self.env.user.company_id.double_email_specific_user_id.email
                        mail_res = template.send_mail(self.id,force_send=True,email_values={'email_to':send_email_to })
        
        
    def action_confirm(self): # overwrite existing
        
        if self.env.user.company_id.double_approval:
        
            dbl_apr_tp = self.env.user.company_id.double_approval_type 
            
            if dbl_apr_tp == 'global':   # Company wise
                glb_dbl_apr_amt = self.env.user.company_id.double_approval_amount 
                   
                if self.user_has_groups('sh_sale_order_double_approval.sh_group_sale_order_double_approval'):  #  If Double Approval Permission
                    ind_dbl_aprl_limit = self.env.user.double_approval_limit 
                   
                    if(self.amount_total >= ind_dbl_aprl_limit):   # check Individual for user having approval group
                        if self.state != 'approve':   # Executes if not already on approve stage 
                            self.send_email_alert_noritification()
                            self.state = 'approve'
                        
                    else:
                        self.hide_approve_btn = True
                        res = super(SaleOrder,self).action_confirm()
                        return res            
                   
                else: 
                        
                    if(self.amount_total >= glb_dbl_apr_amt):   # check globally for user not having approval group
                        if self.state != 'approve':   # Executes if not already on approve stage 
                            self.send_email_alert_noritification()
                            self.state = 'approve'
                    else:
                        self.hide_approve_btn = True
                        res = super(SaleOrder,self).action_confirm()
                        return res            
            
            elif dbl_apr_tp == 'individual':   # User Wise
                
                if self.user_has_groups('sh_sale_order_double_approval.sh_group_sale_order_double_approval'): # If Double Approval Permission
                    ind_dbl_aprl_limit = self.env.user.double_approval_limit 
                        
                    if(self.amount_total >= ind_dbl_aprl_limit):   # check Individual for user having approval group
                        if self.state != 'approve':   # Executes if not already on approve stage 
                            self.send_email_alert_noritification()
                            self.state = 'approve'
                    else:
                        self.hide_approve_btn = True
                        res = super(SaleOrder,self).action_confirm()
                        return res            
                
                else : # to Approve  Stage   
                    
                    ind_dbl_max_amt = self.env.user.double_max_limit 
                    
                    if(self.amount_total >= ind_dbl_max_amt):   # check Individual for user NOT having approval group
                        if self.state != 'approve':   # Executes if not already on approve stage 
                            self.send_email_alert_noritification()
                            self.state = 'approve'
                    else:
                        self.hide_approve_btn = True
                        res = super(SaleOrder,self).action_confirm()
                        return res            
                        
            return False      
              
        else :
            self.hide_approve_btn = True
            res = super(SaleOrder,self).action_confirm()
            return res            
        
    def action_draft(self):
        res = super(SaleOrder,self).action_draft()
        return res     
