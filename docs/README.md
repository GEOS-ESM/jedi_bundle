# Introduction

Welcome to the system for installing JEDI source code bundles. Bundles are a make system that uses ECMWF's ecbuild software. It allows various CMake-based software packages to be concurrently built  with seamless handling of dependencies between them.

This software is useful for:

- Coordinating branch names across multiple repositories.
- Searching across repos with the same name across different GitHub organisations. This can be used, for example, to search forks for branches.
- Embedding the building of the source code within a workflow system.

