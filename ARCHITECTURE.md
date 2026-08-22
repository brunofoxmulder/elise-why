# Architecture — Élise Why V0.1

## Décision

Élise Why est **indépendante de HA-MCP**.

Aucun fichier n'est placé dans le paquet HA-MCP et aucun patch HA-MCP n'est appliqué.
Le patch historique `ha_mcp_why_v0_1.patch` reste uniquement une archive de conception.

## Chaîne V0.1

Home Assistant
→ Logbook / Recorder (lecture)
→ `HomeAssistantLogbookProvider`
→ `WhyEngine`
→ action `elise_why.explain` (`SupportsResponse.ONLY`)
→ résultat JSON

## Invariants

1. Aucun service de commande n'est appelé.
2. Aucun état HA n'est modifié.
3. Aucun fichier YAML n'est lu/écrit.
4. Aucun secret n'est requis.
5. Une cause est `confirmed` uniquement lorsque la trace l'établit.
6. Une trace incomplète donne `probable` ou `indeterminate`.
7. Une mise à jour HA-MCP ne touche pas cette intégration.

## Étape ultérieure — hors V0.1

Un accès ChatGPT direct demandera une interface/bridge séparée.
Elle devra appeler Élise Why sans donner de droits de commande sur Home Assistant.
