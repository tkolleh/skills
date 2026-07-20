---
name: diagram
description: Generates technical diagrams using the D2 language, with automatic color-contrast verification and diagram-type detection.
license: MIT
compatibility: opencode
metadata:
  purpose: visualization
  engine: d2
  audience: developers
  tools: [d2, pastel, bash]
---

## Diagram Creator

Generate professional architecture and sequence diagrams using the D2 declarative language. Output is a rigorous engineering artifact modeling complex distributed systems with precision, enforcing strict separation between *inventory* (what exists) and *topology* (how it connects) - with automatic color-contrast verification and diagram-type detection


## When to use me
Use this skill whenever a system architecture, data flow, sequence diagram, or service interaction needs to be visualized. This skill should be triggered after a planning phase to present a visual map to the user.

## Core Instructions

### Core Philosophy: "Measure Once, Cut Twice"
1.  **Inventory First:** You must define every entity fully (metadata, technology, owner) before drawing a single line.
2.  **Strict Typing:** Every entity is a simple shape with a class and structured metadata.
3.  **Compiler Safety:** You always generate D2 code that compiles, avoiding known D2 antipatterns.

### Instructions

#### 1. Visualization Standard

You define the model and view in separate files. The model file (`models.d2`) contains the inventory of entities and their metadata, while the view file (`backend-view.d2`) contains the topology (connections) and styling. This separation ensures clarity and maintainability.

* You **Always** reference the files `models.d2` and `backend-view.d2` for examples of how to structure your code.
* You view files **must** import model files to reference entities.
* You **Always** validate your D2 files using the d2 CLI tool against the view files

#### 2. C4 Model Integration
* **Context:** Use D2 "Groups" (empty containers) for Domains (e.g., `Analytics_Domain`).
* **Container:** Runtime units (Services, DBs).
* **Component:** Code units (Libraries, DAGs).
* **Actors:** Use `shape: person` for human users or external systems.

#### 3. D2 Code Structure (Strict Hierarchy)
You must generate code in this exact order to ensure compilation:

1.  **Metamodel (Classes):**
    * *Critical Constraint:* Classes must be defined at the root.
    * *Critical Constraint:* **No nesting.** You cannot define a class inside `classes`.
    * *Critical Constraint:* **No inheritance.** One class cannot reference another via `class:`.
2.  **Domain Contexts:** Empty groups with `fill: transparent`.
3.  **Entity Inventory:** Define objects using dot notation (`Domain.Entity`). **No connections here.**
4.  **Topology:** Define connections (`->`) in separate files after suspending unwanted classes.

#### Negative Constraints (Guardrails)
* **DO NOT** mix entity definitions with relationships.
* **DO NOT** use semicolons in style blocks.
* **DO NOT** use local file paths for icons.
* **DO NOT** nest classes inside the `classes` block.

#### Canonical Example

* Reference the `models.d2` and `backend-view.d2` files as examples
* Use undefined classes (tags) such as `systembe` for grouping components. The `domain_actor` class is defined with specific styles, and then both `systembe` and `domain_actor` are applied to the `api_service` component.

#### Execution Steps
1.  **Analyze** the user's request to identify Domains, Containers, and Components.
2.  **Draft** the Inventory list mentally, and assigning tech stacks.
3.  **Generate** the D2 code following the instructions strictly.
4.  **Recommend diagram type** — once the model/view files exist, run `python main.py recommend-diagram-type --model_path <view-file>.d2`. This parses actual entity/relationship counts, cycles, actor shapes, and edge ordering from the file and returns `sequence`, `state`, or `c4` — a deterministic decision, not a free-form read of the user's request. If the recommendation doesn't match what was drafted in step 1, prefer the tool's output and adjust the structure.
5.  **Check contrast** — run `python main.py check-contrast --model_path models.d2`. This validates every class's `fill`/`font-color` pair against `pastel textcolor` and reports mismatches. Fix any `"ok": false` result before rendering.
    - Known limitation: this check assumes plain black/white text and will report `_md`/`_grp` markdown classes as failing even when they intentionally use a tinted `font-color` (see the styling comment at the top of `models.d2`). Treat `_md`/`_grp` class failures as informational, not blocking — the `stroke` vs `fill` distinction on those classes is the real readability signal, not `font-color`.
6.  **Preview** — render just the class/legend definitions from `models.d2` to a small SVG first (`d2 models.d2 preview.svg`) and confirm it compiles cleanly before rendering the full diagram.
7.  **Render** the full view file to SVG (`d2 backend-view.d2 output.svg`) and present the result.
