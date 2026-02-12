---
title: qBraid
emoji: 🏃‍♂️⏱️
project_url: https://github.com/qBraid/qBraid
metaDescription: A platform-agnostic quantum runtime framework
date: 2025-04-17
summary: A platform-agnostic quantum runtime framework
tags:
  - python
  - openqasm
  - compiler
  - semantic analysis
bounties:
  # - issue_num: 53
  #   value: 150
---

The [qBraid-SDK](https://docs.qbraid.com/v2/sdk/user-guide/overview) is a platform-agnostic quantum runtime framework designed for both quantum software and hardware providers. This Python-based tool streamlines the full lifecycle management of quantum jobs—from defining program specifications to job submission and through to the post-processing and visualization of results.

Unlike existing runtime frameworks that focus their automation and abstractions on quantum components, qBraid adds an extra layer of abstractions that considers the ultimate IR needed to encode the quantum program and securely submit it to a remote API. Notably, the qBraid-SDK *does not adhere to a fixed circuit-building library*, or quantum program representation. Instead, it empowers providers to dynamically [register](https://docs.qbraid.com/v2/sdk/user-guide/programs#quantum-program-registry) any desired input program type as the target based on their specific needs. By doing so, the qBraid-SDK vastly reduces the overhead and redundancy typically associated with the development of [runtime pipelines](https://docs.qbraid.com/v2/sdk/user-guide/runtime/components) and cross-platform integrations in quantum computing.

[PyQASM](https://docs.qbraid.com/v2/pyqasm/user-guide/overview) is a Python toolkit providing an [OpenQASM 3](https://openqasm.com/) semantic analyzer and utilities for program analysis and compilation. It serves as a core dependency of the qBraid-SDK, ensuring consistent runtime behavior across heterogeneous quantum backends.

*Resources*:
- [Documentation](https://docs.qbraid.com)
- [API Reference](https://sdk.qbraid.com)
- [Example Notebooks](https://github.com/qBraid/qbraid-lab-demo/)
