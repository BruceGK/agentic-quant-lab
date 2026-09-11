BEGIN;

ALTER TABLE audit_events DROP CONSTRAINT audit_events_kind_check;
ALTER TABLE audit_events ADD CONSTRAINT audit_events_kind_check CHECK (kind IN (
    'discovery', 'filing', 'universe', 'reconciliation', 'correction', 'archive_recovery'
));

COMMIT;
