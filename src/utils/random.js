import crypto from "crypto";

export function secureRandom() {
  return crypto.randomBytes(4).readUInt32LE() / 0xffffffff;
}
