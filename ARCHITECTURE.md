# Architecture — Élise Why dev.17

## Décision

Élise Why n'est plus un second moteur causal. Elle devient une façade Home Assistant LLM, strictement en lecture seule, vers Élise Investigator.

Le moteur déterministe et les verdicts `confirmed` / `probable` / `indeterminate` restent la responsabilité exclusive d'Élise Investigator.

## Chaîne dev.17

Utilisateur
→ agent conversationnel Home Assistant / LLM
→ outil `InvestigateWhy`
→ Élise Why
→ API locale `POST /api/v1/investigate`
→ Élise Investigator
→ JSON de preuve inchangé
→ formulation naturelle par l'IA

## Résolution des objets

L'outil accepte soit un `entity_id` exact, soit des critères Home Assistant (`name`, `domain`, `area`).

La résolution est faite avec le moteur de ciblage Home Assistant et uniquement parmi les entités exposées à l'assistant.

Une cible ambiguë est refusée. `all_matches=true` n'est autorisé que lorsque la demande est explicitement plurielle, par exemple « les volets ».

## Réseau et authentification

- Le slug réel de l'App Investigator est obtenu via `get_apps_list()`.
- Pour compatibilité avec Home Assistant 2026.8.2, l'hostname interne est dérivé par remplacement `_` → `-`, comme dans Maison Élise Bridge.
- Le port 8099 reste interne au réseau Supervisor et n'est pas exposé au LAN.
- Les appels directs utilisent le Bearer token Investigator stocké dans la config entry Home Assistant.
- Le token n'est jamais placé dans le prompt LLM ni retourné par l'outil.

## Invariants

1. Aucun service de commande n'est appelé par Élise Why.
2. Aucun état Home Assistant n'est modifié.
3. Élise Why ne lit plus Logbook/Recorder pour déterminer une cause.
4. L'IA ne peut jamais augmenter un niveau de certitude Investigator.
5. Un statut inconnu ou une réponse associée à une autre `entity_id` est rejeté.
6. Une indisponibilité Investigator reste une indisponibilité, jamais une cause plausible.
7. Plusieurs résultats sont conservés séparément avant synthèse par l'IA.
8. Maison Élise Bridge / Alexa est hors périmètre dev.17 et n'est pas modifié.

## Compatibilité V0.1

L'action réponse seule `elise_why.explain` est conservée pendant la transition mais elle appelle désormais Investigator.

Les anciens fichiers `engine.py` et `logbook_provider.py` restent temporairement dans le dépôt pour faciliter comparaison et rollback, mais ils ne sont plus importés par le runtime dev.17.
