# -*- coding: utf-8 -*-
{
    'name': 'Google Gmail Multi-Company oAuth',
    'version': '17.0.1.0.0',
    'category': 'Productivity/Mail',
    'summary': 'Chaque société utilise ses propres identifiants OAuth Gmail (Client ID & Secret).',
    'description': """
        Google Gmail Multi-Company Support
        ==================================
        Ce module corrige la limitation native d'Odoo qui impose un seul Client ID et Client Secret Gmail pour toute l'instance.
        
        Points clés :
        -------------
        * **Configuration par société** : Déplace le Client ID et le Client Secret Gmail des paramètres systèmes vers la fiche Société.
        * **Support Multi-Sociétés** : Permet à chaque société de posséder son propre projet Google Cloud Console.
        * **Serveurs de mail dédiés** : Ajoute le support de la société sur les serveurs de messagerie sortants (ir.mail_server).
        * **Workflow OAuth isolé** : Le processus d'authentification utilise automatiquement les identifiants de la société liée au serveur.
        * **Interface épurée** : Masque les anciens champs globaux dans les paramètres généraux pour éviter les erreurs de configuration.
        
        Idéal pour les environnements multi-sociétés utilisant des domaines Google Workspace différents.
    """,
    'author': 'Youssef CHAHINE',
    'company': 'Youssef CHAHINE',
    'maintainer': 'Youssef CHAHINE',
    'website': 'youssef.chahine@gmail.com',
    'depends': [
        'base',
        'mail',
        'google_gmail',
    ],
    'data': [
        'security/ir_mail_server_rules.xml',
        'views/res_company_views.xml',
        'views/ir_mail_server_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'price': 50,
    'currency': 'USD',
    'installable': True,
    'application': False,
    'auto_install': False,
}
