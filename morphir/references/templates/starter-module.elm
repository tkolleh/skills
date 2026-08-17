-- Minimal starter Elm module for a new Morphir model.
-- Copy into src/<ProjectName-as-path>/<Domain>/<Name>.elm and adapt.
--
-- Verified project shape (see ../morphir-elm-cli.md):
--   morphir.json: {"name": "<ProjectName>", "sourceDirectory": "src", "exposedModules": ["<Domain>.<Name>"]}
--   File path:    src/<ProjectName>/<Domain>/<Name>.elm
--   exposedModules entries are relative to `name` — leaf module path only.
--
-- Translate the source function 1:1: same branches, same short-circuit
-- order. Do not "clean up" or restructure the logic during translation —
-- a decision table (see ../decision-table-methodology.md) verifies this
-- module against the source afterward, and a restructured model makes
-- that comparison harder to trust, not easier.

module <ProjectName>.<Domain>.<Name> exposing (..)


-- Replace with the actual input/output types from the source function.
-- Keep field names close to the source's own vocabulary so a reviewer
-- can map Elm fields to source fields without a lookup table.
type alias Input =
    { flag : Bool
    , value : Int
    }


-- Type variables must be lowercase in Elm (`a`, `i o`) — an uppercase
-- identifier in a type-variable position parses as a type-constructor
-- reference, not a variable binding, and will not compile as intended.


evaluate : Input -> Int -> Bool
evaluate input threshold =
    if input.flag then
        False

    else
        input.value >= threshold
