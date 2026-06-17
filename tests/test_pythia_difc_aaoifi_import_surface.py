def test_canonical_aaoifi_import_surface_exists():
    from pythia_finance_audit.difc_aaoifi_bridge import generate_sample_difc_sukuk_packet

    packet = generate_sample_difc_sukuk_packet(drift=False)
    assert packet["schema"] == "PYTHIA_DIFC_AAOIFI_SUKUK_AUDIT_V1"
    assert packet["automatic_action_allowed"] is False
