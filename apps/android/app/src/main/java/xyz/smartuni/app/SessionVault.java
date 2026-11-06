package xyz.smartuni.app;

import android.content.Context;
import android.util.AtomicFile;

import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import java.util.Arrays;

/**
 * Token OIDC efímero cifrado Rust/Keystore. Sin refresh por ahora.
 * No almacenar ID tokens o información de usuarios en SharedPreferences.
 */
final class SessionVault {
    private static final String FILENAME = "local_auth.sun1";
    private static final byte[] AAD =
            "smartuni/android/session/v1".getBytes(StandardCharsets.UTF_8);
    private final Context app;

    SessionVault(Context context) {
        app = context.getApplicationContext();
    }

    void save(String accessToken, long expiryMillis) throws Exception {
        if (accessToken == null || accessToken.length() < 10 ||
                accessToken.length() > 16384 ||
                expiryMillis <= System.currentTimeMillis() + 10000) {
            throw new GeneralSecurityException("Token inválido o caducado");
        }
        for (int i = 0; i < accessToken.length(); i++) {
            char c = accessToken.charAt(i);
            if (c < 0x21 || c > 0x7e) {
                throw new GeneralSecurityException("Token no ASCII imprimible");
            }
        }
        JSONObject data = new JSONObject();
        data.put("issuer", BuildConfig.OIDC_ISSUER);
        data.put("expiry", expiryMillis);
        data.put("access", accessToken);
        byte[] plain = data.toString().getBytes(StandardCharsets.UTF_8);
        byte[] key = new KeyVault(app).loadOrCreate();
        byte[] sealed = null;
        try {
            sealed = NativeBridge.seal(key, AAD, plain);
            if (sealed == null || sealed.length > 32768) {
                throw new GeneralSecurityException("No se pudo proteger la sesión");
            }
            AtomicFile file = new AtomicFile(new File(app.getFilesDir(), FILENAME));
            FileOutputStream stream = file.startWrite();
            try {
                stream.write(sealed);
                file.finishWrite(stream);
            } catch (java.io.IOException error) {
                file.failWrite(stream);
                throw error;
            }
        } finally {
            Arrays.fill(plain, (byte) 0);
            Arrays.fill(key, (byte) 0);
            if (sealed != null) Arrays.fill(sealed, (byte) 0);
        }
    }

    byte[] bearer() throws Exception {
        AtomicFile file = new AtomicFile(new File(app.getFilesDir(), FILENAME));
        if (!file.getBaseFile().exists()) return null;
        if (file.getBaseFile().length() > 32768) {
            throw new GeneralSecurityException("Paquete de sesión inválido");
        }
        byte[] sealed = file.readFully();
        byte[] key = new KeyVault(app).loadOrCreate();
        byte[] plain = null;
        try {
            plain = NativeBridge.open(key, AAD, sealed);
            if (plain == null || plain.length > 20000) {
                throw new GeneralSecurityException("Sesión no autenticada");
            }
            JSONObject state = new JSONObject(new String(plain, StandardCharsets.UTF_8));
            if (!BuildConfig.OIDC_ISSUER.equals(state.getString("issuer"))) {
                throw new GeneralSecurityException("Issuer distinto a esta compilación");
            }
            if (state.getLong("expiry") <= System.currentTimeMillis() + 10000) return null;
            return state.getString("access").getBytes(StandardCharsets.US_ASCII);
        } finally {
            Arrays.fill(sealed, (byte) 0);
            Arrays.fill(key, (byte) 0);
            if (plain != null) Arrays.fill(plain, (byte) 0);
        }
    }

    void clear() throws Exception {
        File file = new File(app.getFilesDir(), FILENAME);
        if (file.exists() && !file.delete()) {
            throw new java.io.IOException("No se pudo borrar sesión local");
        }
    }
}
