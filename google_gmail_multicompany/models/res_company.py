from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    """
        SURCHARGE DU MODÈLE RESCOMPANY POUR 
        PRISE EN CHARGE INDIVIDUELLE DES IDENTIFIANTS
        GOOGLE CONSOLE 
    """

    google_gmail_client_identifier = fields.Char(
        string='Gmail Client Id'
    )
    google_gmail_client_secret = fields.Char(
        string='Gmail Client Secret'
    )