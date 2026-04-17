# -*- coding: utf-8 -*-
from odoo import fields, models


class IrMailServer(models.Model):
    """ This model inherit ir.mail_server."""
    _inherit = 'ir.mail_server'

    company_id = fields.Many2one(
        'res.company',
        string='Société',
        default=lambda self: self.env.company,
        readonly=True,
        help='Société associé au serveur de messagerie')