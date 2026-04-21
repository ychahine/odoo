# models/google_service.py
from odoo import models, api
from odoo.addons.google_account.models.google_service import GOOGLE_TOKEN_ENDPOINT


class GoogleServiceMultiCompany(models.AbstractModel):
    _inherit = 'google.service'

    def _get_client_id(self, service):
        if service == 'calendar':
            company = self.env.user.company_id
            client_id = company.google_calendar_client_id
            if client_id:
                return client_id

        return super()._get_client_id(service)

    @api.model
    def _get_google_tokens(self, authorize_code, service, redirect_uri):
        if service == 'calendar' and self.env.company.google_calendar_client_secret:
            client_id = self.env.company.google_calendar_client_id
            client_secret = self.env.company.google_calendar_client_secret

            headers = {"content-type": "application/x-www-form-urlencoded"}
            data = {
                'code': authorize_code,
                'client_id': client_id,
                'client_secret': client_secret,
                'grant_type': 'authorization_code',
                'redirect_uri': redirect_uri
            }

            dummy, response, dummy = self._do_request(
                GOOGLE_TOKEN_ENDPOINT,
                params=data,
                headers=headers,
                method='POST',
                preuri=''
            )

            return response.get('access_token'), response.get('refresh_token'), response.get('expires_in')

        # Fallback pour Gmail ou si non configuré sur la société
        return super()._get_google_tokens(authorize_code, service, redirect_uri)