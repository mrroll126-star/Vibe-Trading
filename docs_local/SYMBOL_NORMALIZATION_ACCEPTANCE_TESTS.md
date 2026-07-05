# Symbol Normalization Acceptance Tests

Status: implemented for pure helper tests.

These are acceptance cases for a future symbol normalization implementation. They should be runnable without network for deterministic rules. Name-resolution cases can use a local security master fixture.

## 1. Test Table

| 输入 | 上下文 | 期望标准 symbol | market | asset_type | 是否需确认 | 备注 |
|---|---|---|---|---|---|---|
| `QQQ` | none | `QQQ.US` | US | etf | no | Common US ETF. |
| `SPY` | none | `SPY.US` | US | etf | no | Regression for prior bare-symbol issue. |
| `AAPL` | none | `AAPL.US` | US | stock | no | Pure letters default to US. |
| `NVDA` | none | `NVDA.US` | US | stock | no | Pure letters default to US. |
| `QQQ.US` | none | `QQQ.US` | US | etf | no | Already normalized. |
| `600519` | none | `600519.SH` | CN | stock | no | Shanghai stock prefix. |
| `300750` | none | `300750.SZ` | CN | stock | no | Shenzhen ChiNext prefix. |
| `000001` | none | `000001.SZ` | CN | stock | yes | Ambiguous with index concept; default stock but warn. |
| `601318` | none | `601318.SH` | CN | stock | no | Shanghai stock prefix. |
| `510300` | none | `510300.SH` | CN | etf | no | Shanghai ETF prefix. |
| `159915` | none | `159915.SZ` | CN | etf | no | Shenzhen ETF prefix. |
| `600519.SH` | none | `600519.SH` | CN | stock | no | Already normalized. |
| `SH600519` | none | `600519.SH` | CN | stock | no | Exchange prefix form. |
| `sh.600519` | none | `600519.SH` | CN | stock | no | BaoStock-style prefix form. |
| `300750.SZ` | none | `300750.SZ` | CN | stock | no | Already normalized. |
| `SZ300750` | none | `300750.SZ` | CN | stock | no | Exchange prefix form. |
| `sz.300750` | none | `300750.SZ` | CN | stock | no | BaoStock-style prefix form. |
| `700` | HK | `00700.HK` | HK | stock | no | HK context pads to five digits. |
| `0700` | HK | `00700.HK` | HK | stock | no | HK context pads to five digits. |
| `00700` | none | `00700.HK` | HK | stock | maybe | Known mapping for Tencent can avoid confirmation; otherwise ask. |
| `9988` | HK | `09988.HK` | HK | stock | no | HK context pads to five digits. |
| `09988` | HK | `09988.HK` | HK | stock | no | Already five-digit HK base. |
| `00700.HK` | none | `00700.HK` | HK | stock | no | Already normalized. |
| `HK.00700` | none | `00700.HK` | HK | stock | no | Prefix form. |
| `贵州茅台` | none | `600519.SH` | CN | stock | no | Requires local security master fixture. |
| `宁德时代` | none | `300750.SZ` | CN | stock | no | Requires local security master fixture. |
| `腾讯` | none | `00700.HK` | HK | stock | no | Requires local security master fixture. |
| `阿里巴巴` | none | empty primary | multi | stock | yes | Candidates: `BABA.US`, `09988.HK`. |
| `中国平安` | none | empty primary | multi | stock | yes | Candidates: `601318.SH`, `02318.HK`. |
| empty string | none | empty primary | UNKNOWN | unknown | no | Return validation error. |
| `not-a-code` | none | empty primary | UNKNOWN | unknown | no | Return invalid-symbol warning. |
| `123` | none | empty primary | UNKNOWN or HK | unknown | yes | Too ambiguous without HK context or name mapping. |
| `ABCDEFG` | none | empty primary | UNKNOWN | unknown | no | Too long for default US ticker rule. |
| `000001` | none | `000001.SZ` | CN | stock | yes | Warn: may be confused with index. |
| `000001` | index | `000001.SH` or index-standard TBD | CN | index | yes | Requires explicit index policy. |
| `00700` | HK | `00700.HK` | HK | stock | no | Context removes ambiguity. |
| `00700` | CN | empty primary | UNKNOWN | unknown | yes | Do not silently convert to A-share. |

## 2. Coverage Count

| Category | Count |
| -- | --: |
| US | 5 |
| A-share | 12 |
| HK | 7 |
| Chinese name | 5 |
| Boundary / ambiguity | 8 |

## 3. Acceptance Rules

A future implementation passes this design gate when:

* All deterministic tests pass without network.
* Already-normalized symbols pass through unchanged except casing/padding.
* Ambiguous names return candidates instead of guessing.
* Warnings are produced for `000001`, `123`, and context-conflicting `00700`.
* Normalized output includes the structured fields defined in `SYMBOL_NORMALIZATION_DESIGN.md`.
* No provider chain changes are required for the tests to pass.

## 4. Suggested Test Locations

Future implementation test files:

```text
agent/tests/test_symbol_normalizer.py
agent/tests/fixtures/security_master_minimal.json
```

Optional later integration tests:

```text
agent/tests/integration/test_symbol_search_resolution.py
```

## 5. Minimal Helper Test Result

Date: 2026-07-05.

Implemented test file:

```text
agent/tests/test_symbol_normalizer.py
```

Primary command attempted:

```bash
.venv/bin/python -m pytest agent/tests/test_symbol_normalizer.py
```

Result:

* Failed because `pytest` is not installed in the current `.venv`.
* `pyproject.toml` declares pytest under the `dev` optional extra, but this environment was installed without dev extras.

Fallback command used:

```bash
.venv/bin/python -m unittest agent.tests.test_symbol_normalizer
```

Result:

* Passed.
* 12 unittest test methods ran.
* The test methods cover the acceptance categories above using subtests.

Boundary:

* No dependency was installed.
* No network was used.
* No provider was called.
* Existing tools/loaders were not changed.
