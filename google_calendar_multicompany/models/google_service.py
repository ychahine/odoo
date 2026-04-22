# -*- coding: utf-8 -*-
import logging

from odoo import models, api, _
from odoo.exceptions import UserError
from odoo.addons.google_account.models.google_service import GOOGLE_TOKEN_ENDPOINT

_logger = logging.getLogger(__name__)


class GoogleServiceMultiCompany(models.AbstractModel):
    _inherit = 'google.service'


    def _get_company_calendar_credentials(self):
        """
        Retourne (client_id, client_secret) pour la société active,
        en appliquant un fallback sur les paramètres système globaux.

        Retourne (None, None) si aucune configuration n'est trouvée,
        ce qui permet à l'appelant de décider s'il doit fallback sur super().
        """
        company = self.env.company
        client_id = (company.google_calendar_client_id or '').strip()
        client_secret = (company.google_calendar_client_secret or '').strip()

        if client_id and client_secret:
            _logger.debug(
                "Google Calendar : utilisation des credentials de la société « %s ».",
                company.name,
            )
            return client_id, client_secret

        # Fallback explicite sur les paramètres système (compatibilité mono-société)
        ICP = self.env['ir.config_parameter'].sudo()
        global_id = (ICP.get_param('google_calendar_client_id') or '').strip()
        global_secret = (ICP.get_param('google_calendar_client_secret') or '').strip()

        if global_id and global_secret:
            _logger.debug(
                "Google Calendar : credentials non configurés sur la société « %s », "
                "utilisation des paramètres système globaux.",
                company.name,
            )
            return global_id, global_secret

        return None, None

    def _get_client_id(self, service):
        """
        Surcharge pour retourner le Client ID de la société active
        quand le service est 'calendar'.
        """
        if service == 'calendar':
            client_id, _secret = self._get_company_calendar_credentials()
            if client_id:
                return client_id

        return super()._get_client_id(service)

    @api.model
    def _get_google_tokens(self, authorize_code, service, redirect_uri):
        """
        Surcharge pour échanger le code d'autorisation OAuth contre des tokens,
        en utilisant les credentials de la société active pour le service 'calendar'.

        Fallback transparent vers super() si :
        - le service n'est pas 'calendar'
        - aucun credential n'est configuré (société ni global)
        """
        if service != 'calendar':
            return super()._get_google_tokens(authorize_code, service, redirect_uri)

        client_id, client_secret = self._get_company_calendar_credentials()

        if not client_id or not client_secret:
            # Aucun credential trouvé → on laisse super() gérer (comportement natif)
            _logger.warning(
                "Google Calendar : aucun credential configuré pour la société « %s ». "
                "Fallback sur le comportement Odoo natif.",
                self.env.company.name,
            )
            return super()._get_google_tokens(authorize_code, service, redirect_uri)

        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {
            'code': authorize_code,
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
        }

        try:
            _dummy, response, _dummy = self._do_request(
                GOOGLE_TOKEN_ENDPOINT,
                params=data,
                headers=headers,
                method='POST',
                preuri='',
            )
        except Exception as e:
            _logger.error(
                "Google Calendar : échec de l'échange du code OAuth pour la société « %s » : %s",
                self.env.company.name,
                str(e),
            )
            raise UserError(_(
                "Impossible d'obtenir les tokens Google Calendar pour la société « %s ». "
                "Vérifiez que le Client ID et le Client Secret sont corrects et que "
                "l'URI de redirection est bien autorisée dans la Google Cloud Console.\n\n"
                "Détail technique : %s",
                self.env.company.name,
                str(e),
            )) from e

        access_token = response.get('access_token')
        refresh_token = response.get('refresh_token')
        expires_in = response.get('expires_in')

        if not access_token:
            raise UserError(_(
                "Google Calendar : la réponse OAuth pour la société « %s » "
                "ne contient pas d'access_token. Réponse reçue : %s",
                self.env.company.name,
                response,
            ))

        return access_token, refresh_token, expires_in