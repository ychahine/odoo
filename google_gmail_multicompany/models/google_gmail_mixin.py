# -*- coding: utf-8 -*-
import json
import requests
from werkzeug.urls import url_encode, url_join
from odoo import _, api, models
from odoo.exceptions import UserError


class GoogleGmailMixin(models.AbstractModel):
    _inherit = 'google.gmail.mixin'

    def _get_gmail_credentials(self):
        """ Récupère les credentials de la société liée au record """
        self.ensure_one()
        # Si le serveur n'a pas de société, on peut éventuellement
        # prendre celle de l'utilisateur ou rester sur les paramètres système par défaut
        company = self.company_id if hasattr(self, 'company_id') and self.company_id else self.env.company

        return {
            'client_id': company.google_gmail_client_identifier,
            'client_secret': company.google_gmail_client_secret,
        }

    @api.depends('google_gmail_authorization_code')
    def _compute_gmail_uri(self):
        for record in self:
            creds = record._get_gmail_credentials()
            if not creds['client_id'] or not creds['client_secret']:
                record.google_gmail_uri = False
            else:
                # Utiliser creds['client_id'] au lieu de Config.get_param
                base_url = self.get_base_url()
                redirect_uri = url_join(base_url, '/google_gmail/confirm')

                record.google_gmail_uri = 'https://accounts.google.com/o/oauth2/v2/auth?%s' % url_encode({
                    'client_id': creds['client_id'],
                    'redirect_uri': redirect_uri,
                    'response_type': 'code',
                    'scope': self._SERVICE_SCOPE,
                    'access_type': 'offline',
                    'prompt': 'consent',
                    'state': json.dumps({
                        'model': record._name,
                        'id': record.id or False,
                        'csrf_token': record._get_gmail_csrf_token() if record.id else False,
                    })
                })

    def _fetch_gmail_token(self, grant_type, **values):
        self.ensure_one()
        creds = self._get_gmail_credentials()  # <--- Appel des identifiants par société

        response = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'client_id': creds['client_id'],
                'client_secret': creds['client_secret'],
                'grant_type': grant_type,
                'redirect_uri': url_join(self.get_base_url(), '/google_gmail/confirm'),
                **values,
            },
            timeout=5,
        )
        if not response.ok:
            raise UserError(_('Erreur lors de la récupération du token Gmail.'))
        return response.json()