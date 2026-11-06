package xyz.smartuni.app;

import android.content.Context;
import android.net.Uri;
import android.provider.OpenableColumns;
import android.database.Cursor;
import android.util.AtomicFile;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.Locale;
import java.util.UUID;

/**
 * Importa material mediante Storage Access Framework a un contenedor Rust
 * autenticado privado. No exporta plaintext ni abre visores externos.
 */
final class MaterialVault {
    private static final int MAX_MATERIAL = 8 * 1024 * 1024;
    private static final String PREFIX = "smartuni/android/material/v1/";
    private final Context app;

    MaterialVault(Context context) {
        app = context.getApplicationContext();
    }

    private File directory() throws Exception {
        File dir = new File(app.getFilesDir(), "encrypted_materials");
        if (!dir.isDirectory() && !dir.mkdirs()) {
            throw new java.io.IOException("No se pudo crear almacenamiento privado");
        }
        return dir;
    }

    private File target(String id) throws Exception {
        UUID.fromString(id);
        return new File(directory(), id + ".sun1");
    }

    private static byte[] contextFor(String id) {
        return (PREFIX + id).getBytes(StandardCharsets.UTF_8);
    }

    private static String safeName(String supplied) throws GeneralSecurityException {
        if (supplied == null || supplied.length() > 160 ||
                supplied.trim().isEmpty() ||
                supplied.indexOf('/') >= 0 || supplied.indexOf('\\') >= 0 ||
                supplied.contains("..") || supplied.matches(".*[\\x00-\\x1f].*")) {
            throw new GeneralSecurityException("Nombre de material inválido");
        }
        String name = supplied.trim();
        String low = name.toLowerCase(Locale.ROOT);
        if (!(low.endsWith(".txt") || low.endsWith(".md") ||
                low.endsWith(".csv") || low.endsWith(".pdf") ||
                low.endsWith(".jpg") || low.endsWith(".jpeg") ||
                low.endsWith(".png") || low.endsWith(".docx") ||
                low.endsWith(".xlsx") || low.endsWith(".pptx"))) {
            throw new GeneralSecurityException("Extensión de material no admitida");
        }
        return name;
    }

    String displayName(Uri uri) throws Exception {
        try (Cursor cursor = app.getContentResolver().query(uri,
                new String[]{OpenableColumns.DISPLAY_NAME}, null, null, null)) {
            if (cursor == null || !cursor.moveToFirst()) {
                throw new GeneralSecurityException("El proveedor no informó un nombre");
            }
            return safeName(cursor.getString(0));
        }
    }

    private static byte[] readBounded(InputStream input) throws Exception {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] block = new byte[8192];
        int size = 0;
        try {
            int n;
            while ((n = input.read(block)) != -1) {
                size += n;
                if (size > MAX_MATERIAL) {
                    throw new GeneralSecurityException("Material supera los 8 MiB");
                }
                out.write(block, 0, n);
            }
            return out.toByteArray();
        } finally {
            Arrays.fill(block, (byte) 0);
        }
    }

    String importDocument(Uri uri) throws Exception {
        String filename = displayName(uri);
        String id = UUID.randomUUID().toString();
        byte[] plaintext;
        try (InputStream input = app.getContentResolver().openInputStream(uri)) {
            if (input == null) throw new GeneralSecurityException("Documento inaccesible");
            plaintext = readBounded(input);
        }
        byte[] key = null;
        byte[] ciphertext = null;
        File file = target(id);
        try {
            key = new KeyVault(app).loadOrCreate();
            ciphertext = NativeBridge.seal(key, contextFor(id), plaintext);
            if (ciphertext == null || ciphertext.length < 39) {
                throw new GeneralSecurityException("Cifrado de material fallido");
            }
            // No guardar un material en disco si no se ha cifrado completamente.
            AtomicFile atomic = new AtomicFile(file);
            FileOutputStream output = atomic.startWrite();
            try {
                output.write(ciphertext);
                atomic.finishWrite(output);
            } catch (java.io.IOException error) {
                atomic.failWrite(output);
                throw error;
            }
            try {
                new LocalVault(app).add(LocalVault.MATERIALS, filename,
                        id, Integer.toString(plaintext.length));
            } catch (Exception error) {
                if (file.exists() && !file.delete()) {
                    throw new java.io.IOException("Importación fallida; contenedor huérfano pendiente", error);
                }
                throw error;
            }
            return filename;
        } finally {
            Arrays.fill(plaintext, (byte) 0);
            if (key != null) Arrays.fill(key, (byte) 0);
            if (ciphertext != null) Arrays.fill(ciphertext, (byte) 0);
        }
    }

    byte[] readMaterial(String id) throws Exception {
        File file = target(id);
        if (!file.isFile() || file.length() > MAX_MATERIAL + 512) {
            throw new GeneralSecurityException("Material inaccesible o inválido");
        }
        AtomicFile atomic = new AtomicFile(file);
        byte[] ciphertext = atomic.readFully();
        byte[] key = new KeyVault(app).loadOrCreate();
        try {
            byte[] raw = NativeBridge.open(key, contextFor(id), ciphertext);
            if (raw == null || raw.length > MAX_MATERIAL) {
                throw new GeneralSecurityException("Material no autenticado");
            }
            return raw;
        } finally {
            Arrays.fill(ciphertext, (byte) 0);
            Arrays.fill(key, (byte) 0);
        }
    }

    void deleteMaterial(String id, String vaultRecordId) throws Exception {
        // Preferir restos cifrados a pérdida de metadata: borrar primero el índice.
        new LocalVault(app).delete(LocalVault.MATERIALS, vaultRecordId);
        File file = target(id);
        if (file.exists() && !file.delete()) {
            throw new java.io.IOException("Índice eliminado; queda ciphertext huérfano");
        }
    }
}
