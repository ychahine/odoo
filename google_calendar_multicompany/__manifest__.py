# -*- coding: utf-8 -*-
{
    'name': 'Google Calendar Multi-Company Sync Fix',
    'version': '17.0.1.1.0', # Incrément de version recommandé
    'category': 'Productivity/Calendar',
    'summary': 'Synchronisation Google Calendar isolée par société (Client ID & Secret dédiés).',
    'description': """
Google Calendar Multi-Company Integration
=========================================
Ce module étend la gestion multi-sociétés à la synchronisation Google Calendar, résolvant le conflit natif d'identifiants uniques sur Odoo.

Problématique résolue :
-----------------------
Nativement, Odoo utilise une seule paire de Client ID / Client Secret pour tous les utilisateurs de l'instance. Dans un environnement multi-sociétés (domaines différents, entités juridiques séparées), cela empêche la synchronisation des agendas pour les filiales n'appartenant pas au projet Google Cloud principal.

Points clés du module :
-----------------------
* **Isolation des Identifiants Calendar** : Utilise le Client ID et le Client Secret spécifiques à chaque société pour les flux Google Calendar.
* **Redirection OAuth Dynamique** : Adapte l'URL de redirection et la validation des jetons (Tokens) en fonction de la société active de l'utilisateur.
* **Compatibilité Multi-Domaines** : Permet à la Société A d'utiliser @domaine-a.com et à la Société B d'utiliser @domaine-b.com sans conflit de consentement.
* **Gestion des Tokens (Access/Refresh)** : Garantit que les jetons de synchronisation sont liés au bon projet Google Cloud Console.
* **Continuité d'Expérience** : Les utilisateurs cliquent sur le bouton "Synchroniser" habituel, mais le module route la requête vers les bons secrets en arrière-plan.

Infrastructures supportées :
----------------------------
Idéal pour les déploiements Odoo où chaque entité possède son propre Google Workspace et nécessite une étanchéité totale des accès API.
    """,
    'author': 'Youssef CHAHINE',
    'company': 'Youssef CHAHINE',
    'maintainer': 'Youssef CHAHINE',
    'website': 'youssef.chahine@gmail.com',
    'depends': [
        'base',
        'google_account',
        'google_calendar',
    ],
    'data': [
        'views/res_company_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'price': 100,
    'currency': 'EUR',
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
