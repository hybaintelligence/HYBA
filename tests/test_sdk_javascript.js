import assert from 'node:assert/strict';
import test from 'node:test';

test('javascript sdk staging test is opt-in', () => {
  if (!process.env.HYBA_STAGING_URL) {
    assert.equal(Boolean(process.env.HYBA_STAGING_URL), false);
    return;
  }
});
