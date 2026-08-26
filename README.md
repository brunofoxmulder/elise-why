# Élise Why

Intégration Home Assistant **strictement en lecture seule** qui relie un agent conversationnel à **Élise Investigator**, moteur causal local et déterministe.

**Candidate : 0.2.0-dev.17**

## Rôle dev.17

Élise Why ne détermine plus elle-même les causes.

`question naturelle → LLM Home Assistant → InvestigateWhy → Élise Why → Élise Investigator → preuve JSON → réponse naturelle`

L'outil `InvestigateWhy` peut résoudre une entité exposée par `entity_id`, nom, domaine ou zone. Une demande explicitement plurielle peut investiguer plusieurs cibles, par exemple tous les volets exposés.

## Garantie de preuve

Les verdicts Investigator sont immuables :
- `confirmed`
- `probable`
- `indeterminate`

Élise Why transmet les résultats sans augmenter leur certitude. Une réponse invalide, une cible ambiguë ou un Investigator indisponible produit une erreur explicite plutôt qu'une cause inventée.

## Sécurité

Élise Why :
- ne commande aucun équipement ;
- ne modifie aucun état Home Assistant ;
- n'appelle aucun service mutateur ;
- n'expose pas le port 8099 au LAN ;
- utilise uniquement le réseau interne Supervisor pour joindre Investigator ;
- garde le Bearer token Investigator dans la config entry Home Assistant ;
- ne transmet jamais ce token au modèle IA.

## Mise à niveau depuis 0.1.0

La config entry V0.1 ne contient pas encore de jeton Investigator. Après installation de dev.17, Home Assistant demandera une reconnexion :

1. Ouvrir Élise Investigator dans Home Assistant et copier son jeton API local.
2. Ouvrir la demande de reconnexion Élise Why.
3. Coller le jeton dans le champ masqué.
4. Élise Why détecte automatiquement le slug complet de l'App et vérifie la connexion.

Aucune suppression/réinstallation de l'intégration n'est nécessaire.

## Compatibilité

La candidate est conçue pour Home Assistant 2026.8.2. Le raccordement LLM repose sur le mécanisme natif `llm.py` / `async_get_tools()` de l'API Assist.

L'action `elise_why.explain` est conservée temporairement pour compatibilité, mais elle est désormais un proxy vers `POST /api/v1/investigate`.

Les anciens `engine.py` et `logbook_provider.py` sont conservés temporairement comme archive de transition et ne participent plus au runtime dev.17.

## État

Cette branche est une candidate de développement. Elle doit passer HACS, hassfest, tests unitaires puis un test runtime contrôlé sur HAOS avant fusion sur `main` ou installation.
