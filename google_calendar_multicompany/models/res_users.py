# -*- coding: utf-8 -*-
import logging

from odoo import api, models, _
from odoo.addons.google_calendar.utils.google_calendar import GoogleCalendarService

_logger = logging.getLogger(__name__)


class User(models.Model):
    _inherit = 'res.users'

    def _get_google_sync_status(self):
        """
        Retourne le statut de synchronisation de l'utilisateur :
        - 'sync_paused'  : la société de l'utilisateur a mis la synchro en pause.
        - 'sync_stopped' : l'utilisateur a explicitement arrêté sa synchro.
        - 'sync_active'  : synchronisation active.
        """
        self.ensure_one()
        if self.company_id.cal_sync_paused:
            return "sync_paused"
        if self.google_synchronization_stopped:
            return "sync_stopped"
        return "sync_active"

    def pause_google_synchronization(self):
        """
        Met en pause la synchronisation Google Calendar pour la société
        de l'utilisateur courant.
        """
        self.ensure_one()
        _logger.info(
            "Google Calendar : synchronisation mise en pause pour la société « %s » "
            "(demandée par l'utilisateur %s).",
            self.company_id.name, self.name,
        )
        self.company_id.sudo().cal_sync_paused = True

    def unpause_google_synchronization(self):
        """
        Reprend la synchronisation Google Calendar pour la société
        de l'utilisateur courant.
        """
        self.ensure_one()
        _logger.info(
            "Google Calendar : synchronisation reprise pour la société « %s » "
            "(demandée par l'utilisateur %s).",
            self.company_id.name, self.name,
        )
        self.company_id.sudo().cal_sync_paused = False

    @api.model
    def check_calendar_credentials(self):
        """
        Indique au frontend si les credentials Google Calendar sont configurés
        pour la société actuellement sélectionnée dans l'interface.

        On délègue d'abord à super() pour conserver les éventuelles vérifications
        natives (ex. gmail), puis on écrase uniquement le flag 'google_calendar'.
        """
        res = super().check_calendar_credentials()

        company = self.env.company
        client_id = (company.google_calendar_client_id or '').strip()
        client_secret = (company.google_calendar_client_secret or '').strip()

        # Fallback sur les paramètres système si la société n'a pas de credentials dédiés
        if not (client_id and client_secret):
            ICP = self.env['ir.config_parameter'].sudo()
            client_id = (ICP.get_param('google_calendar_client_id') or '').strip()
            client_secret = (ICP.get_param('google_calendar_client_secret') or '').strip()

        res['google_calendar'] = bool(client_id and client_secret)
        return res

    def restart_google_synchronization(self):
        """
        Réinitialise le compte Google Calendar de l'utilisateur.

        Le sudo() est nécessaire pour manipuler les records techniques (res.partner,
        calendar.event) qui peuvent appartenir à une autre société que l'utilisateur,
        notamment en contexte multi-société strict.
        """
        self.ensure_one()
        _logger.info(
            "Google Calendar : réinitialisation pour l'utilisateur « %s » (société : %s).",
            self.name, self.company_id.name,
        )
        return super(User, self.sudo()).restart_google_synchronization()

    def _sync_google_calendar(self, calendar_service: GoogleCalendarService):
        """
        Synchronise le calendrier Google de cet utilisateur.

        Le sudo() combiné à allowed_company_ids permet de traiter les événements
        et partenaires appartenant à d'autres sociétés (ex. invités externes,
        events partagés entre filiales) sans lever d'erreur d'accès.
        """
        self.ensure_one()
        return super(User, self.sudo().with_context(allowed_company_ids=[self.company_id.id]))._sync_google_calendar(calendar_service)

    @api.model
    def _sync_all_google_calendar(self):
        """
        Point d'entrée du cron de synchronisation Google Calendar.

        Filtre les utilisateurs éligibles :
        - Possèdent un refresh token valide.
        - N'ont pas arrêté manuellement leur synchronisation.
        - La société associée n'a pas la synchronisation en pause.

        Chaque utilisateur est traité dans une transaction indépendante :
        une erreur sur un utilisateur n'empêche pas la synchronisation des suivants.
        """
        users = self.env['res.users'].search([
            ('google_calendar_rtoken', '!=', False),
            ('google_synchronization_stopped', '=', False),
            ('company_id.cal_sync_paused', '=', False),
        ])

        if not users:
            _logger.info("Google Calendar Cron : aucun utilisateur éligible à la synchronisation.")
            return

        _logger.info(
            "Google Calendar Cron : démarrage pour %d utilisateur(s).", len(users)
        )

        google_service = GoogleCalendarService(self.env['google.service'])

        success_count = 0
        error_count = 0

        for user in users:
            _logger.info(
                "Google Calendar Cron : synchronisation de « %s » (société : %s).",
                user.name, user.company_id.name,
            )
            try:
                user.with_user(user).sudo()._sync_google_calendar(google_service)
                self.env.cr.commit()
                success_count += 1
            except Exception:
                _logger.exception(
                    "Google Calendar Cron : erreur pour l'utilisateur « %s » (société : %s).",
                    user.name, user.company_id.name,
                )
                self.env.cr.rollback()
                error_count += 1

        _logger.info(
            "Google Calendar Cron : terminé — %d succès, %d erreur(s).",
            success_count, error_count,
        )