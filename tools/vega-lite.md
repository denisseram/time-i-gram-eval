---
name: Vega-Lite
deliverable: spec.vl.json
deliverable_kind: the Vega-Lite specification
---
## Tool: Vega-Lite

- **Tool and version:** Vega-Lite 6.5.0; the specification must declare
  `"$schema": "https://vega.github.io/schema/vega-lite/v6.json"`.
- **Documentation:** you may use the web. The official documentation is https://vega.github.io/vega-lite/docs/
  and the example gallery is https://vega.github.io/vega-lite/examples/.
- **Deliverable:** one file, `spec.vl.json`, a single Vega-Lite specification (JSON).
- **How it will be run:** rendered with vega-embed 7.3.0 (Vega 6.4.0) in Chromium (latest stable), window
  1400 × 900 px, with default embed options. It must render without errors or warnings that change the figure.
- **Allowed:** everything in the Vega-Lite specification language, including transforms, parameters and
  expressions.
- **Not allowed:** a compiled or hand-written Vega (non-Lite) specification, custom JavaScript, or changes to
  the embed options.
