# Changelog

## 0.2.0-dev.19

- Corrige l’aiguillage Assist identifié en recette dev.29 : l’outil LLM `InvestigateWhy` n’appelle plus la recherche approfondie historique `POST /api/v1/investigate`.
- Élise Why utilise désormais le nouvel endpoint structuré `POST /api/v1/why` d’Investigator, conçu pour consulter d’abord le journal causal puis lancer l’enquête approfondie uniquement si le réglage de secours l’autorise.
- Le contrat reçu par le LLM reste volontairement compact : verdict, entité, événement/heure utiles, raison fonctionnelle ou source directe prouvée. Les noms d’automatisations et traces détaillées restent dans Investigator.
- La résolution des cibles exposées à Assist, les règles de pluralité, les niveaux de restitution et l’acquittement « Je regarde… » restent inchangés.
- Les verdicts `confirmed`, `probable`, `indeterminate` restent immuables ; Élise Why ne déduit aucune cause supplémentaire.
- Aucun service mutateur ni droit Home Assistant supplémentaire n’est ajouté.

## 0.2.0-dev.18

- Ajoute dans les options Élise Why trois niveaux de restitution : `Humaine`, `Détaillée`, `Complète`.
- Le mode `Humaine` est le réglage par défaut et vise une réponse naturelle très courte ; le mode `Complète` conserve la richesse de la restitution dev.17.
- Ajoute un prompt complémentaire optionnel limité au style de réponse et plafonné à 500 caractères.
- Le prompt utilisateur ne peut pas remplacer les règles de preuve, de sécurité, de ciblage ou de certitude Investigator.
- Renforce le routage Assist : `InvestigateWhy` est réservé aux questions causales ; les demandes de pilotage doivent utiliser les outils Assist standards de Home Assistant.
- Renforce la pluralité naturelle : une formulation explicitement plurielle doit utiliser `all_matches=true` sans demander de clarification inutile.
- Demande un acquittement bref « Je regarde… » avant l'investigation lorsque le transport conversationnel permet d'afficher du texte avant l'appel d'outil ; sinon l'investigation démarre immédiatement.
- Les options sont relues à chaque requête LLM : aucun redémarrage ni rechargement d'Investigator n'est nécessaire pour changer le niveau de réponse.
- Aucun changement du moteur causal Investigator, de Maison Élise Bridge/Alexa ou de Home Assistant installé.

## 0.2.0-dev.17

- Transforme Élise Why en façade LLM Home Assistant vers Élise Investigator.
- Ajoute le client local authentifié `POST /api/v1/investigate`.
- Détecte dynamiquement le slug complet de l'App Investigator via Supervisor ; aucun hash de dépôt n'est codé en dur.
- Ajoute l'outil LLM natif `InvestigateWhy` pour l'API Assist.
- Résout les cibles via Home Assistant parmi les entités exposées à l'assistant ; ambiguïté refusée, pluralité explicite supportée.
- Préserve strictement les verdicts `confirmed`, `probable`, `indeterminate` et rejette tout statut inconnu.
- Conserve `elise_why.explain` comme action de compatibilité, désormais proxifiée vers Investigator.
- Ajoute un flux de réauthentification pour les installations V0.1 existantes sans jeton Investigator.
- Retire Logbook/Recorder du chemin runtime d'Élise Why ; les anciens fichiers restent temporairement présents pour rollback/comparaison.
- Aucun changement du moteur causal Investigator, de Maison Élise Bridge/Alexa ou de Home Assistant installé.
