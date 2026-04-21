# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.google_calendar.controllers.main import GoogleCalendarController


class GoogleCalendarControllerMultiCompany(GoogleCalendarController):

    @http.route()
    def check_calendar_credentials(self):
        res = super(GoogleCalendarControllerMultiCompany, self).check_calendar_credentials()
        company = request.env.company

        client_id = company.google_gmail_client_identifier
        client_secret = company.google_gmail_client_secret

        if client_id and client_secret:
            res['google_calendar'] = True

        return res