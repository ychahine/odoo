from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'


    google_calendar_client_id = fields.Char(string="Calendar Client ID")
    google_calendar_client_secret = fields.Char(string="Calendar Client Secret")
    cal_sync_paused = fields.Boolean("Interrompre la synchronisation",
                                     help="Indique si la synchronisation avec google est active ou en pause")