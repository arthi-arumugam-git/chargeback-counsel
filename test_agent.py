from disputeagent import agent, mock_airwallex as api
def test_loop():
    log={s["dispute"]:s for s in agent.run()}
    assert log["dsp_002"]["action"].startswith("accept")
    assert log["dsp_001"]["action"]=="evidence submitted"
    assert "dsp_003" in api.SUBMITTED
    assert api.SUBMITTED["dsp_001"]["file_ids"] and api.SUBMITTED["dsp_003"]["file_ids"]
