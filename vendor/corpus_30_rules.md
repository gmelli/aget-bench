<!-- VENDORED PRIOR WORK (poc/vocab-spec-compliance, Feb 2026) — NOT a Build Day contribution. See README. -->
# Agent Configuration

## Mandatory Rules

The agent SHALL follow all rules below when implementing code.

### Input & Data Rules (R-001 to R-006)

R-001: The agent SHALL validate all function parameters against expected types before processing.
R-002: The agent SHALL reject negative values for quantity parameters.
R-003: The agent SHALL sanitize all string inputs that will be used in database queries.
R-004: The agent SHALL escape HTML entities in user-provided content before rendering.
R-005: The agent SHALL validate email format using regex before accepting email fields.
R-006: The agent SHALL strip leading/trailing whitespace from all text inputs.

### Error Handling Rules (R-007 to R-012)

R-007: The agent SHALL use domain-specific exception classes rather than generic Exception.
R-008: The agent SHALL include the original error context when re-raising exceptions.
R-009: The agent SHALL log all caught exceptions at ERROR level with stack trace.
R-010: The agent SHALL return structured error responses with error code, message, and timestamp.
R-011: The agent SHALL NOT use bare except clauses.
R-012: The agent SHALL handle timeout errors separately from other exceptions.

### Logging Rules (R-013 to R-018)

R-013: The agent SHALL log function entry at DEBUG level with parameter summary.
R-014: The agent SHALL log function exit at DEBUG level with return value type.
R-015: The agent SHALL log all state-changing operations at INFO level.
R-016: The agent SHALL include correlation_id in all log entries for request tracing.
R-017: The agent SHALL log configuration values at startup at INFO level.
R-018: The agent SHALL NOT log sensitive data (passwords, tokens, PII).

### Architecture Rules (R-019 to R-024)

R-019: The agent SHALL externalize all configuration values into a config object.
R-020: The agent SHALL verify caller permissions before executing privileged operations.
R-021: The agent SHALL release all allocated resources in finally blocks.
R-022: The agent SHALL implement idempotency guards for all write operations.
R-023: The agent SHALL implement rate limiting for all public-facing endpoints.
R-024: The agent SHALL record all state changes in an append-only audit log.

### Quality Rules (R-025 to R-030)

R-025: The agent SHALL include type hints for all function signatures.
R-026: The agent SHALL write docstrings for all public functions with Args, Returns, and Raises sections.
R-027: The agent SHALL use constants instead of magic numbers.
R-028: The agent SHALL keep functions under 30 lines.
R-029: The agent SHALL use descriptive variable names (minimum 3 characters, no single letters except loop indices).
R-030: The agent SHALL include unit tests for all public functions with at least one positive and one negative test case.
