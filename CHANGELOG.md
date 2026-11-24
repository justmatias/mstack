# CHANGELOG

<!-- version list -->

## v6.6.0 (2026-11-24)

### Features

- **rules**: Name compound keyword conditions
  ([`a2f86fa`](https://github.com/justmatias/mstack/commit/a2f86fa38a6e589c47ebb0094a535ec1358ba04c))

- **rules**: Prefer named fields for structured returns
  ([`89fbc69`](https://github.com/justmatias/mstack/commit/89fbc69de0bda79083f3bee024da4ab5a13474ff))


## v6.5.0 (2026-11-24)

### Bug Fixes

- **skills**: Close stdin when running a reviewer CLI
  ([#70](https://github.com/justmatias/mstack/pull/70),
  [`7f701b1`](https://github.com/justmatias/mstack/commit/7f701b1b93b12571ea0960993c2ba524a281ec59))

- **skills**: Close stdin when running a reviewer CLI
  ([#68](https://github.com/justmatias/mstack/pull/68),
  [`362ed27`](https://github.com/justmatias/mstack/commit/362ed274159fc08d063cb6efd219963e065ac0ec))

### Features

- **rules**: Add conftest-has-only-fixtures check
  ([#70](https://github.com/justmatias/mstack/pull/70),
  [`7f701b1`](https://github.com/justmatias/mstack/commit/7f701b1b93b12571ea0960993c2ba524a281ec59))

- **rules**: Add conftest-has-only-fixtures check
  ([#68](https://github.com/justmatias/mstack/pull/68),
  [`362ed27`](https://github.com/justmatias/mstack/commit/362ed274159fc08d063cb6efd219963e065ac0ec))

- **rules**: Clarify naming for result models ([#70](https://github.com/justmatias/mstack/pull/70),
  [`7f701b1`](https://github.com/justmatias/mstack/commit/7f701b1b93b12571ea0960993c2ba524a281ec59))

- **rules**: Name functions with a verb phrase
  ([`4135aa5`](https://github.com/justmatias/mstack/commit/4135aa5e47f91f912392af38b61083dcddb3395c))


## v6.4.0 (2026-11-23)

### Bug Fixes

- **skills**: Close stdin when running a reviewer CLI
  ([`7dd0027`](https://github.com/justmatias/mstack/commit/7dd002720dc12741add7e0bbddb0123a61c87c13))

### Features

- **rules**: Add conftest-has-only-fixtures check
  ([`7d94462`](https://github.com/justmatias/mstack/commit/7d944622e3424621e218c8f540d1373fffb9f336))


## v6.3.0 (2026-11-23)

### Bug Fixes

- **testing**: Align the valid fixture with the test-name rule
  ([`ceadc39`](https://github.com/justmatias/mstack/commit/ceadc3986088f1984f3e83850aec160e906d529e))

### Features

- **testing**: Check descriptive test names
  ([`d020c74`](https://github.com/justmatias/mstack/commit/d020c7427f9503cb8fa0f7dbdc584f5345f1fcea))


## v6.2.0 (2026-11-23)

### Features

- **reflect**: Open PRs for approved mstack contributions
  ([`412c3ae`](https://github.com/justmatias/mstack/commit/412c3aee710387963c980b71bae72522de9a359b))

- **rules**: Clarify which pytest setup belongs in fixtures
  ([`88bc095`](https://github.com/justmatias/mstack/commit/88bc0956fa8be838970bdf1d43287f240daaaf2f))

- **rules**: Keep class-specific Python helpers on the class
  ([`5d17060`](https://github.com/justmatias/mstack/commit/5d170603f4ec6322067e25441fd5d677aa0f8c4d))


## v6.1.0 (2026-11-23)

### Features

- **hooks**: Run checks while agents edit
  ([`8598e74`](https://github.com/justmatias/mstack/commit/8598e743e1655343876fd42f466ed6c55b5b208a))

- **hooks**: Support Codex edit and stop hooks
  ([`052fc9a`](https://github.com/justmatias/mstack/commit/052fc9aed984f851590215cc9e2952524a2b7e68))


## v6.0.0 (2026-11-23)

### Features

- **skills**: Namespace the two-axis review command
  ([`ff95293`](https://github.com/justmatias/mstack/commit/ff952931953f5e3d2ca88855be70d0fdcc136e38))

- **skills**: Rename review command to diff-review
  ([`242e3ea`](https://github.com/justmatias/mstack/commit/242e3ea79964e3f72bba7f8c86e2ca267c23cffc))

- **skills**: Verify sources and challenge decisions earlier
  ([`e007505`](https://github.com/justmatias/mstack/commit/e007505be08f8bfb7c9479cb031c571ed5d4f0a4))


## v5.7.0 (2026-11-22)

### Features

- **rules**: Add sleep, raises and skip guidance to testing
  ([`3f26c1e`](https://github.com/justmatias/mstack/commit/3f26c1e3f75a23a31222c5d5a881b8b438927976))

- **rules**: Expand commit format and branch guidance
  ([`6e86513`](https://github.com/justmatias/mstack/commit/6e86513d2493c30aff6e6a03da42623dd1301ae3))


## v5.6.0 (2026-11-22)

### Documentation

- Consolidate optional agent asset guides ([#61](https://github.com/justmatias/mstack/pull/61),
  [`fafaf42`](https://github.com/justmatias/mstack/commit/fafaf42a5479b4bf79fe39bf7db1401e05eaa314))

### Features

- **reflect**: Offer shared rules and checks as mstack contributions
  ([`9f65363`](https://github.com/justmatias/mstack/commit/9f65363b685bdeec6f72b694d3f2804400b0eb58))

### Testing

- Allow absent optional asset folders ([#61](https://github.com/justmatias/mstack/pull/61),
  [`fafaf42`](https://github.com/justmatias/mstack/commit/fafaf42a5479b4bf79fe39bf7db1401e05eaa314))


## v5.5.0 (2026-11-22)

### Bug Fixes

- **lint**: Isolate shared pack scans and CI settings
  ([`690fb9d`](https://github.com/justmatias/mstack/commit/690fb9d068ff735a47099d016823cdbbf0fb611f))

### Continuous Integration

- Run checks on the automation update
  ([`4737c54`](https://github.com/justmatias/mstack/commit/4737c541e96d4967a7f4474fa320c5f57db6f12c))

### Features

- **lint**: Ship shared rule packs with mstack
  ([`eac2ec1`](https://github.com/justmatias/mstack/commit/eac2ec1f42ca96083e65e38a43323dd1c9b52698))


## v5.4.0 (2026-11-21)

### Bug Fixes

- **rules**: Match Python lint cases more precisely
  ([`aa649bb`](https://github.com/justmatias/mstack/commit/aa649bbb46b56028e03f59521cfe695e9c76bb16))

### Features

- **rules**: Add engineering principles adapted from pstack
  ([`a21daf0`](https://github.com/justmatias/mstack/commit/a21daf0da37d12ba92e35c7e9016a63676ac774a))

- **rules**: Add module, fixture, MCP, logging and pin rules with checks
  ([`cecc084`](https://github.com/justmatias/mstack/commit/cecc084a88286b10d5395d37695aa17b73492f2f))

- **rules**: Let shared checks stand without prose
  ([`b2a2dd7`](https://github.com/justmatias/mstack/commit/b2a2dd796a8b0b5eae8c9b9a4b0baf0300eba627))

### Refactoring

- **rules**: Drop the logging and MCP server rules
  ([`dbab6b8`](https://github.com/justmatias/mstack/commit/dbab6b86ff6ada597695cdfc675c44641e3c0541))

### Testing

- **render**: Move the expected-rendering helper into a conftest fixture
  ([`2c1510d`](https://github.com/justmatias/mstack/commit/2c1510df9d13c2b12998904352362b9880147564))


## v5.3.0 (2026-11-21)

### Features

- **cleanup**: Prune old mstack backups
  ([`1fd4c5f`](https://github.com/justmatias/mstack/commit/1fd4c5f7c8662617950aadf9fafdd77837342fea))


## v5.2.0 (2026-11-21)

### Features

- **skills**: Add five skills adapted from pstack
  ([`8f739b0`](https://github.com/justmatias/mstack/commit/8f739b0da3fa8b38dadf7666fe8d78859481b07f))

- **skills**: Delete the merged branch at the end of full-send
  ([`3c083ca`](https://github.com/justmatias/mstack/commit/3c083ca555ac9515193622d6c93b0ff9b5af6199))


## v5.1.1 (2026-11-21)

### Bug Fixes

- **ci**: Keep the bump-level regexes in variables
  ([#53](https://github.com/justmatias/mstack/pull/53),
  [`2540dd5`](https://github.com/justmatias/mstack/commit/2540dd54d77501e7317ff1aebadf22f8aa93987f))

- **ci**: Make the release-prepare bump commit and re-run cleanly
  ([`347bcea`](https://github.com/justmatias/mstack/commit/347bceaac47a30f00362e4f3897674e2ff7432ae))

- **ci**: Quote the bump level values for shellcheck
  ([#53](https://github.com/justmatias/mstack/pull/53),
  [`2540dd5`](https://github.com/justmatias/mstack/commit/2540dd54d77501e7317ff1aebadf22f8aa93987f))

- **skills**: Remove stale top-level copies of shipping skills
  ([#49](https://github.com/justmatias/mstack/pull/49),
  [`5a9037a`](https://github.com/justmatias/mstack/commit/5a9037afae89defd39d2300d027a3b2f78dc3c65))

### Continuous Integration

- **release**: Bump the version inside the PR instead of pushing to main
  ([#53](https://github.com/justmatias/mstack/pull/53),
  [`2540dd5`](https://github.com/justmatias/mstack/commit/2540dd54d77501e7317ff1aebadf22f8aa93987f))

- **release**: Bump the version inside the PR so main never needs a push
  ([#53](https://github.com/justmatias/mstack/pull/53),
  [`2540dd5`](https://github.com/justmatias/mstack/commit/2540dd54d77501e7317ff1aebadf22f8aa93987f))

- **release**: Update the pinned mstack revision in the README on each release
  ([#52](https://github.com/justmatias/mstack/pull/52),
  [`d10003d`](https://github.com/justmatias/mstack/commit/d10003ddade6c978836907b9060ed0b981ea2244))

### Documentation

- **skills**: Pin reflect and correct to the upstream pstack commit
  ([#48](https://github.com/justmatias/mstack/pull/48),
  [`d640c98`](https://github.com/justmatias/mstack/commit/d640c98afcb754703abd28fe48465b70b46204b6))

- **specs**: Drop specs the agent-driven setup made moot
  ([#54](https://github.com/justmatias/mstack/pull/54),
  [`489ec5f`](https://github.com/justmatias/mstack/commit/489ec5fd1edd20111084455227e9e61da9e33e89))

### Features

- **skills**: Add full-send, full-stop, babysit-pr and review-loop
  ([#47](https://github.com/justmatias/mstack/pull/47),
  [`93a366a`](https://github.com/justmatias/mstack/commit/93a366a72684628c5f38adae07a423abe18de192))

- **skills**: Add full-send, full-stop, babysit-pr and review-loop
  ([#45](https://github.com/justmatias/mstack/pull/45),
  [`f6a8ddd`](https://github.com/justmatias/mstack/commit/f6a8dddb9f5097932266b28ef0d0ece94a9029d5))

- **skills**: Add grill-me, handoff and research from mattpocock/skills
  ([#50](https://github.com/justmatias/mstack/pull/50),
  [`86513b5`](https://github.com/justmatias/mstack/commit/86513b590d4036537b5412752d6c7dd377f961a9))

- **skills**: Add implement cadence and declutter step to full-send
  ([#47](https://github.com/justmatias/mstack/pull/47),
  [`93a366a`](https://github.com/justmatias/mstack/commit/93a366a72684628c5f38adae07a423abe18de192))

- **skills**: Add implement cadence and declutter step to full-send
  ([#45](https://github.com/justmatias/mstack/pull/45),
  [`f6a8ddd`](https://github.com/justmatias/mstack/commit/f6a8dddb9f5097932266b28ef0d0ece94a9029d5))

- **skills**: Add show-me skill adapted from humanlayer/skills
  ([#49](https://github.com/justmatias/mstack/pull/49),
  [`5a9037a`](https://github.com/justmatias/mstack/commit/5a9037afae89defd39d2300d027a3b2f78dc3c65))

### Refactoring

- **skills**: Group skills by topic ([#47](https://github.com/justmatias/mstack/pull/47),
  [`93a366a`](https://github.com/justmatias/mstack/commit/93a366a72684628c5f38adae07a423abe18de192))

- **skills**: Rename open-pull-request to open-pr
  ([#51](https://github.com/justmatias/mstack/pull/51),
  [`962d65c`](https://github.com/justmatias/mstack/commit/962d65c118b946b6f7e57eaa4a57739576934acd))

- **skills**: Trim duplicated text from four skills
  ([#51](https://github.com/justmatias/mstack/pull/51),
  [`962d65c`](https://github.com/justmatias/mstack/commit/962d65c118b946b6f7e57eaa4a57739576934acd))

- **skills**: Trim duplicated text from integrate, declutter, show-me and open-pull-request
  ([#51](https://github.com/justmatias/mstack/pull/51),
  [`962d65c`](https://github.com/justmatias/mstack/commit/962d65c118b946b6f7e57eaa4a57739576934acd))


## v5.1.0 (2026-11-20)

### Documentation

- List the pstack skills and their overlaps ([#43](https://github.com/justmatias/mstack/pull/43),
  [`cff5a87`](https://github.com/justmatias/mstack/commit/cff5a8755a0c693000411ecc3f895688d0c0786c))

### Features

- **agents**: Add comment-sicko and the no-comments skill
  ([#43](https://github.com/justmatias/mstack/pull/43),
  [`cff5a87`](https://github.com/justmatias/mstack/commit/cff5a8755a0c693000411ecc3f895688d0c0786c))

- **rules**: Forbid AI attribution in commits and PRs
  ([#43](https://github.com/justmatias/mstack/pull/43),
  [`cff5a87`](https://github.com/justmatias/mstack/commit/cff5a8755a0c693000411ecc3f895688d0c0786c))

- **skills**: Add bro ([#43](https://github.com/justmatias/mstack/pull/43),
  [`cff5a87`](https://github.com/justmatias/mstack/commit/cff5a8755a0c693000411ecc3f895688d0c0786c))

- **skills**: Add how and why ([#43](https://github.com/justmatias/mstack/pull/43),
  [`cff5a87`](https://github.com/justmatias/mstack/commit/cff5a8755a0c693000411ecc3f895688d0c0786c))

- **skills**: Add leave-pr-comments ([#42](https://github.com/justmatias/mstack/pull/42),
  [`b6ff6ed`](https://github.com/justmatias/mstack/commit/b6ff6ed3c66f06caec55f5cc7a3a5c05ffcb7777))

- **skills**: Add modernize ([#42](https://github.com/justmatias/mstack/pull/42),
  [`b6ff6ed`](https://github.com/justmatias/mstack/commit/b6ff6ed3c66f06caec55f5cc7a3a5c05ffcb7777))

- **skills**: Add open-pull-request ([#42](https://github.com/justmatias/mstack/pull/42),
  [`b6ff6ed`](https://github.com/justmatias/mstack/commit/b6ff6ed3c66f06caec55f5cc7a3a5c05ffcb7777))

- **skills**: Add open-pull-request, leave-pr-comments and modernize
  ([#42](https://github.com/justmatias/mstack/pull/42),
  [`b6ff6ed`](https://github.com/justmatias/mstack/commit/b6ff6ed3c66f06caec55f5cc7a3a5c05ffcb7777))

- **skills**: Add pstack skills and the comment-sicko agent
  ([#43](https://github.com/justmatias/mstack/pull/43),
  [`cff5a87`](https://github.com/justmatias/mstack/commit/cff5a8755a0c693000411ecc3f895688d0c0786c))

- **skills**: Add recall ([#43](https://github.com/justmatias/mstack/pull/43),
  [`cff5a87`](https://github.com/justmatias/mstack/commit/cff5a8755a0c693000411ecc3f895688d0c0786c))

- **skills**: Add sharpen ([#43](https://github.com/justmatias/mstack/pull/43),
  [`cff5a87`](https://github.com/justmatias/mstack/commit/cff5a8755a0c693000411ecc3f895688d0c0786c))

- **skills**: Add teach ([#43](https://github.com/justmatias/mstack/pull/43),
  [`cff5a87`](https://github.com/justmatias/mstack/commit/cff5a8755a0c693000411ecc3f895688d0c0786c))

- **skills**: Add unslop ([#43](https://github.com/justmatias/mstack/pull/43),
  [`cff5a87`](https://github.com/justmatias/mstack/commit/cff5a8755a0c693000411ecc3f895688d0c0786c))

### Refactoring

- **skills**: Rename code-simplification to declutter
  ([#43](https://github.com/justmatias/mstack/pull/43),
  [`cff5a87`](https://github.com/justmatias/mstack/commit/cff5a8755a0c693000411ecc3f895688d0c0786c))


## v5.0.0 (2026-11-20)

### Documentation

- **specs**: Plan a shared ~/.agents/skills copy in more-agent-tools
  ([#40](https://github.com/justmatias/mstack/pull/40),
  [`a25eeb7`](https://github.com/justmatias/mstack/commit/a25eeb77a606f0f728c1707f000c5afd1f3179fa))

### Features

- **doctor**: Add the repair skill and point doctor's fixes at it
  ([#39](https://github.com/justmatias/mstack/pull/39),
  [`783e67e`](https://github.com/justmatias/mstack/commit/783e67e057d9dc51f1fbad44d6c6dc0d45b3ec54))

- **setup**: Let the agent drive setup, and drop the manifest
  ([#40](https://github.com/justmatias/mstack/pull/40),
  [`a25eeb7`](https://github.com/justmatias/mstack/commit/a25eeb77a606f0f728c1707f000c5afd1f3179fa))

- **setup**: Load the setup skill from .agents/skills for every agent
  ([#40](https://github.com/justmatias/mstack/pull/40),
  [`a25eeb7`](https://github.com/justmatias/mstack/commit/a25eeb77a606f0f728c1707f000c5afd1f3179fa))

- **skills**: Add code-simplification from addyosmani/agent-skills
  ([#39](https://github.com/justmatias/mstack/pull/39),
  [`783e67e`](https://github.com/justmatias/mstack/commit/783e67e057d9dc51f1fbad44d6c6dc0d45b3ec54))

- **skills**: Add review, code-simplification and repair
  ([#39](https://github.com/justmatias/mstack/pull/39),
  [`783e67e`](https://github.com/justmatias/mstack/commit/783e67e057d9dc51f1fbad44d6c6dc0d45b3ec54))

- **skills**: Add the review skill ([#39](https://github.com/justmatias/mstack/pull/39),
  [`783e67e`](https://github.com/justmatias/mstack/commit/783e67e057d9dc51f1fbad44d6c6dc0d45b3ec54))


## v4.2.0 (2026-11-20)

### Features

- **doctor**: Add the repair skill and point doctor's fixes at it
  ([#39](https://github.com/justmatias/mstack/pull/39),
  [`783e67e`](https://github.com/justmatias/mstack/commit/783e67e057d9dc51f1fbad44d6c6dc0d45b3ec54))

- **skills**: Add code-simplification from addyosmani/agent-skills
  ([#39](https://github.com/justmatias/mstack/pull/39),
  [`783e67e`](https://github.com/justmatias/mstack/commit/783e67e057d9dc51f1fbad44d6c6dc0d45b3ec54))

- **skills**: Add review, code-simplification and repair
  ([#39](https://github.com/justmatias/mstack/pull/39),
  [`783e67e`](https://github.com/justmatias/mstack/commit/783e67e057d9dc51f1fbad44d6c6dc0d45b3ec54))

- **skills**: Add the review skill ([#39](https://github.com/justmatias/mstack/pull/39),
  [`783e67e`](https://github.com/justmatias/mstack/commit/783e67e057d9dc51f1fbad44d6c6dc0d45b3ec54))


## v4.1.0 (2026-11-20)

### Features

- **skills**: Decide between a static check and llm-review
  ([#38](https://github.com/justmatias/mstack/pull/38),
  [`b81b704`](https://github.com/justmatias/mstack/commit/b81b70481b48dabeb1b0bc73c7c4c30ac7414132))


## v4.0.0 (2026-11-20)

### Features

- **integrate**: Integrate rules from GitHub, not only skills
  ([#37](https://github.com/justmatias/mstack/pull/37),
  [`e2a3120`](https://github.com/justmatias/mstack/commit/e2a31201e7d3a62562e491a4e2af2601f53b882b))

- **skills**: Integrate rules, and shorten the skill names
  ([#37](https://github.com/justmatias/mstack/pull/37),
  [`e2a3120`](https://github.com/justmatias/mstack/commit/e2a31201e7d3a62562e491a4e2af2601f53b882b))

- **skills**: Shorten the skill names ([#37](https://github.com/justmatias/mstack/pull/37),
  [`e2a3120`](https://github.com/justmatias/mstack/commit/e2a31201e7d3a62562e491a4e2af2601f53b882b))


## v3.13.0 (2026-11-20)

### Features

- **platform**: Behave the same on Linux, macOS, Windows and WSL
  ([#31](https://github.com/justmatias/mstack/pull/31),
  [`4c846e4`](https://github.com/justmatias/mstack/commit/4c846e438e328b5012a436886c5567a8d42b4d06))


## v3.12.0 (2026-11-20)

### Features

- **doctor**: Verify a machine's setup with mstack doctor
  ([#30](https://github.com/justmatias/mstack/pull/30),
  [`1c38399`](https://github.com/justmatias/mstack/commit/1c3839956dc3c5c3e3ea3e69a8c8d26372773e0a))


## v3.11.0 (2026-11-20)

### Features

- **init**: Scaffold the rules-as-checks layout with mstack init
  ([#29](https://github.com/justmatias/mstack/pull/29),
  [`4e400cc`](https://github.com/justmatias/mstack/commit/4e400cc3939396d379ab256a1b5ff6681141205b))


## v3.10.0 (2026-11-20)

### Features

- **ci**: Add a reusable GitHub Action that runs mstack lint
  ([#28](https://github.com/justmatias/mstack/pull/28),
  [`ef8c991`](https://github.com/justmatias/mstack/commit/ef8c99132afedf96f2ab08b7c55b89e3c627cc66))


## v3.9.0 (2026-11-20)

### Features

- **hooks**: Publish the checks as pre-commit hooks for other repos
  ([#27](https://github.com/justmatias/mstack/pull/27),
  [`887650d`](https://github.com/justmatias/mstack/commit/887650dd7f80ade5d4d13dac64d278f0c52a0b4c))


## v3.8.0 (2026-11-20)

### Features

- **rules**: Add test-code rules and checks ([#34](https://github.com/justmatias/mstack/pull/34),
  [`bda9b66`](https://github.com/justmatias/mstack/commit/bda9b66b017c3ea90068cd9ade306bbd6cdc13a6))


## v3.7.0 (2026-11-20)

### Bug Fixes

- **platform**: Portable config paths and test homes on Windows
  ([#35](https://github.com/justmatias/mstack/pull/35),
  [`adee83e`](https://github.com/justmatias/mstack/commit/adee83e95360551bc247d50344bb16fdc04b0f9f))

### Documentation

- **commit-msg**: Document the command and [commits] in the README
  ([#35](https://github.com/justmatias/mstack/pull/35),
  [`adee83e`](https://github.com/justmatias/mstack/commit/adee83e95360551bc247d50344bb16fdc04b0f9f))

### Features

- **coverage**: Let a rule be enforced by a pre-commit hook
  ([#35](https://github.com/justmatias/mstack/pull/35),
  [`adee83e`](https://github.com/justmatias/mstack/commit/adee83e95360551bc247d50344bb16fdc04b0f9f))

- **rules**: Add git commit rules and mstack commit-msg
  ([#35](https://github.com/justmatias/mstack/pull/35),
  [`adee83e`](https://github.com/justmatias/mstack/commit/adee83e95360551bc247d50344bb16fdc04b0f9f))


## v3.6.0 (2026-11-20)

### Bug Fixes

- **platform**: Portable config paths and test homes on Windows
  ([#33](https://github.com/justmatias/mstack/pull/33),
  [`9f4f831`](https://github.com/justmatias/mstack/commit/9f4f83126d24cc5a9733d0c8932bdae862515307))

### Features

- **coverage**: Let a rule be enforced by a pre-commit hook
  ([#33](https://github.com/justmatias/mstack/pull/33),
  [`9f4f831`](https://github.com/justmatias/mstack/commit/9f4f83126d24cc5a9733d0c8932bdae862515307))

- **rules**: Add shell script rules and checks ([#33](https://github.com/justmatias/mstack/pull/33),
  [`9f4f831`](https://github.com/justmatias/mstack/commit/9f4f83126d24cc5a9733d0c8932bdae862515307))

### Testing

- **lint**: Copy the pre-commit config into the lint sandbox
  ([#33](https://github.com/justmatias/mstack/pull/33),
  [`9f4f831`](https://github.com/justmatias/mstack/commit/9f4f83126d24cc5a9733d0c8932bdae862515307))

- **lint**: Name the scanned sample so leak-check ignores the rules' prose
  ([#33](https://github.com/justmatias/mstack/pull/33),
  [`9f4f831`](https://github.com/justmatias/mstack/commit/9f4f83126d24cc5a9733d0c8932bdae862515307))


## v3.5.0 (2026-11-20)

### Bug Fixes

- **coverage**: Ignore malformed entries in the pre-commit config
  ([#32](https://github.com/justmatias/mstack/pull/32),
  [`9ec992d`](https://github.com/justmatias/mstack/commit/9ec992d7f247b92102ea46fc6391e0cff62e20b1))

- **platform**: Portable config paths and test homes on Windows
  ([#32](https://github.com/justmatias/mstack/pull/32),
  [`9ec992d`](https://github.com/justmatias/mstack/commit/9ec992d7f247b92102ea46fc6391e0cff62e20b1))

### Features

- **coverage**: Let a rule be enforced by a pre-commit hook
  ([#32](https://github.com/justmatias/mstack/pull/32),
  [`9ec992d`](https://github.com/justmatias/mstack/commit/9ec992d7f247b92102ea46fc6391e0cff62e20b1))


## v3.4.0 (2026-11-20)

### Features

- **lint**: Ship ast-grep and import-linter with the CLI and add mstack lint
  ([#26](https://github.com/justmatias/mstack/pull/26),
  [`64f6b14`](https://github.com/justmatias/mstack/commit/64f6b142849c0f42fb010b8b8434d6b82f3464bc))


## v3.3.0 (2026-11-20)

### Features

- **guards**: Add mstack skills-check to validate skills
  ([#24](https://github.com/justmatias/mstack/pull/24),
  [`1b016e7`](https://github.com/justmatias/mstack/commit/1b016e77dcf8e5c23f45992e76f4befeff6051f8))


## v3.2.0 (2026-11-20)

### Documentation

- **setup-mstack**: Reword which items step 5 asks about
  ([#23](https://github.com/justmatias/mstack/pull/23),
  [`378b672`](https://github.com/justmatias/mstack/commit/378b6723f0f233eebb6c1fb7554cc0894c0e318c))

### Features

- **install**: Add agents, MCP servers, instructions and settings folders
  ([#23](https://github.com/justmatias/mstack/pull/23),
  [`378b672`](https://github.com/justmatias/mstack/commit/378b6723f0f233eebb6c1fb7554cc0894c0e318c))

- **install**: Record installed items in a manifest
  ([#23](https://github.com/justmatias/mstack/pull/23),
  [`378b672`](https://github.com/justmatias/mstack/commit/378b6723f0f233eebb6c1fb7554cc0894c0e318c))


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
