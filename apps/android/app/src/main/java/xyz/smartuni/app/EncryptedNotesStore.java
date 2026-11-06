package xyz.smartuni.app;

import android.content.Context;
import android.util.AtomicFile;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import java.util.Arrays;

/** Apunte local único, cifrado por smartuni-core y escrito de forma atómica. */
final class EncryptedNotesStore {
    static final int MAX_NOTE_BYTES = 64 * 1024;
    private static final byte[] CONTEXT =
            "smartuni/android/local-note/v1".getBytes(StandardCharsets.UTF_8);
    private final Context app;

    EncryptedNotesStore(Context context) {
        app = context.getApplicationContext();
    }

    byte[] read() throws IOException, GeneralSecurityException {
        AtomicFile file = new AtomicFile(new File(app.getFilesDir(), "local_note.sun1"));
        if (!file.getBaseFile().exists()) {
            return new byte[0];
        }
        byte[] blob = file.readFully();
        if (blob.length > MAX_NOTE_BYTES + 512) {
            throw new GeneralSecurityException("Archivo demasiado grande");
        }
        byte[] key = new KeyVault(app).loadOrCreate();
        try {
            byte[] plain = NativeBridge.open(key, CONTEXT, blob);
            if (plain == null || plain.length > MAX_NOTE_BYTES) {
                throw new GeneralSecurityException("Nota corrupta o clave incorrecta");
            }
            return plain;
        } finally {
            Arrays.fill(key, (byte) 0);
        }
    }

    void save(byte[] plaintext) throws IOException, GeneralSecurityException {
        if (plaintext == null || plaintext.length > MAX_NOTE_BYTES) {
            throw new GeneralSecurityException("Nota excede el límite de 64 KiB");
        }
        byte[] key = new KeyVault(app).loadOrCreate();
        byte[] ciphertext;
        try {
            ciphertext = NativeBridge.seal(key, CONTEXT, plaintext);
        } finally {
            Arrays.fill(key, (byte) 0);
        }
        if (ciphertext == null || ciphertext.length == 0) {
            throw new GeneralSecurityException("El núcleo nativo rechazó el cifrado");
        }
        AtomicFile file = new AtomicFile(new File(app.getFilesDir(), "local_note.sun1"));
        FileOutputStream output = file.startWrite();
        try {
            output.write(ciphertext);
            file.finishWrite(output);
        } catch (IOException exception) {
            file.failWrite(output);
            throw exception;
        }
    }
}
