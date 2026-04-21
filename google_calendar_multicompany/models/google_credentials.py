# -*- coding: utf-8 -*-
import logging
import requests
from datetime import timedelta

from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.addons.google_account.models.google_service import GOOGLE_TOKEN_ENDPOINT

_logger = logging.getLogger(__name__)


class GoogleCredentials(models.Model):
    _inherit = 'google.calendar.credentials'

    def _refresh_google_calendar_token(self):
        self.ensure_one()

        user = self.user_ids[:1]
        company = user.company_id if user else self.env.company

        client_id = company.google_calendar_client_id
        client_secret = company.google_calendar_client_secret

        if not client_id or not client_secret:
            raise UserError(_(
                "Le service Google Agenda n'est pas configuré pour la société %s. "
                "Veuillez configurer le Client ID et le Client Secret sur la fiche société.",
                company.name
            ))

        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {
            'refresh_token': self.calendar_rtoken,
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'refresh_token',
        }

        try:
            _dummy, response, _dummy = self.env['google.service']._do_request(
                GOOGLE_TOKEN_ENDPOINT,
                params=data,
                headers=headers,
                method='POST',
                preuri=''
            )

            ttl = response.get('expires_in')
            self.write({
                'calendar_token': response.get('access_token'),
                'calendar_token_validity': fields.Datetime.now() + timedelta(seconds=ttl),
            })
            _logger.info("Google Calendar: Token rafraîchi avec succès pour la société %s", company.name)

        except requests.HTTPError as error:
            if error.response.status_code in (400, 401):
                self.env.cr.rollback()
                self._set_auth_tokens(False, False, 0)
                self.env.cr.commit()

            error_key = error.response.json().get("error", "nc")
            error_msg = _(
                "Une erreur est survenue lors de la génération du token pour la société %s. "
                "Votre code d'autorisation est peut-être invalide ou a expiré [%s].",
                company.name, error_key
            )
            raise UserError(error_msg)