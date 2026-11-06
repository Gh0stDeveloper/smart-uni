package xyz.smartuni.app;

import static org.junit.Assert.*;
import android.content.Context;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import org.junit.runner.RunWith;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;

@RunWith(AndroidJUnit4.class)
public final class NativeCryptoInstrumentedTest {
    @Test public void nativeRustCryptoAndTampering() {
        assertEquals(1, NativeBridge.abiVersion());
        assertTrue(NativeBridge.selfTest());
        byte[] key = new byte[32];
        Arrays.fill(key, (byte) 7);
        byte[] aad = "android-test/one".getBytes(StandardCharsets.UTF_8);
        byte[] input = "Apuntes de prueba ñ".getBytes(StandardCharsets.UTF_8);
        byte[] ciphertext = NativeBridge.seal(key, aad, input);
        assertNotNull(ciphertext);
        assertFalse(Arrays.equals(input, ciphertext));
        assertArrayEquals(input, NativeBridge.open(key, aad, ciphertext));
        ciphertext[ciphertext.length - 1] ^= 1;
        assertNull(NativeBridge.open(key, aad, ciphertext));
        assertNull(NativeBridge.open(new byte[32], aad, ciphertext));
        assertNull(NativeBridge.open(key, "otro".getBytes(StandardCharsets.UTF_8), ciphertext));
    }

    @Test public void keystorePersistsEncryptedNoteAfterReopen() throws Exception {
        Context context = InstrumentationRegistry.getInstrumentation().getTargetContext();
        EncryptedNotesStore store = new EncryptedNotesStore(context);
        byte[] note = "Contenido sintético sin red".getBytes(StandardCharsets.UTF_8);
        store.save(note);
        byte[] raw = new java.io.FileInputStream(
                new java.io.File(context.getFilesDir(), "local_note.sun1")).readAllBytes();
        assertFalse(Arrays.equals(raw, note));
        assertArrayEquals(note, new EncryptedNotesStore(context).read());
    }

    @Test public void rejectCleartextOrUntrustedOrigin() {
        assertEquals(-1, NativeBridge.checkHealth("http://example.com"));
        assertEquals(-1, NativeBridge.checkHealth("https://example.com/path"));
        assertEquals(-1, NativeBridge.checkHealth("https://user@example.com"));
    }

    @Test public void encryptedLocalVaultSurvivesReopenAndRejectsTampering() throws Exception {
        Context context = InstrumentationRegistry.getInstrumentation().getTargetContext();
        LocalVault vault = new LocalVault(context);
        String id = vault.add(LocalVault.TASKS, "Tarea de laboratorio", "", "");
        assertTrue(vault.list(LocalVault.TASKS).length() > 0);
        LocalVault reloaded = new LocalVault(context);
        boolean found = false;
        for (int i = 0; i < reloaded.list(LocalVault.TASKS).length(); i++) {
            if (id.equals(reloaded.list(LocalVault.TASKS).getJSONObject(i).getString("id"))) {
                found = true;
            }
        }
        assertTrue(found);
        java.io.File file = new java.io.File(context.getFilesDir(), "local_vault.sun1");
        byte[] original = java.nio.file.Files.readAllBytes(file.toPath());
        byte[] corrupt = original.clone();
        corrupt[corrupt.length - 1] ^= 0x01;
        try {
            java.nio.file.Files.write(file.toPath(), corrupt);
            boolean rejected = false;
            try {
                new LocalVault(context).list(LocalVault.TASKS);
            } catch (java.security.GeneralSecurityException | org.json.JSONException expected) {
                rejected = true;
            }
            assertTrue("La bóveda alterada no fue rechazada", rejected);
        } finally {
            java.nio.file.Files.write(file.toPath(), original);
            Arrays.fill(original, (byte) 0);
            Arrays.fill(corrupt, (byte) 0);
        }
    }

    @Test public void nativeApiRequiresValidOriginAndTokenWithoutNetwork() {
        byte[] token = "synthetic-bearer-only-for-test".getBytes(StandardCharsets.US_ASCII);
        assertNull(NativeBridge.apiRequest("http://example.invalid", token, 0, 0, null));
        assertNull(NativeBridge.apiRequest("https://example.invalid/path", token, 0, 0, null));
        assertNull(NativeBridge.apiRequest("https://example.invalid", token, 1, -1, null));
        assertNull(NativeBridge.apiRequest("https://example.invalid", token, 5, 0, null));
        assertNull(NativeBridge.apiRequest("https://example.invalid", token, 2, 0, null));
        assertNull(NativeBridge.apiRequest("https://example.invalid", new byte[0], 0, 0, null));
    }

    @Test public void keyWrapIsHeldByAndroidKeyStore() throws Exception {
        Context context = InstrumentationRegistry.getInstrumentation().getTargetContext();
        byte[] secret = new KeyVault(context).loadOrCreate();
        assertEquals(32, secret.length);
        Arrays.fill(secret, (byte) 0);
        java.security.KeyStore store = java.security.KeyStore.getInstance("AndroidKeyStore");
        store.load(null);
        assertTrue(store.containsAlias("smartuni.local.wrap.v1"));
        assertNotNull(store.getKey("smartuni.local.wrap.v1", null));
    }
}
