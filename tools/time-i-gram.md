---
name: time-i-gram
deliverable: spec.json
deliverable_kind: the time-i-gram specification
---
## Tool: time-i-gram

- **Tool and version:** time-i-gram 0.1.0, a grammar for time-based data that extends Gosling.js (npm package
  `time-i-gram`). Source: https://github.com/vanessastoiber/time-i-gram at tag `v0.1.0`
  (commit `fa8a247161eafbb67c97bfb4e6af18ac034b0dab`).
- **Documentation:** you may use the web. The official documentation is, at that tag, the repository's
  `README.md`, the JSON schema `src/gosling-schema/gosling.schema.json` and the example specifications under
  `editor/example/`; and the package page https://www.npmjs.com/package/time-i-gram.
- **Deliverable:** one file, `spec.json`, a single time-i-gram specification (JSON).
- **How it will be run:** passed to `embed(element, spec)` from time-i-gram 0.1.0
  (`https://cdn.jsdelivr.net/npm/time-i-gram@0.1.0/dist/index.js`) in Chromium (latest stable), window
  1400 × 900 px. It must render without errors.
- **Allowed:** everything in the time-i-gram specification language, including the time-aware data sources,
  time coordinate systems and linking.
- **Not allowed:** custom JavaScript, editing time-i-gram's source code, or data fetchers other than those
  built in.
