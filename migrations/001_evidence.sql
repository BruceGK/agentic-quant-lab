BEGIN;

CREATE TABLE audit_events (
    sequence bigint PRIMARY KEY CHECK (sequence > 0),
    event_id uuid NOT NULL UNIQUE,
    kind text NOT NULL CHECK (kind IN (
        'discovery', 'filing', 'universe', 'reconciliation', 'correction'
    )),
    recorded_at timestamptz NOT NULL,
    prev_hash text NOT NULL CHECK (length(prev_hash) = 64),
    record_hash text NOT NULL UNIQUE CHECK (length(record_hash) = 64),
    payload jsonb NOT NULL
);

CREATE TABLE discoveries (
    source text NOT NULL,
    external_id text NOT NULL,
    event_id uuid NOT NULL UNIQUE REFERENCES audit_events(event_id),
    first_seen_at timestamptz NOT NULL,
    PRIMARY KEY (source, external_id)
);

CREATE TABLE filings (
    event_id uuid PRIMARY KEY REFERENCES audit_events(event_id),
    source text NOT NULL,
    external_id text NOT NULL,
    cik text NOT NULL,
    form_type text NOT NULL,
    document_url text NOT NULL,
    accepted_at timestamptz NOT NULL,
    first_seen_at timestamptz NOT NULL,
    fetched_at timestamptz NOT NULL,
    decision_eligible_at timestamptz NOT NULL,
    content_sha256 text NOT NULL CHECK (length(content_sha256) = 64),
    UNIQUE (source, external_id),
    FOREIGN KEY (source, external_id) REFERENCES discoveries(source, external_id),
    CHECK (first_seen_at <= fetched_at),
    CHECK (decision_eligible_at = fetched_at)
);

CREATE TABLE corrections (
    event_id uuid PRIMARY KEY REFERENCES audit_events(event_id),
    supersedes_event_id uuid NOT NULL REFERENCES audit_events(event_id),
    reason text NOT NULL CHECK (length(reason) > 0),
    changes jsonb NOT NULL
);

CREATE VIEW universe_snapshots AS
    SELECT event_id, recorded_at, payload FROM audit_events WHERE kind = 'universe';

CREATE VIEW reconciliations AS
    SELECT event_id, recorded_at, payload FROM audit_events WHERE kind = 'reconciliation';

CREATE FUNCTION reject_evidence_mutation() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Evidence is append-only; append a correction instead'
        USING ERRCODE = '55000';
END;
$$;

CREATE TRIGGER audit_events_append_only
BEFORE UPDATE OR DELETE OR TRUNCATE ON audit_events
FOR EACH STATEMENT EXECUTE FUNCTION reject_evidence_mutation();
CREATE TRIGGER discoveries_append_only
BEFORE UPDATE OR DELETE OR TRUNCATE ON discoveries
FOR EACH STATEMENT EXECUTE FUNCTION reject_evidence_mutation();
CREATE TRIGGER filings_append_only
BEFORE UPDATE OR DELETE OR TRUNCATE ON filings
FOR EACH STATEMENT EXECUTE FUNCTION reject_evidence_mutation();
CREATE TRIGGER corrections_append_only
BEFORE UPDATE OR DELETE OR TRUNCATE ON corrections
FOR EACH STATEMENT EXECUTE FUNCTION reject_evidence_mutation();

ALTER TABLE audit_events ENABLE ALWAYS TRIGGER audit_events_append_only;
ALTER TABLE discoveries ENABLE ALWAYS TRIGGER discoveries_append_only;
ALTER TABLE filings ENABLE ALWAYS TRIGGER filings_append_only;
ALTER TABLE corrections ENABLE ALWAYS TRIGGER corrections_append_only;

COMMIT;
