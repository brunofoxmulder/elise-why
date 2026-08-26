# Changelog

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
