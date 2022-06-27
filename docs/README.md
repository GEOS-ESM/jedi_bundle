# Introduction

Welcome to the "jedi_bundle" system for installing JEDI source code. The JEDI source code utilizes bundles, which are a make system based on ECMWF's ecbuild software. It is convenient in that multiple CMake-based software packages can be concurrently built with seamless handling of dependencies between them. This software provides highly flexible configuration of the bundles for different applications of the JEDI source code as well as an end-to-end build process.

In particular this software is designed to be useful for:

- Building several JEDI bundles in one go. Without having to clone and maintain several bundle repositories, each with single use.
- Application-focused building of multiple bundles by using select make steps, rather than building the entire bundle
- Providing a single build system for teams working with public, private and forked versions of repositories.
- Coordinating development across multiple repos by searching for a particular branch name across all included repos and across multiple organisations.
- Having YAML configuration to control the build system.
- Embedding the building of the source code within a workflow system, where it is likely necessary to clone code in one workflow task and build within another task that uses a scheduler.
- Unification of the build system across multiple repos that have CI build systems.

