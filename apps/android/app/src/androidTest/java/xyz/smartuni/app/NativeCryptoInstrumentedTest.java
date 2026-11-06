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
}
