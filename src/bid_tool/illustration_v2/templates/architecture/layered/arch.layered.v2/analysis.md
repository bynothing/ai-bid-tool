# Template Analysis: arch.layered.v2

## Goal

Convert common bid-proposal architecture descriptions into a stable, polished
three-layer diagram without allowing the model to invent coordinates.

## Visual Pattern

- A full-width dark title band establishes document identity.
- Three stacked layer panels express top-to-bottom architecture dependency.
- Each layer has a frozen header and up to four fixed card slots.
- Each card contains an icon badge, short title, and one-line description.
- A bottom note band records assumptions, constraints, or evidence notes.

## Template Selection Cues

Select this template when the content describes:

- system architecture;
- platform/service/data layering;
- capability groups arranged by layer;
- bid-document overview figures where stable formal layout matters.

Do not select this template when:

- the primary content is numeric chart data;
- the relationship graph has more than three layers or dense cross-links;
- the main value is a network topology with device-level links.

## Contract Summary

- Layers: 2 to 3.
- Items per layer: 1 to 4.
- Title: max 16 characters per item.
- Description: max 42 characters per item.
- Layer label: max 18 characters.
- Icons must come from the whitelist in `contract.json`.

