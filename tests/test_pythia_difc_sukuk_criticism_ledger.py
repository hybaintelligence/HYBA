from pythia_finance_audit.criticism_ledger import (
    LEDGER_SCHEMA_VERSION,
    render_criticism_ledger,
    render_lifecycle_ledger,
    render_packet_ledger,
)
from pythia_finance_audit.difc_aaiofi_bridge import generate_sample_difc_sukuk_packet
from pythia_finance_audit.sukuk_lifecycle_simulation import simulate_sukuk_lifecycle_drift


def test_single_packet_ledger_is_read_only_and_shows_findings():
    packet = generate_sample_difc_sukuk_packet(drift=True)
    rendered = render_packet_ledger(packet)

    assert "PYTHIA DIFC / AAOIFI Read-Only Criticism Ledger" in rendered
    assert LEDGER_SCHEMA_VERSION in rendered
    assert "Automatic action allowed:** `false`" in rendered
    assert "Human review required:** `true`" in rendered
    assert "ESCALATE_TO_SOVEREIGN_HUMAN" in rendered
    assert "DIFC_AAOIFI_ASSET_BACKING_OWNERSHIP" in rendered
    assert "DIFC_AAOIFI_SPV_TRUSTEE_GOVERNANCE" in rendered
    assert "human-review aid" in rendered


def test_lifecycle_ledger_surfaces_first_warning_and_first_blocker():
    bundle = simulate_sukuk_lifecycle_drift(include_packets=False)
    rendered = render_lifecycle_ledger(bundle)

    assert "PYTHIA DIFC / AAOIFI Sukuk Lifecycle Criticism Ledger" in rendered
    assert "First warning step: `03`" in rendered
    assert "First blocker step: `04`" in rendered
    assert "DIFC_AAOIFI_RISK_SHARING_DEBT_MIMICRY" in rendered
    assert "DIFC_AAOIFI_ASSET_BACKING_OWNERSHIP" in rendered
    assert "Automatic action allowed:** `false`" in rendered


def test_generic_renderer_accepts_packet_or_lifecycle_bundle():
    packet = generate_sample_difc_sukuk_packet(drift=False)
    lifecycle = simulate_sukuk_lifecycle_drift(include_packets=False)

    assert "Read-Only Criticism Ledger" in render_criticism_ledger(packet)
    assert "Lifecycle Criticism Ledger" in render_criticism_ledger(lifecycle)
