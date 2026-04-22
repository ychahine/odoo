# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.google_calendar.controllers.main import GoogleCalendarController


class GoogleCalendarControllerMultiCompany(GoogleCalendarController):

    @http.route()
    def check_calendar_credentials(self):
        """
        Surcharge du contrôleur natif pour vérifier les credentials Calendar
        de la société active.

        On vérifie en priorité les credentials dédiés à la société.
        Si absents, on accepte le fallback sur les paramètres système globaux
        (comportement natif Odoo) pour rester compatible avec les configurations
        mono-société existantes.
        """
        res = super().check_calendar_credentials()

        company = request.env.company

        # Credentials dédiés à la société
        client_id = (company.google_calendar_client_id or '').strip()
        client_secret = (company.google_calendar_client_secret or '').strip()

        if client_id and client_secret:
            res['google_calendar'] = True
            return res

        # Fallback : paramètres système globaux
        ICP = request.env['ir.config_parameter'].sudo()
        global_id = (ICP.get_param('google_calendar_client_id') or '').strip()
        global_secret = (ICP.get_param('google_calendar_client_secret') or '').strip()

        if global_id and global_secret:
            res['google_calendar'] = True
        else:
            res['google_calendar'] = False

        return res