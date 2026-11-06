package xyz.smartuni.app;

/**
 * JNI C++ es el único adaptador de endpoints; Rust ejecuta la criptografía.
 * No contiene rutas de API, claves universales ni credenciales de servidor.
 */
public final class NativeBridge {
    static {
        System.loadLibrary("smartuni_android");
    }

    private NativeBridge() { }

    public static native int abiVersion();
    public static native boolean selfTest();
    public static native byte[] seal(byte[] key, byte[] context, byte[] plaintext);
    public static native byte[] open(byte[] key, byte[] context, byte[] ciphertext);
    /** Diagnóstico público de /healthz por HTTPS; sin autenticación ni sync. */
    public static native int checkHealth(String httpsOrigin);
    /**
     * 0=me, 1=pull, 2=push, 3=conflicts. Rutas fijadas en JNI C++.
     * Requiere bearer OIDC provisto externamente: no hay login Android todavía.
     * Esta API NO efectúa ACK ni modifica cursores locales.
     */
    public static native HttpReply apiRequest(String httpsOrigin, byte[] bearer,
                                               int operation, long cursor, byte[] jsonBody);
}
