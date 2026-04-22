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

    def _get_company(self):
        """
        Résout la société à partir des utilisateurs liés à ce credential.

        Stratégie :
        - Si un seul utilisateur est lié → on prend sa société principale.
        - Si plusieurs utilisateurs → on vérifie qu'ils partagent la même société
          pour éviter d'utiliser les mauvais identifiants. Si les sociétés diffèrent,
          on lève une erreur explicite.
        - Si aucun utilisateur → fallback sur self.env.company
        """
        self.ensure_one()
        users = self.user_ids
        if not users:
            return self.env.company

        companies = users.mapped('company_id')
        unique_companies = companies.filtered(lambda c: c.id in companies.ids)

        # Dédoublonnage via set pour ne garder que les sociétés distinctes
        distinct_companies = self.env['res.company'].browse(
            list({c.id for c in companies})
        )

        if len(distinct_companies) > 1:
            # Plusieurs sociétés distinctes → situation ambiguë, on log et on
            # prend la société de l'utilisateur courant si disponible, sinon la première.
            current_user_company = self.env.user.company_id
            if current_user_company in distinct_companies:
                _logger.warning(
                    "Google Calendar Credentials #%s : liés à plusieurs sociétés (%s). "
                    "Utilisation de la société courante : %s.",
                    self.id,
                    ', '.join(distinct_companies.mapped('name')),
                    current_user_company.name,
                )
                return current_user_company
            _logger.warning(
                "Google Calendar Credentials #%s : liés à plusieurs sociétés (%s). "
                "Utilisation de la première société trouvée : %s.",
                self.id,
                ', '.join(distinct_companies.mapped('name')),
                distinct_companies[0].name,
            )

        return distinct_companies[0]

    def _refresh_google_calendar_token(self):
        self.ensure_one()

        company = self._get_company()
        client_id = company.google_calendar_client_id
        client_secret = company.google_calendar_client_secret

        # Fallback sur les paramètres globaux si la société n'a pas de credentials dédiés.
        if not client_id or not client_secret:
            ICP = self.env['ir.config_parameter'].sudo()
            client_id = ICP.get_param('google_calendar_client_id')
            client_secret = ICP.get_param('google_calendar_client_secret')

        if not client_id or not client_secret:
            raise UserError(_(
                "Le service Google Agenda n'est pas configuré pour la société « %s ». "
                "Veuillez renseigner le Client ID et le Client Secret sur la fiche société "
                "ou dans les Paramètres généraux.",
                company.name,
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
                preuri='',
            )

            ttl = response.get('expires_in', 3600)
            self.write({
                'calendar_token': response.get('access_token'),
                'calendar_token_validity': fields.Datetime.now() + timedelta(seconds=ttl),
            })
            _logger.info(
                "Google Calendar : token rafraîchi avec succès pour la société « %s ».",
                company.name,
            )

        except requests.HTTPError as error:
            if error.response.status_code in (400, 401):
                with self.env.cr.savepoint():
                    self._set_auth_tokens(False, False, 0)
                _logger.warning(
                    "Google Calendar : tokens invalidés pour la société « %s » "
                    "suite à une erreur %s.",
                    company.name,
                    error.response.status_code,
                )

            error_key = error.response.json().get("error", "nc")
            raise UserError(_(
                "Une erreur est survenue lors du rafraîchissement du token pour la société « %s ». "
                "Le code d'autorisation est peut-être invalide ou révoqué [%s]. "
                "Veuillez reconnecter votre compte Google Calendar.",
                company.name,
                error_key,
            )) from error