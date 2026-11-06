package xyz.smartuni.app;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.URL;
import java.nio.charset.StandardCharsets;

import javax.net.ssl.HttpsURLConnection;

/**
 * Adaptador del TLS del sistema Android, invocado solo desde JNI C++.
 * JNI fija las rutas; la capa Java no conserva endpoints, hosts ni credenciales.
 *
 * No altera TrustManager, no sigue redirecciones y nunca escribe tokens en logs.
 */
final class NativeHttpTls {
    private static final int MAX_BODY = 2 * 1024 * 1024;
    private static final int MAX_POST = 180 * 1024;

    private NativeHttpTls() {}

    static HttpReply execute(String fullUrl, byte[] bearer, byte[] json, String method) {
        if (fullUrl == null || !fullUrl.startsWith("https://") ||
                bearer == null || bearer.length < 10 || bearer.length > 16384 ||
                !("GET".equals(method) || "POST".equals(method)) ||
                ("POST".equals(method) && (json == null || json.length > MAX_POST)) ||
                ("GET".equals(method) && json != null)) {
            return null;
        }

        for (byte b : bearer) {
            if (!(b >= 0x21 && b <= 0x7e) || b == ':' || b == '\\') return null;
        }
        HttpsURLConnection connection = null;
        try {
            URL url = new URL(fullUrl);
            if (!"https".equals(url.getProtocol()) || url.getUserInfo() != null ||
                    url.getRef() != null) return null;
            connection = (HttpsURLConnection) url.openConnection();
            connection.setInstanceFollowRedirects(false);
            connection.setConnectTimeout(5000);
            connection.setReadTimeout(10000);
            connection.setUseCaches(false);
            connection.setRequestProperty("Accept", "application/json");
            connection.setRequestProperty("Authorization", "Bearer " +
                    new String(bearer, StandardCharsets.US_ASCII));
            connection.setRequestMethod(method);
            if ("POST".equals(method)) {
                connection.setDoOutput(true);
                connection.setRequestProperty("Content-Type", "application/json");
                connection.setFixedLengthStreamingMode(json.length);
                try (OutputStream output = connection.getOutputStream()) {
                    output.write(json);
                }
            }
            int code = connection.getResponseCode();
            if (code < 100 || code > 599) return null;
            long advertised = connection.getContentLengthLong();
            if (advertised > MAX_BODY) return null;
            try (InputStream stream = code >= 400 ?
                    connection.getErrorStream() : connection.getInputStream()) {
                if (stream == null) return new HttpReply(code, new byte[0]);
                ByteArrayOutputStream bytes = new ByteArrayOutputStream();
                byte[] chunk = new byte[8192];
                int size = 0;
                int count;
                while ((count = stream.read(chunk)) != -1) {
                    size += count;
                    if (size > MAX_BODY) return null;
                    bytes.write(chunk, 0, count);
                }
                return new HttpReply(code, bytes.toByteArray());
            }
        } catch (Exception ignored) {
            // Los errores de red no deben revelar tokens, respuestas ni rutas.
            return null;
        } finally {
            if (connection != null) connection.disconnect();
        }
    }
}
