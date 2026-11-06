package xyz.smartuni.app;

import android.content.Context;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.AtomicFile;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.security.GeneralSecurityException;
import java.security.KeyStore;
import java.security.SecureRandom;
import java.util.Arrays;

import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/**
 * La clave de datos de 256 bits se envuelve con Android Keystore: no se
 * persiste en claro. Rust cifra las notas; Keystore sólo protege la DEK.
 * El material se pierde al desinstalar; recovery sigue pendiente.
 */
final class KeyVault {
    private static final String ALIAS = "smartuni.local.wrap.v1";
    private static final String TRANSFORM = "AES/GCM/NoPadding";
    private static final byte[] AAD = "smartuni/local/keywrap/v1".getBytes(java.nio.charset.StandardCharsets.UTF_8);
    private static final int KEY_LENGTH = 32;
    private static final int IV_LENGTH = 12;
    private final Context app;

    KeyVault(Context context) {
        this.app = context.getApplicationContext();
    }

    private boolean hasEncryptedMaterials() {
        File folder = new File(app.getFilesDir(), "encrypted_materials");
        String[] filenames = folder.list((dir, name) -> name.endsWith(".sun1"));
        return filenames != null && filenames.length > 0;
    }

    byte[] loadOrCreate() throws GeneralSecurityException, IOException {
        AtomicFile file = new AtomicFile(new File(app.getFilesDir(), "local_key.wrap"));
        KeyStore store = KeyStore.getInstance("AndroidKeyStore");
        store.load(null);
        byte[] existing = null;
        if (file.getBaseFile().exists()) {
            if (file.getBaseFile().length() != IV_LENGTH + KEY_LENGTH + 16) {
                throw new GeneralSecurityException("Tamaño de clave envuelta inválido");
            }
            existing = file.readFully();
            if (existing.length != IV_LENGTH + KEY_LENGTH + 16) {
                throw new GeneralSecurityException("Paquete de clave inválido");
            }
        }
        SecretKey wrapping = (SecretKey) store.getKey(ALIAS, null);
        if (existing != null) {
            if (wrapping == null) {
                throw new GeneralSecurityException("Clave Keystore no disponible; se requiere recuperación");
            }
            Cipher cipher = Cipher.getInstance(TRANSFORM);
            cipher.init(Cipher.DECRYPT_MODE, wrapping,
                    new GCMParameterSpec(128, existing, 0, IV_LENGTH));
            cipher.updateAAD(AAD);
            byte[] key = cipher.doFinal(existing, IV_LENGTH, existing.length - IV_LENGTH);
            if (key.length != KEY_LENGTH) {
                Arrays.fill(key, (byte) 0);
                throw new GeneralSecurityException("Longitud de clave inválida");
            }
            return key;
        }

        if (new File(app.getFilesDir(), "local_auth.sun1").exists() ||
                new File(app.getFilesDir(), "local_note.sun1").exists() ||
                new File(app.getFilesDir(), "local_vault.sun1").exists() ||
                hasEncryptedMaterials()) {
            throw new GeneralSecurityException("Nota presente sin llave; se requiere recuperación");
        }
        if (wrapping == null) {
            KeyGenerator generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES,
                    "AndroidKeyStore");
            generator.init(new KeyGenParameterSpec.Builder(ALIAS,
                    KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                    .setKeySize(256)
                    .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                    .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                    .setRandomizedEncryptionRequired(true)
                    .build());
            wrapping = generator.generateKey();
        }
        byte[] key = new byte[KEY_LENGTH];
        new SecureRandom().nextBytes(key);
        try {
            Cipher cipher = Cipher.getInstance(TRANSFORM);
            cipher.init(Cipher.ENCRYPT_MODE, wrapping);
            cipher.updateAAD(AAD);
            byte[] encrypted = cipher.doFinal(key);
            byte[] packageBytes = new byte[IV_LENGTH + encrypted.length];
            byte[] iv = cipher.getIV();
            if (iv.length != IV_LENGTH) {
                throw new GeneralSecurityException("IV Keystore inválido");
            }
            System.arraycopy(iv, 0, packageBytes, 0, IV_LENGTH);
            System.arraycopy(encrypted, 0, packageBytes, IV_LENGTH, encrypted.length);
            FileOutputStream output = file.startWrite();
            try {
                output.write(packageBytes);
                file.finishWrite(output);
            } catch (IOException exception) {
                file.failWrite(output);
                throw exception;
            }
            return key;
        } catch (GeneralSecurityException | IOException exception) {
            Arrays.fill(key, (byte) 0);
            throw exception;
        }
    }
}
