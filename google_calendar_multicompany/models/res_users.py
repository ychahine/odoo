# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, Command
from odoo.addons.google_calendar.utils.google_calendar import GoogleCalendarService

_logger = logging.getLogger(__name__)


class User(models.Model):
    _inherit = 'res.users'

    def _get_google_sync_status(self):
        """
        Vérifie si la synchronisation est active, en pause ou arrêtée
        en se basant sur la configuration de la société de l'utilisateur.
        """
        self.ensure_one()
        status = "sync_active"

        # On utilise la société rattachée à l'utilisateur (self.company_id)
        if self.company_id.cal_sync_paused:
            status = "sync_paused"
        elif self.google_synchronization_stopped:
            status = "sync_stopped"
        return status

    def unpause_google_synchronization(self):
        """ Désactive la pause sur la société de l'utilisateur """
        self.ensure_one()
        self.company_id.sudo().cal_sync_paused = False

    def pause_google_synchronization(self):
        """ Active la pause sur la société de l'utilisateur """
        self.ensure_one()
        self.company_id.sudo().cal_sync_paused = True

    @api.model
    def check_calendar_credentials(self):
        """
        Utilisé par le frontend (JS) pour afficher ou non le bouton de synchronisation.
        Vérifie les credentials sur la société actuelle de l'interface.
        """
        res = super(User, self).check_calendar_credentials()

        # Ici on utilise self.env.company pour refléter la société sélectionnée à l'écran
        company = self.env.company
        client_id = company.google_calendar_client_id
        client_secret = company.google_calendar_client_secret

        res['google_calendar'] = bool(client_id and client_secret)
        return res

    def restart_google_synchronization(self):
        """ 
        Surcharge pour éviter l'erreur d'accès lors de la réinitialisation.
        Le sudo() permet de manipuler les records techniques (partners) 
        qui pourraient appartenir à une autre société.
        """
        self.ensure_one()
        _logger.info("Réinitialisation du compte Google Agenda pour l'utilisateur %s", self.name)
        return super(User, self.sudo()).restart_google_synchronization()

    def _sync_google_calendar(self, calendar_service: GoogleCalendarService):
        """
        Surcharge de la synchronisation pour passer en sudo().
        Cela évite les blocages si un participant à un événement (res.partner)
        appartient à une autre société que l'utilisateur.
        """
        self.ensure_one()
        # On force le contexte de la société de l'utilisateur et on passe en sudo
        # pour bypasser les Record Rules sur les partenaires/événements.
        return super(User, self.sudo().with_context(allowed_company_ids=[self.company_id.id]))._sync_google_calendar(
            calendar_service)

    @api.model
    def _sync_all_google_calendar(self):
        """
        Cron job : Synchronise tous les utilisateurs ayant un jeton valide.
        """
        users = self.env['res.users'].search([
            ('google_calendar_rtoken', '!=', False),
            ('google_synchronization_stopped', '=', False)
        ])

        # Initialisation du service Google
        google_service = GoogleCalendarService(self.env['google.service'])

        for user in users:
            _logger.info("Calendar Synchro - Starting synchronization for %s (Company: %s)", user.name,
                         user.company_id.name)
            try:
                # On utilise with_user et sudo pour garantir que le cron 
                # a les droits nécessaires sur toutes les sociétés
                user.with_user(user).sudo()._sync_google_calendar(google_service)
                self.env.cr.commit()
            except Exception as e:
                _logger.error("Calendar Synchro - Exception pour l'utilisateur %s : %s", user.name, str(e))
                self.env.cr.rollback()