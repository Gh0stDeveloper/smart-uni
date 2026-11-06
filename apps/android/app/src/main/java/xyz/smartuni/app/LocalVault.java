package xyz.smartuni.app;

import android.content.Context;
import android.util.AtomicFile;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import java.util.Arrays;
import java.util.UUID;

/**
 * Repositorio offline de laboratorio: un documento JSON completo cifrado con
 * Rust (SUAEAD01) y clave DEK envuelta en Android Keystore.
 *
 * No es SQLCipher, no tiene transacciones multiarchivo ni sincronización.
 * Una sola cerradura serializa lecturas/escrituras dentro del proceso.
 */
final class LocalVault {
    static final String NOTES = "notes";
    static final String TASKS = "tasks";
    static final String EVENTS = "events";
    static final String MATERIALS = "materials";
    private static final Object LOCK = new Object();
    private static final int MAX_BYTES = 512 * 1024;
    private static final int MAX_ITEMS = 400;
    private static final String FILENAME = "local_vault.sun1";
    private static final byte[] AAD = "smartuni/android/local-vault/v1"
            .getBytes(StandardCharsets.UTF_8);
    private final Context app;

    LocalVault(Context context) {
        app = context.getApplicationContext();
    }

    private static JSONObject fresh() throws JSONException {
        JSONObject root = new JSONObject();
        root.put("schema", 1);
        root.put(NOTES, new JSONArray());
        root.put(TASKS, new JSONArray());
        root.put(EVENTS, new JSONArray());
        root.put(MATERIALS, new JSONArray());
        return root;
    }

    private static JSONArray group(JSONObject root, String kind) throws JSONException {
        if (!(NOTES.equals(kind) || TASKS.equals(kind) ||
                EVENTS.equals(kind) || MATERIALS.equals(kind))) {
            throw new JSONException("Tipo de registro no admitido");
        }
        return root.getJSONArray(kind);
    }

    private JSONObject load() throws IOException, GeneralSecurityException, JSONException {
        AtomicFile file = new AtomicFile(new File(app.getFilesDir(), FILENAME));
        if (!file.getBaseFile().exists()) {
            JSONObject root = fresh();
            // Migración conservadora: no borrar el apunte legacy hasta restauración verificada.
            if (new File(app.getFilesDir(), "local_note.sun1").exists()) {
                byte[] legacy = new EncryptedNotesStore(app).read();
                try {
                    if (legacy.length > 0) {
                        JSONObject item = new JSONObject();
                        item.put("id", UUID.randomUUID().toString());
                        item.put("title", "Apunte anterior");
                        item.put("text", new String(legacy, StandardCharsets.UTF_8));
                        item.put("date", "");
                        item.put("done", false);
                        root.getJSONArray(NOTES).put(item);
                    }
                } finally {
                    Arrays.fill(legacy, (byte) 0);
                }
            }
            return root;
        }
        byte[] encrypted = file.readFully();
        if (encrypted.length < 39 || encrypted.length > MAX_BYTES + 512) {
            throw new GeneralSecurityException("Contenedor de bóveda inválido");
        }
        byte[] key = new KeyVault(app).loadOrCreate();
        byte[] plaintext = null;
        try {
            plaintext = NativeBridge.open(key, AAD, encrypted);
            if (plaintext == null || plaintext.length > MAX_BYTES) {
                throw new GeneralSecurityException("Bóveda sin autenticar");
            }
            JSONObject root = new JSONObject(new String(plaintext, StandardCharsets.UTF_8));
            if (root.getInt("schema") != 1) {
                throw new GeneralSecurityException("Versión de bóveda no admitida");
            }
            for (String kind : new String[]{NOTES, TASKS, EVENTS, MATERIALS}) {
                JSONArray rows = group(root, kind);
                if (rows.length() > MAX_ITEMS) {
                    throw new GeneralSecurityException("Demasiados elementos en " + kind);
                }
                for (int i = 0; i < rows.length(); i++) {
                    JSONObject row = rows.getJSONObject(i);
                    UUID.fromString(row.getString("id"));
                    row.getString("title");
                }
            }
            return root;
        } catch (IllegalArgumentException error) {
            throw new GeneralSecurityException("Identificador de bóveda inválido", error);
        } finally {
            Arrays.fill(key, (byte) 0);
            Arrays.fill(encrypted, (byte) 0);
            if (plaintext != null) Arrays.fill(plaintext, (byte) 0);
        }
    }

    private void save(JSONObject root) throws IOException, GeneralSecurityException {
        byte[] data = root.toString().getBytes(StandardCharsets.UTF_8);
        if (data.length > MAX_BYTES) {
            Arrays.fill(data, (byte) 0);
            throw new GeneralSecurityException("La bóveda supera 512 KiB");
        }
        byte[] key = new KeyVault(app).loadOrCreate();
        byte[] blob;
        try {
            blob = NativeBridge.seal(key, AAD, data);
        } finally {
            Arrays.fill(key, (byte) 0);
            Arrays.fill(data, (byte) 0);
        }
        if (blob == null || blob.length < 39) {
            throw new GeneralSecurityException("No se pudo cifrar la bóveda");
        }
        AtomicFile file = new AtomicFile(new File(app.getFilesDir(), FILENAME));
        FileOutputStream output = file.startWrite();
        try {
            output.write(blob);
            file.finishWrite(output);
        } catch (IOException error) {
            file.failWrite(output);
            throw error;
        } finally {
            Arrays.fill(blob, (byte) 0);
        }
    }

    JSONArray list(String kind) throws Exception {
        synchronized (LOCK) {
            JSONArray records = group(load(), kind);
            return new JSONArray(records.toString());
        }
    }

    String add(String kind, String title, String value, String date) throws Exception {
        if (title == null || title.trim().isEmpty() || title.length() > 160 ||
                value == null || value.length() > 64000 ||
                date == null || date.length() > 64) {
            throw new GeneralSecurityException("Campos fuera de límites");
        }
        synchronized (LOCK) {
            JSONObject root = load();
            JSONArray records = group(root, kind);
            if (records.length() >= MAX_ITEMS) {
                throw new GeneralSecurityException("Límite de registros alcanzado");
            }
            String id = UUID.randomUUID().toString();
            JSONObject item = new JSONObject();
            item.put("id", id);
            item.put("title", title.trim());
            item.put("text", value);
            item.put("date", date);
            item.put("done", false);
            records.put(item);
            save(root);
            return id;
        }
    }

    void updateNote(String id, String title, String body) throws Exception {
        if (title == null || title.trim().isEmpty() || title.length() > 160 ||
                body == null || body.length() > 64000) {
            throw new GeneralSecurityException("Campos de apunte inválidos");
        }
        synchronized (LOCK) {
            JSONObject root = load();
            JSONArray notes = group(root, NOTES);
            for (int i = 0; i < notes.length(); i++) {
                JSONObject row = notes.getJSONObject(i);
                if (id.equals(row.getString("id"))) {
                    row.put("title", title.trim());
                    row.put("text", body);
                    save(root);
                    return;
                }
            }
            throw new GeneralSecurityException("Apunte no encontrado");
        }
    }

    void toggleTask(String id) throws Exception {
        synchronized (LOCK) {
            JSONObject root = load();
            JSONArray rows = group(root, TASKS);
            for (int i = 0; i < rows.length(); i++) {
                JSONObject item = rows.getJSONObject(i);
                if (id.equals(item.getString("id"))) {
                    item.put("done", !item.optBoolean("done"));
                    save(root);
                    return;
                }
            }
            throw new GeneralSecurityException("Tarea no encontrada");
        }
    }

    void delete(String kind, String id) throws Exception {
        synchronized (LOCK) {
            JSONObject root = load();
            JSONArray rows = group(root, kind);
            for (int i = 0; i < rows.length(); i++) {
                if (id.equals(rows.getJSONObject(i).getString("id"))) {
                    rows.remove(i);
                    save(root);
                    return;
                }
            }
            throw new GeneralSecurityException("Registro no encontrado");
        }
    }
}
