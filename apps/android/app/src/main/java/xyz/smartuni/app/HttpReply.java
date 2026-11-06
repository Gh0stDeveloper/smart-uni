package xyz.smartuni.app;

/** Resultado tipado de un intercambio HTTPS: no representa un ACK de sync. */
public final class HttpReply {
    public final int status;
    public final byte[] body;

    public HttpReply(int status, byte[] body) {
        this.status = status;
        this.body = body;
    }
}
