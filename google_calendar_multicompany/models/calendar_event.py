# -*- coding: utf-8 -*-
import logging
from odoo import models


_logger = logging.getLogger(__name__)


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    def write(self, values):
        if set(values.keys()) == {'need_sync'}:
            try:
                return super().write(values)
            except Exception:
                _logger.debug(
                    "Google Calendar : write(need_sync) bloqué par Record Rules "
                    "pour l'utilisateur %s (uid=%s) sur %d event(s) — "
                    "contournement sudo activé pour ce champ technique.",
                    self.env.user.name,
                    self.env.user.id,
                    len(self),
                )
                return super(CalendarEvent, self.sudo()).write(values)

        return super().write(values)