# Élise Why

Intégration Home Assistant **strictement en lecture seule** destinée à expliquer la dernière action causale observée sur une entité.

**Version actuelle : 0.1.0**

## Objectif V0.1

`entity_id -> dernier événement causal réel -> contexte Home Assistant -> explication courte`

Verdicts :
- `confirmed`
- `probable`
- `indeterminate`

La réponse expose également, quand Home Assistant le prouve, le type de source (`automation`, `script`, `user`, `integration`), l'entité source et le déclencheur issu du contexte Logbook.

## Sécurité

Élise Why :
- ne commande aucun équipement ;
- ne modifie aucun état Home Assistant ;
- n'écrit aucun YAML ;
- n'accède à aucun secret ;
- n'appelle aucun service mutateur ;
- n'altère pas HA-MCP ;
- ne recherche jamais une automatisation seulement « plausible ».

L'action `elise_why.explain` est enregistrée avec `SupportsResponse.ONLY` :
elle retourne des données et ne réalise aucune action.

## Installation

Le dépôt doit être ajouté à HACS comme **Custom repository / Integration**.

Après installation et redémarrage :
1. Paramètres → Appareils et services → Ajouter une intégration.
2. Rechercher **Élise Why**.
3. Ajouter l'intégration.
4. Outils de développement → Actions → `elise_why.explain`.
5. Fournir `entity_id`, par exemple `cover.volet_salon_2`.

> Ne pas installer en production sans validation explicite dans une séance Maison Cognitive.

## Limites V0.1

- Le moteur s'appuie sur le Logbook Home Assistant.
- Il utilise une petite surface interne de l'implémentation Logbook/Recorder ; la compatibilité est ciblée sur Home Assistant 2026.8.2.
- Les déclencheurs inconnus restent `probable` ou `indeterminate` plutôt que d'être inventés.
- Le raccordement à ChatGPT/MCP n'est **pas** inclus dans V0.1 : ce dépôt est indépendant de HA-MCP.
