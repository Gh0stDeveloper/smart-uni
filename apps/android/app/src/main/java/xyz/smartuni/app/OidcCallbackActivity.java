package xyz.smartuni.app;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.widget.Toast;

import net.openid.appauth.AuthorizationException;
import net.openid.appauth.AuthorizationResponse;
import net.openid.appauth.AuthorizationService;
import net.openid.appauth.TokenResponse;

/**
 * Destino privado del PendingIntent de AppAuth, sin WebView ni secretos en Intent.
 * El resultado no equivale a autorización API hasta validar /me en servidor.
 */
public final class OidcCallbackActivity extends Activity {
    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        AuthorizationResponse response = AuthorizationResponse.fromIntent(getIntent());
        AuthorizationException error = AuthorizationException.fromIntent(getIntent());
        if (error != null || response == null) {
            complete(false);
            return;
        }
        if (!BuildConfig.OIDC_CLIENT_ID.equals(response.request.clientId)) {
            complete(false);
            return;
        }
        AuthorizationService service = new AuthorizationService(this);
        service.performTokenRequest(response.createTokenExchangeRequest(),
                (TokenResponse tokenResponse, AuthorizationException failure) -> {
                    boolean stored = false;
                    try {
                        if (failure == null && tokenResponse != null &&
                                tokenResponse.accessToken != null &&
                                tokenResponse.accessTokenExpirationTime != null) {
                            new SessionVault(this).save(tokenResponse.accessToken,
                                    tokenResponse.accessTokenExpirationTime);
                            stored = true;
                        }
                    } catch (Exception | LinkageError ignored) {
                        // No registrar tokens, refresh tokens ni cuerpo de respuesta.
                    } finally {
                        service.dispose();
                    }
                    complete(stored);
                });
    }

    private void complete(boolean ok) {
        runOnUiThread(() -> {
            Toast.makeText(this, ok ? "Token cifrado. Validar acceso con el servidor."
                    : "Autenticación no completada; no se guardó ninguna sesión nueva.",
                    Toast.LENGTH_LONG).show();
            Intent back = new Intent(this, MainActivity.class);
            back.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
            back.putExtra("openProfile", true);
            startActivity(back);
            finish();
        });
    }
}
