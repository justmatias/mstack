# CHANGELOG

<!-- version list -->

## v3.1.0 (2026-11-20)

### Continuous Integration

- Audit the locked dependencies, least-privilege permissions and drop redundant steps
  ([#18](https://github.com/justmatias/mstack/pull/18),
  [`e42e9d5`](https://github.com/justmatias/mstack/commit/e42e9d50c889bbb3ee44f0a27088f09d59754d03))

### Documentation

- Simplify the README and add a getting started section
  ([#19](https://github.com/justmatias/mstack/pull/19),
  [`dd55a73`](https://github.com/justmatias/mstack/commit/dd55a73d138f2d0355ebfeaf9e9a8a751398cdc2))

- **setup-mstack**: Reword which items step 5 asks about
  ([#22](https://github.com/justmatias/mstack/pull/22),
  [`3c28eed`](https://github.com/justmatias/mstack/commit/3c28eed8d0423930fbcc7265b57050dfff343618))

- **specs**: Add implementation plans for the cross-machine stack
  ([#20](https://github.com/justmatias/mstack/pull/20),
  [`05230f5`](https://github.com/justmatias/mstack/commit/05230f5f4c966d1493c890c020960409389febf3))

### Features

- **config**: Read repo paths from .mstack.toml
  ([#21](https://github.com/justmatias/mstack/pull/21),
  [`09dde71`](https://github.com/justmatias/mstack/commit/09dde7109a46dd761636d455e2c7d5a5915e7bc6))

- **install**: Record installed items in a manifest
  ([#22](https://github.com/justmatias/mstack/pull/22),
  [`3c28eed`](https://github.com/justmatias/mstack/commit/3c28eed8d0423930fbcc7265b57050dfff343618))


## v3.0.0 (2026-11-20)

### Features

- **integrate-skills**: Add skill to integrate skills from a GitHub URL
  ([#17](https://github.com/justmatias/mstack/pull/17),
  [`6260b0d`](https://github.com/justmatias/mstack/commit/6260b0d849d559a262710cdef27945187d0f5708))

- **integrate-skills**: Compare with every existing skill before adding a new one
  ([#17](https://github.com/justmatias/mstack/pull/17),
  [`6260b0d`](https://github.com/justmatias/mstack/commit/6260b0d849d559a262710cdef27945187d0f5708))

### Testing

- Remove the skill tests ([#17](https://github.com/justmatias/mstack/pull/17),
  [`6260b0d`](https://github.com/justmatias/mstack/commit/6260b0d849d559a262710cdef27945187d0f5708))


## v2.0.0 (2026-11-20)

### Documentation

- Record the setup-mstack end-to-end run ([#15](https://github.com/justmatias/mstack/pull/15),
  [`a3fcde1`](https://github.com/justmatias/mstack/commit/a3fcde14241329b2292222c5a0e83ccf07838497))

- **setup-mstack**: Summarize each item's purpose before asking
  ([#15](https://github.com/justmatias/mstack/pull/15),
  [`a3fcde1`](https://github.com/justmatias/mstack/commit/a3fcde14241329b2292222c5a0e83ccf07838497))

### Features

- Add setup-mstack skill that installs the skills by copy
  ([#15](https://github.com/justmatias/mstack/pull/15),
  [`a3fcde1`](https://github.com/justmatias/mstack/commit/a3fcde14241329b2292222c5a0e83ccf07838497))

### Refactoring

- Make setup a skill-only workflow and drop hooks and user-level rules
  ([#15](https://github.com/justmatias/mstack/pull/15),
  [`a3fcde1`](https://github.com/justmatias/mstack/commit/a3fcde14241329b2292222c5a0e83ccf07838497))

- Move setup-mstack into skills/ ([#15](https://github.com/justmatias/mstack/pull/15),
  [`a3fcde1`](https://github.com/justmatias/mstack/commit/a3fcde14241329b2292222c5a0e83ccf07838497))

### Testing

- Drop third-party notices file and its tests ([#15](https://github.com/justmatias/mstack/pull/15),
  [`a3fcde1`](https://github.com/justmatias/mstack/commit/a3fcde14241329b2292222c5a0e83ccf07838497))


## v1.9.0 (2026-11-19)

### Documentation

- **skills**: Credit pstack in skill frontmatter instead of a notices file
  ([#13](https://github.com/justmatias/mstack/pull/13),
  [`550bd2a`](https://github.com/justmatias/mstack/commit/550bd2ab64f0c1661ea3b6615b51f01f1cf4667c))

### Features

- **reflect-rules**: Rebase on current upstream reflect, add --deep mode
  ([#13](https://github.com/justmatias/mstack/pull/13),
  [`550bd2a`](https://github.com/justmatias/mstack/commit/550bd2ab64f0c1661ea3b6615b51f01f1cf4667c))


## v1.8.0 (2026-11-19)

### Features

- Ship the guards as an mstack CLI and fix design review findings
  ([#12](https://github.com/justmatias/mstack/pull/12),
  [`8f724ca`](https://github.com/justmatias/mstack/commit/8f724ca765db4ea1b1c9291ba867ca883b99a021))

### Refactoring

- Remove the conventions store integration ([#14](https://github.com/justmatias/mstack/pull/14),
  [`79b5ec8`](https://github.com/justmatias/mstack/commit/79b5ec8ad936c0837da759f5a4711f10cff50d36))


## v1.7.0 (2026-11-19)

### Continuous Integration

- Add pre-commit hook and GitHub Actions workflow running the single command
  ([#11](https://github.com/justmatias/mstack/pull/11),
  [`09185c1`](https://github.com/justmatias/mstack/commit/09185c1aee2ea824aeefa47a8fa36780ef3bc2c1))

### Documentation

- Record end-to-end scenario results ([#11](https://github.com/justmatias/mstack/pull/11),
  [`09185c1`](https://github.com/justmatias/mstack/commit/09185c1aee2ea824aeefa47a8fa36780ef3bc2c1))

### Features

- Add agent hooks and a configurable setup CLI ([#11](https://github.com/justmatias/mstack/pull/11),
  [`09185c1`](https://github.com/justmatias/mstack/commit/09185c1aee2ea824aeefa47a8fa36780ef3bc2c1))

- Add ast-grep checks, rule tests and import-linter contract
  ([#11](https://github.com/justmatias/mstack/pull/11),
  [`09185c1`](https://github.com/justmatias/mstack/commit/09185c1aee2ea824aeefa47a8fa36780ef3bc2c1))

- Add coverage, exception and domain-leak guards and the single command
  ([#11](https://github.com/justmatias/mstack/pull/11),
  [`09185c1`](https://github.com/justmatias/mstack/commit/09185c1aee2ea824aeefa47a8fa36780ef3bc2c1))

- Add example app, demo violations and prose rules
  ([#11](https://github.com/justmatias/mstack/pull/11),
  [`09185c1`](https://github.com/justmatias/mstack/commit/09185c1aee2ea824aeefa47a8fa36780ef3bc2c1))

- Add personal user-level rules, global hooks and conventions inventory
  ([#11](https://github.com/justmatias/mstack/pull/11),
  [`09185c1`](https://github.com/justmatias/mstack/commit/09185c1aee2ea824aeefa47a8fa36780ef3bc2c1))

- Add sync-rules, reflect-rules and correct-rules skills
  ([#11](https://github.com/justmatias/mstack/pull/11),
  [`09185c1`](https://github.com/justmatias/mstack/commit/09185c1aee2ea824aeefa47a8fa36780ef3bc2c1))


## v1.6.0 (2026-11-19)

### Bug Fixes

- Drop shebang from conventions_inventory, which runs as a module
  ([#10](https://github.com/justmatias/mstack/pull/10),
  [`a415fd8`](https://github.com/justmatias/mstack/commit/a415fd89fc44bf8f3c919ccb3a24fece846a4dcf))

### Continuous Integration

- Add pre-commit hook and GitHub Actions workflow running the single command
  ([#10](https://github.com/justmatias/mstack/pull/10),
  [`a415fd8`](https://github.com/justmatias/mstack/commit/a415fd89fc44bf8f3c919ccb3a24fece846a4dcf))

### Features

- Add agent hooks and a configurable setup CLI ([#10](https://github.com/justmatias/mstack/pull/10),
  [`a415fd8`](https://github.com/justmatias/mstack/commit/a415fd89fc44bf8f3c919ccb3a24fece846a4dcf))

- Add ast-grep checks, rule tests and import-linter contract
  ([#10](https://github.com/justmatias/mstack/pull/10),
  [`a415fd8`](https://github.com/justmatias/mstack/commit/a415fd89fc44bf8f3c919ccb3a24fece846a4dcf))

- Add coverage, exception and domain-leak guards and the single command
  ([#10](https://github.com/justmatias/mstack/pull/10),
  [`a415fd8`](https://github.com/justmatias/mstack/commit/a415fd89fc44bf8f3c919ccb3a24fece846a4dcf))

- Add example app, demo violations and prose rules
  ([#10](https://github.com/justmatias/mstack/pull/10),
  [`a415fd8`](https://github.com/justmatias/mstack/commit/a415fd89fc44bf8f3c919ccb3a24fece846a4dcf))

- Add personal user-level rules, global hooks and conventions inventory
  ([#10](https://github.com/justmatias/mstack/pull/10),
  [`a415fd8`](https://github.com/justmatias/mstack/commit/a415fd89fc44bf8f3c919ccb3a24fece846a4dcf))

- Add sync-rules, reflect-rules and correct-rules skills
  ([#10](https://github.com/justmatias/mstack/pull/10),
  [`a415fd8`](https://github.com/justmatias/mstack/commit/a415fd89fc44bf8f3c919ccb3a24fece846a4dcf))


## v1.5.0 (2026-11-19)

### Continuous Integration

- Add pre-commit hook and GitHub Actions workflow running the single command
  ([#8](https://github.com/justmatias/mstack/pull/8),
  [`7ee0679`](https://github.com/justmatias/mstack/commit/7ee067982351b83142cac2084891c44c5b7a819a))

### Features

- Add agent hooks and a configurable setup CLI ([#8](https://github.com/justmatias/mstack/pull/8),
  [`7ee0679`](https://github.com/justmatias/mstack/commit/7ee067982351b83142cac2084891c44c5b7a819a))

- Add ast-grep checks, rule tests and import-linter contract
  ([#8](https://github.com/justmatias/mstack/pull/8),
  [`7ee0679`](https://github.com/justmatias/mstack/commit/7ee067982351b83142cac2084891c44c5b7a819a))

- Add coverage, exception and domain-leak guards and the single command
  ([#8](https://github.com/justmatias/mstack/pull/8),
  [`7ee0679`](https://github.com/justmatias/mstack/commit/7ee067982351b83142cac2084891c44c5b7a819a))

- Add example app, demo violations and prose rules
  ([#8](https://github.com/justmatias/mstack/pull/8),
  [`7ee0679`](https://github.com/justmatias/mstack/commit/7ee067982351b83142cac2084891c44c5b7a819a))


## v1.4.0 (2026-11-19)

### Continuous Integration

- Add pre-commit hook and GitHub Actions workflow running the single command
  ([#7](https://github.com/justmatias/mstack/pull/7),
  [`ac66a51`](https://github.com/justmatias/mstack/commit/ac66a51573555efbf09a3255314316edc8d0c10a))

- Run the coverage guard as a module after the scripts regrouping
  ([#7](https://github.com/justmatias/mstack/pull/7),
  [`ac66a51`](https://github.com/justmatias/mstack/commit/ac66a51573555efbf09a3255314316edc8d0c10a))

- Run the rule scan, demo and tests in ci.yml instead of a separate workflow
  ([#7](https://github.com/justmatias/mstack/pull/7),
  [`ac66a51`](https://github.com/justmatias/mstack/commit/ac66a51573555efbf09a3255314316edc8d0c10a))

### Features

- Add ast-grep checks, rule tests and import-linter contract
  ([#7](https://github.com/justmatias/mstack/pull/7),
  [`ac66a51`](https://github.com/justmatias/mstack/commit/ac66a51573555efbf09a3255314316edc8d0c10a))

- Add coverage, exception and domain-leak guards and the single command
  ([#7](https://github.com/justmatias/mstack/pull/7),
  [`ac66a51`](https://github.com/justmatias/mstack/commit/ac66a51573555efbf09a3255314316edc8d0c10a))

- Add example app, demo violations and prose rules
  ([#7](https://github.com/justmatias/mstack/pull/7),
  [`ac66a51`](https://github.com/justmatias/mstack/commit/ac66a51573555efbf09a3255314316edc8d0c10a))


## v1.3.0 (2026-11-19)

### Bug Fixes

- Drop shebangs from the Python tools now run as modules
  ([#5](https://github.com/justmatias/mstack/pull/5),
  [`509e3f5`](https://github.com/justmatias/mstack/commit/509e3f5b899be0c7b353fd7e5d665e597a060dd5))

### Features

- Add coverage, exception and domain-leak guards and the single command
  ([#5](https://github.com/justmatias/mstack/pull/5),
  [`509e3f5`](https://github.com/justmatias/mstack/commit/509e3f5b899be0c7b353fd7e5d665e597a060dd5))

### Refactoring

- Group scripts by purpose and document each one ([#5](https://github.com/justmatias/mstack/pull/5),
  [`509e3f5`](https://github.com/justmatias/mstack/commit/509e3f5b899be0c7b353fd7e5d665e597a060dd5))


## v1.2.0 (2026-11-19)

### Features

- Add ast-grep checks, rule tests and import-linter contract
  ([#4](https://github.com/justmatias/mstack/pull/4),
  [`c0dc23e`](https://github.com/justmatias/mstack/commit/c0dc23ef601d193a178a58a698757b21f3b3ef8d))


## v1.1.0 (2026-11-19)

### Bug Fixes

- Allow dataclasses when required in python-models rule
  ([#3](https://github.com/justmatias/mstack/pull/3),
  [`a3db40a`](https://github.com/justmatias/mstack/commit/a3db40aee80864abc3b9f69c9ff117e25e4d72da))

### Features

- Add example app, demo violations and prose rules
  ([#3](https://github.com/justmatias/mstack/pull/3),
  [`a3db40a`](https://github.com/justmatias/mstack/commit/a3db40aee80864abc3b9f69c9ff117e25e4d72da))

- Add valid/invalid fixtures and prose rules ([#3](https://github.com/justmatias/mstack/pull/3),
  [`a3db40a`](https://github.com/justmatias/mstack/commit/a3db40aee80864abc3b9f69c9ff117e25e4d72da))

### Refactoring

- Move fixtures under fixtures/valid and fixtures/invalid
  ([#3](https://github.com/justmatias/mstack/pull/3),
  [`a3db40a`](https://github.com/justmatias/mstack/commit/a3db40aee80864abc3b9f69c9ff117e25e4d72da))


## v1.0.0 (2026-11-19)

- Initial Release
