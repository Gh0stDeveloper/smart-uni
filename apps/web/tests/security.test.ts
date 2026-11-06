import test from "node:test";
import assert from "node:assert/strict";
import { allowedOrigin, backendUrl, validSessionId } from "../lib/security";

test("la sesión requiere un ID concreto y no confía en objetos vacíos", () => {
  assert.equal(validSessionId(undefined), false);
  assert.equal(validSessionId({ message: "error auth()" }), false);
  assert.equal(validSessionId(""), false);
  assert.equal(validSessionId("synthetic-subject"), true);
});
test("CSRF: rechaza ausencia de Origin, ataques cross-origin o HTTP", () => {
  const good = "https://portal.smartuni.invalid";
  assert.equal(allowedOrigin(good, good), true);
  assert.equal(allowedOrigin("http://localhost:3000", "http://localhost:3000", true), true);
  assert.equal(allowedOrigin("http://evil.invalid", "http://evil.invalid", true), false);
  for (const bad of [null, "", "https://evil.invalid", "http://portal.smartuni.invalid",
    "https://portal.smartuni.invalid.evil.invalid", "https://portal.smartuni.invalid/"]) {
    assert.equal(allowedOrigin(bad, good), false);
  }
});
test("BFF: la URL backend no admite parámetros, credenciales ni HTTP productivo", () => {
  assert.equal(backendUrl("https://api.smartuni.invalid/", "/api/v1/notes", true),
    "https://api.smartuni.invalid/api/v1/notes");
  assert.throws(() => backendUrl("http://localhost:8000", "/api/v1/notes", true));
  assert.throws(() => backendUrl("https://user:secret@api.smartuni.invalid/", "/api/v1/notes", true));
  assert.throws(() => backendUrl("https://api.smartuni.invalid/?target=evil", "/api/v1/notes", true));
  assert.throws(() => backendUrl("https://api.smartuni.invalid/", "https://evil.invalid", true));
  assert.equal(backendUrl("http://127.0.0.1:8000/", "/api/v1/me", false),
    "http://127.0.0.1:8000/api/v1/me");
});
