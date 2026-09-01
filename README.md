# Élise Why

Intégration Home Assistant **strictement en lecture seule** qui relie un agent conversationnel à **Élise Investigator**, moteur causal local et déterministe.

**Candidate : 0.2.0-dev.20**

## Rôle

Élise Why ne détermine pas elle-même les causes.

`question naturelle → LLM Home Assistant → InvestigateWhy → Élise Investigator → preuve JSON → restitution Élise Why`

L'outil `InvestigateWhy` peut résoudre une entité exposée par `entity_id`, nom, domaine ou zone. Une demande explicitement plurielle doit investiguer plusieurs cibles sans demander une clarification inutile.

Pour une question simple d'état courant comme « Pourquoi le volet est fermé ? », Élise Why demande à Investigator la dernière cause du dernier changement pertinent et ne transmet aucun `observed_time` implicite. Un repère temporel n'est transmis que lorsque l'utilisateur fournit explicitement une date ou une heure.

Élise Why **n'intercepte pas les commandes**. Une demande comme « allume la lampe » ou « mets le volet à 30 % » doit continuer à utiliser les outils de pilotage standards de l'API Assist. `InvestigateWhy` est réservé aux questions causales de type « pourquoi ? ».

## Niveau de réponse

Dans **Paramètres → Appareils et services → Élise Why → Configurer**, trois niveaux sont proposés :

- `Humaine` — valeur par défaut ; réponse courte centrée sur la cause essentielle.
- `Détaillée` — quelques phrases avec la cause et le contexte utile.
- `Complète` — restitution causale complète.

Les verdicts Investigator `confirmed`, `probable` et `indeterminate` restent immuables.

## Sécurité

Élise Why reste strictement en lecture seule : aucun service mutateur, aucune modification d'état Home Assistant, aucune modification d'Investigator.

## Compatibilité

Candidate dev.20 basée sur la dev.18 en service. Le correctif causal conserve également l'outil `AnalyseThermique` présent dans la version publiée.
