import os
import pytest

from sdks.python.hyba_client import HYBAClient, HYBAAuthError


def test_python_sdk_requires_api_key():
    with pytest.raises(HYBAAuthError):
        HYBAClient(api_key="")


@pytest.mark.skipif(
    not os.getenv("HYBA_STAGING_URL"), reason="HYBA_STAGING_URL not set"
)
def test_python_sdk_hits_staging_qiaas_predict():
    client = HYBAClient(
        api_key=os.environ["HYBA_API_KEY"], base_url=os.environ["HYBA_STAGING_URL"]
    )
    response = client.qiaas.predict({"signal": "sdk-smoke"})
    assert "qi_execution_id" in response
