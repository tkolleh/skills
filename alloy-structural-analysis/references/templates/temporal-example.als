-- Minimal working Alloy 6 temporal spec, verified against a real
-- electrod.nuxmv invocation. Use as a starting skeleton for a new
-- temporal (var-field) model, not as a real property to check as-is.
--
-- Verified invocation:
--   alloy exec -s electrod.nuxmv -t json -f -o <output-dir> temporal-example.als
-- Expected verdict: UNSAT (the property holds for the declared scope).
-- If you get anything else, debug-verify per references/alloy-harness.md
-- Trap 4 before trusting the result.

one sig Counter {
  var count: one Int
}

fact Init {
  Counter.count = 0
}

pred inc {
  Counter.count' = plus[Counter.count, 1]
}

fact Trace {
  always inc
}

check AlwaysNonNegative {
  always Counter.count >= 0
} for 3 Int, 5 steps
