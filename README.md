# Élise Why

Intégration Home Assistant **strictement en lecture seule** qui relie un agent conversationnel à **Élise Investigator**, moteur causal local et déterministe.

**Candidate : 0.2.0-dev.18**

## Rôle

Élise Why ne détermine pas elle-même les causes.

`question naturelle → LLM Home Assistant → InvestigateWhy → Élise Investigator → preuve JSON → restitution Élise Why`

L'outil `InvestigateWhy` peut résoudre une entité exposée par `entity_id`, nom, domaine ou zone. Une demande explicitement plurielle doit investiguer plusieurs cibles sans demander une clarification inutile.

Élise Why **n'intercepte pas les commandes**. Une demande comme « allume la lampe » ou « mets le volet à 30 % » doit continuer à utiliser les outils de pilotage standards de l'API Assist. `InvestigateWhy` est réservé aux questions causales de type « pourquoi ? ».

## Niveau de réponse

Dans **Paramètres → Appareils et services → Élise Why → Configurer**, trois niveaux sont proposés :

- `Humaine` — valeur par défaut ; une réponse naturelle très courte, centrée sur la cause essentielle.
- `Détaillée` — quelques phrases avec la cause, l'heure et l'origine utiles.
- `Complète` — restitution causale complète, proche du comportement dev.17.

Un **prompt complémentaire** optionnel peut personnaliser le ton ou la formulation. Il est limité au style et ne peut pas modifier la preuve, le routage des outils, la sécurité ou la certitude Investigator.

Quand le transport conversationnel le permet, Élise Why demande au modèle d'émettre un bref « Je regarde… » avant l'appel à Investigator. Ce comportement reste dépendant des capacités de streaming de l'agent conversationnel.

## Garantie de preuve

Les verdicts Investigator sont immuables :
- `confirmed`
- `probable`
- `indeterminate`

Élise Why transmet les résultats sans augmenter leur certitude. Une réponse invalide, une cible ambiguë ou un Investigator indisponible produit une erreur explicite plutôt qu'une cause inventée.

## Sécurité

Élise Why :
- ne commande elle-même aucun équipement ;
- ne modifie aucun état Home Assistant ;
- n'appelle aucun service mutateur ;
- laisse les commandes ordinaires aux outils Assist standards ;
- n'expose pas le port 8099 au LAN ;
- utilise uniquement le réseau interne Supervisor pour joindre Investigator ;
- garde le Bearer token Investigator dans la config entry Home Assistant ;
- ne transmet jamais ce token au modèle IA.

## Mise à niveau depuis 0.1.0

La config entry V0.1 ne contient pas encore de jeton Investigator. Après installation de dev.17 ou ultérieur, Home Assistant demandera une reconnexion :

1. Ouvrir Élise Investigator dans Home Assistant et copier son jeton API local.
2. Ouvrir la demande de reconnexion Élise Why.
3. Coller le jeton dans le champ masqué.
4. Élise Why détecte automatiquement le slug complet de l'App et vérifie la connexion.

Aucune suppression/réinstallation de l'intégration n'est nécessaire.

## Compatibilité

La candidate est conçue pour Home Assistant 2026.8.2. Le raccordement LLM repose sur le mécanisme natif `llm.py` / `async_get_tools()` de l'API Assist : les outils fournis par les intégrations sont assemblés avec les outils Assist standards.

L'action `elise_why.explain` est conservée temporairement pour compatibilité, mais elle est désormais un proxy vers `POST /api/v1/investigate`.

Les anciens `engine.py` et `logbook_provider.py` sont conservés temporairement comme archive de transition et ne participent plus au runtime.

## État

Cette branche est une candidate de développement. Elle doit passer HACS, hassfest, tests unitaires puis un test runtime contrôlé sur HAOS avant toute fusion sur `main`.
