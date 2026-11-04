# Run environment of the time-i-gram evaluation: one image, identical for all four tools.
#
#   docker build -t tig-eval:1 env/
#
# Contains: R with ggtime and the allowed packages, Node 22, Chromium (Playwright), the `render` command,
# Claude Code, and a non-root user `agent` whose home is the empty working folder /work.
# It contains NO evaluation materials (prompts, rubrics, datasets list): never copy this repo into it.

ARG R_VERSION=4.5.2
FROM rocker/r-ver:${R_VERSION}

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=UTC \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# System tools agents may reasonably use, and the libraries R graphics and data packages need.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl wget git less procps unzip python3 python3-pip \
        libcurl4-openssl-dev libssl-dev libxml2-dev \
        libfontconfig1-dev libfreetype6-dev libpng-dev libjpeg-dev libtiff-dev \
        libharfbuzz-dev libfribidi-dev libcairo2-dev fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Node.js 22 (needed by Claude Code and the render command).
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# R packages allowed for the ggtime agent, from one dated CRAN snapshot (Posit Package Manager), so the
# versions are fixed. The same snapshot is the default repository inside the container.
ARG CRAN_SNAPSHOT=https://p3m.dev/cran/__linux__/noble/2026-11-01
RUN echo "options(repos = c(CRAN = '${CRAN_SNAPSHOT}'))" >> /usr/local/lib/R/etc/Rprofile.site \
    && Rscript -e 'install.packages(c("ggtime", "ggplot2", "tsibble", "readr", "dplyr", "tidyr", "lubridate", "scales", "patchwork", "svglite"), Ncpus = 4)' \
    && Rscript -e 'pk <- c("ggtime", "ggplot2", "tsibble", "mixtime", "readr", "dplyr", "tidyr", "lubridate", "scales", "patchwork", "svglite"); \
                   missing <- pk[!vapply(pk, requireNamespace, logical(1), quietly = TRUE)]; \
                   if (length(missing)) stop("not installed: ", paste(missing, collapse = ", ")); \
                   if (packageVersion("ggtime") < "1.1.0") stop("ggtime >= 1.1.0 required, got ", packageVersion("ggtime")); \
                   v <- vapply(pk, function(p) as.character(packageVersion(p)), ""); \
                   writeLines(c(R.version.string, paste(pk, v)), "/opt/versions-r.txt")'

# The render command: Playwright + Chromium and the pinned Vega and time-i-gram builds, all local.
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/ms-playwright
COPY render/package.json render/package-lock.json /opt/render/
RUN cd /opt/render && npm ci --no-audit --no-fund \
    && npx playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/*
COPY render/render.mjs /opt/render/render.mjs
COPY render/render /usr/local/bin/render
RUN chmod 755 /usr/local/bin/render

# Claude Code, pinned; no automatic updates during the evaluation.
ARG CLAUDE_CODE_VERSION=2.1.318
RUN npm install -g --no-audit --no-fund @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}
ENV DISABLE_AUTOUPDATER=1 \
    CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1

# Record every version in the image (the runner copies this into each run).
RUN { echo "claude-code $(claude --version 2>/dev/null)"; echo "node $(node --version)"; \
      cat /opt/versions-r.txt; \
      cd /opt/render && node -e 'const l=require("./package-lock.json").packages; for (const p of ["playwright","time-i-gram","vega","vega-embed","vega-lite"]) console.log(p, l["node_modules/"+p].version)'; \
    } > /opt/versions.txt && cat /opt/versions.txt

# Non-root user: Claude Code refuses to skip permission prompts as root, and the agent cannot install
# packages into the system libraries.
RUN useradd --create-home --shell /bin/bash agent && mkdir -p /work && chown agent:agent /work
USER agent
WORKDIR /work
