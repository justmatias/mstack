# CHANGELOG

<!-- version list -->

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
