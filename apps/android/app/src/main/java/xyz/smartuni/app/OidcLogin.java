package xyz.smartuni.app;

import android.app.Activity;
import android.app.PendingIntent;
import android.content.Intent;
import android.net.Uri;
import android.widget.Toast;

import net.openid.appauth.AuthorizationRequest;
import net.openid.appauth.AuthorizationService;
import net.openid.appauth.AuthorizationServiceConfiguration;
import net.openid.appauth.ResponseTypeValues;

/**
 * Authorization Code con PKCE S256, state y nonce implementados por AppAuth.
 * IdP y client_id públicos se inyectan únicamente en builds autorizados.
 */
final class OidcLogin {
    private OidcLogin() {}

    static boolean configured() {
        return !BuildConfig.OIDC_ISSUER.isEmpty() &&
                !BuildConfig.OIDC_CLIENT_ID.isEmpty();
    }

    static void start(Activity activity) {
        if (!configured()) {
            Toast.makeText(activity, "No se ha configurado un proveedor OIDC real.",
                    Toast.LENGTH_LONG).show();
            return;
        }
        if (!BuildConfig.OIDC_ISSUER.startsWith("https://")) return;
        Uri issuer = Uri.parse(BuildConfig.OIDC_ISSUER);
        AuthorizationServiceConfiguration.fetchFromIssuer(issuer, (config, error) -> {
            if (activity.isFinishing() || activity.isDestroyed()) return;
            if (error != null || config == null) {
                activity.runOnUiThread(() -> Toast.makeText(activity,
                        "No se pudo conectar al proveedor OIDC por HTTPS.",
                        Toast.LENGTH_LONG).show());
                return;
            }
            activity.runOnUiThread(() -> {
                AuthorizationService service = new AuthorizationService(activity);
                AuthorizationRequest request = new AuthorizationRequest.Builder(
                        config,
                        BuildConfig.OIDC_CLIENT_ID,
                        ResponseTypeValues.CODE,
                        Uri.parse("xyz.smartuni.app:/oauth2redirect")
                ).setScope("openid profile").build();
                // AppAuth crea valores aleatorios state, nonce, code_verifier y challenge S256.
                Intent callback = new Intent(activity, OidcCallbackActivity.class);
                int flags = PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_MUTABLE;
                PendingIntent completed = PendingIntent.getActivity(activity, 1631, callback, flags);
                try {
                    service.performAuthorizationRequest(request, completed);
                } catch (RuntimeException exc) {
                    Toast.makeText(activity, "No se pudo abrir el navegador de autenticación.",
                            Toast.LENGTH_LONG).show();
                } finally {
                    service.dispose();
                }
            });
        });
    }
}
